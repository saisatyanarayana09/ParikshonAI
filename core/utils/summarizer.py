"""Summarization utility using HuggingFace Inference API (no local model download)."""
import os

from django.conf import settings
from huggingface_hub import InferenceClient

from .files import split_text


class SummarizationError(Exception):
    """Raised when summarization cannot be completed."""


def _client() -> InferenceClient:
    api_key = settings.HUGGINGFACE_API_KEY or os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise SummarizationError(
            "HUGGINGFACE_API_KEY is missing. Add a Hugging Face access token to your .env file."
        )
    return InferenceClient(model=settings.HUGGINGFACE_CHAT_MODEL, provider="auto", token=api_key)


def _build_prompt(text: str, length: str, summary_style: str, output_format: str) -> str:
    length_instruction = {
        "short": "Write a brief summary in 3–5 sentences.",
        "medium": "Write a clear summary in 6–10 sentences.",
        "long": "Write a detailed, comprehensive summary.",
    }.get(length, "Write a clear summary.")

    style_instruction = {
        "quick": "Focus on the main idea only.",
        "detailed": "Cover all major points with supporting details.",
        "bullets": "Use bullet points for each key idea.",
        "executive": "Write an executive summary suitable for decision-makers.",
        "academic": "Use formal academic language and structure.",
        "insights": "Extract and list the key insights.",
        "actions": "Extract and list all action items or recommendations.",
        "important": "Highlight only the most important points.",
    }.get(summary_style, "Summarize the content clearly.")

    format_instruction = (
        "Format your response as bullet points starting each with '- '."
        if output_format == "bullets" or summary_style in {"bullets", "insights", "actions", "important"}
        else "Format your response as clear paragraphs."
    )

    return (
        f"Summarize the following document.\n\n"
        f"Instructions:\n"
        f"- {length_instruction}\n"
        f"- {style_instruction}\n"
        f"- {format_instruction}\n"
        f"- Only use information from the document. Do not add external knowledge.\n\n"
        f"Document:\n{text}"
    )


def summarize_text(
    text: str,
    length: str = "medium",
    output_format: str = "paragraph",
    summary_style: str = "quick",
) -> str:
    if len(text.split()) < 30:
        raise SummarizationError("Please upload a document with at least 30 words for summarization.")

    # Take first ~3000 words to stay within token limits
    chunks = split_text(text, max_chars=3500, overlap=100)
    source = "\n\n".join(chunks[:3])

    prompt = _build_prompt(source, length, summary_style, output_format)

    try:
        client = _client()
        response = client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional document summarizer. "
                        "Summarize only from the provided document text. "
                        "Never add information not present in the document."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        result = response.choices[0].message.content
        if not result or not result.strip():
            raise SummarizationError("The AI returned an empty summary. Try again.")
        return result.strip()
    except SummarizationError:
        raise
    except Exception as exc:
        raise SummarizationError(f"Summary generation failed: {exc}") from exc
