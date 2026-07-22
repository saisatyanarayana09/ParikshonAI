import os
import math

from django.conf import settings
from huggingface_hub import InferenceClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings


class ChatError(Exception):
    """Raised when document chat setup or answering fails."""


def _require_huggingface_key() -> str:
    api_key = settings.HUGGINGFACE_API_KEY or os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise ChatError("HUGGINGFACE_API_KEY is missing. Add a Hugging Face access token to your .env file before using document chat.")
    return api_key


def _embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def build_document_index(text: str, session) -> int:
    """Store document chunks and embeddings in MySQL through Django models."""
    from core.models import DocumentChunk

    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    documents = splitter.create_documents([text])
    if not documents:
        raise ChatError("The uploaded document did not contain enough text for chat.")

    try:
        embeddings = _embedding_model().embed_documents([document.page_content for document in documents])
        DocumentChunk.objects.filter(session=session).delete()
        DocumentChunk.objects.bulk_create(
            [
                DocumentChunk(session=session, chunk_index=index, content=document.page_content, embedding=embedding)
                for index, (document, embedding) in enumerate(zip(documents, embeddings))
            ]
        )
    except Exception as exc:
        raise ChatError(f"Unable to create the document index: {exc}") from exc

    return len(documents)


from pgvector.django import CosineDistance


def answer_question(session, question: str, history: list[tuple[str, str]]) -> str:
    api_key = _require_huggingface_key()
    if not session.chunks.exists():
        raise ChatError("Document index was not found. Upload the document again.")

    client = InferenceClient(model=settings.HUGGINGFACE_CHAT_MODEL, provider="auto", token=api_key)

    try:
        question_embedding = _embedding_model().embed_query(question)
        ranked_chunks = session.chunks.annotate(
            distance=CosineDistance("embedding", question_embedding)
        ).order_by("distance")[:4]

        # If the closest chunk is too far away, the question is likely off-topic
        top_chunk = ranked_chunks.first()
        if top_chunk and top_chunk.distance > 0.75:
            return (
                "🎯 That question doesn't seem to be related to the uploaded document. "
                "I'm Parikshon AI — a study assistant designed to help you understand your documents. "
                "Please ask questions about the content you've uploaded!"
            )

        context = "\n\n".join(chunk.content for chunk in ranked_chunks)
        recent_history = "\n".join(
            f"User: {user_message}\nAssistant: {ai_message}"
            for user_message, ai_message in history[-6:]
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Parikshon AI, a focused study assistant. "
                    "Your ONLY job is to answer questions strictly based on the uploaded document context provided below. "
                    "\n\nRULES (follow strictly):"
                    "\n1. ONLY answer if the answer is clearly present in the document context."
                    "\n2. If the question is unrelated to the document (general knowledge, weather, coding, casual chat, etc.), "
                    "respond ONLY with: "
                    "'🎯 Please ask questions related to your uploaded document. I am Parikshon AI, your study assistant!'"
                    "\n3. If the answer is partially in the document, answer what you can and note the limitation."
                    "\n4. Never invent facts, hallucinate, or answer from general knowledge."
                    "\n5. Be concise, accurate, and helpful for studying."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Document context:\n{context}"
                    f"\n\nRecent conversation:\n{recent_history}"
                    f"\n\nQuestion: {question}"
                ),
            },
        ]
        result = client.chat_completion(messages=messages, temperature=0.1, max_tokens=700)
    except Exception as exc:
        raise ChatError(f"Document chat failed: {exc}") from exc

    content = result.choices[0].message.content
    return (content or "🎯 Please ask questions related to your uploaded document. I am Parikshon AI, your study assistant!").strip()
