import json
import os
import re

from django.conf import settings
from huggingface_hub import InferenceClient

from .files import split_text


class QuizError(Exception):
    """Raised when quiz generation or scoring input is invalid."""


def _client() -> InferenceClient:
    api_key = settings.HUGGINGFACE_API_KEY or os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise QuizError("HUGGINGFACE_API_KEY is missing. Add a Hugging Face access token to your .env file before generating quizzes.")
    return InferenceClient(model=settings.HUGGINGFACE_CHAT_MODEL, provider="auto", token=api_key)


def _parse_json(content: str) -> list[dict]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", content)
        if not match:
            raise
        data = json.loads(match.group(0))
    if not isinstance(data, list) or len(data) != 5:
        raise QuizError("The quiz model returned an invalid question set.")
    for item in data:
        if not {"question", "options", "correct_answer"}.issubset(item):
            raise QuizError("The quiz model returned incomplete question data.")
        if not isinstance(item["options"], list) or len(item["options"]) != 4:
            raise QuizError("Each quiz question must contain four options.")
        if item["correct_answer"] not in item["options"]:
            raise QuizError("Each correct answer must exactly match one option.")
    return data


def generate_quiz(text: str) -> list[dict]:
    if len(text.split()) < 80:
        raise QuizError("Please upload a document with at least 80 words for quiz generation.")
    source = "\n\n".join(split_text(text, max_chars=3000, overlap=100)[:4])
    prompt = (
        "Generate exactly five multiple-choice questions from the document content below. "
        "Return strict JSON only, with no markdown and no explanation. "
        "The JSON must be an object with a questions array containing five objects. "
        "Each question object must contain question, options, and correct_answer. "
        "Options must be an array of exactly four concise strings, and correct_answer must exactly match one option.\n\n"
        f"Document:\n{source}"
    )
    try:
        response = _client().chat_completion(
            temperature=0.2,
            messages=[
                {"role": "system", "content": "You create accurate quizzes from supplied document text and return strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1600,
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            parsed = parsed.get("questions", parsed.get("quiz", []))
        return _parse_json(json.dumps(parsed))
    except QuizError:
        raise
    except Exception as exc:
        raise QuizError(f"Quiz generation failed: {exc}") from exc


def score_quiz(questions: list[dict], answers: dict) -> dict:
    total = len(questions)
    correct = 0
    results = []
    for index, question in enumerate(questions):
        selected = answers.get(str(index), "")
        is_correct = selected == question["correct_answer"]
        correct += int(is_correct)
        results.append(
            {
                "question": question["question"],
                "selected": selected,
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
            }
        )
    return {"score": correct, "total": total, "percentage": round((correct / total) * 100) if total else 0, "results": results}
