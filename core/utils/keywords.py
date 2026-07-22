from collections import Counter
import re

import yake
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer


class KeywordError(Exception):
    """Raised when keyword extraction cannot be completed."""


def extract_keywords(text: str, top_n: int = 15, method: str = "yake") -> list[dict]:
    if len(text.split()) < 10:
        raise KeywordError("Please upload a document with at least 10 words for keyword extraction.")

    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9-]{2,}\b", text.lower())
    frequencies = Counter(word for word in words if word not in ENGLISH_STOP_WORDS)

    if method == "tfidf":
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=100)
        matrix = vectorizer.fit_transform([text])
        scores = matrix.toarray()[0]
        names = vectorizer.get_feature_names_out()
        ranked = sorted(zip(names, scores), key=lambda item: item[1], reverse=True)[:top_n]
        return [{"keyword": name, "score": round(float(score), 4), "frequency": frequencies.get(name.split()[0], 0)} for name, score in ranked]

    extractor = yake.KeywordExtractor(lan="en", n=2, dedupLim=0.9, top=top_n, features=None)
    ranked = extractor.extract_keywords(text)
    return [
        {
            "keyword": keyword,
            "score": round(float(score), 4),
            "frequency": sum(frequencies.get(part.lower(), 0) for part in keyword.split()),
        }
        for keyword, score in ranked[:top_n]
    ]
