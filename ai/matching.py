from __future__ import annotations

from typing import Iterable

from models.resume_schema import extract_keyword_set


def safe_mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def keyword_overlap_score(resume_text: str, job_text: str) -> tuple[float, set[str], set[str]]:
    resume_keywords = extract_keyword_set(resume_text)
    job_keywords = extract_keyword_set(job_text)

    matches = resume_keywords & job_keywords
    if not resume_keywords or not job_keywords:
        return 0.0, matches, job_keywords - resume_keywords

    score = len(matches) / max(len(job_keywords), 1)
    return round(score * 100, 2), matches, job_keywords - resume_keywords


def hybrid_match_score(resume_text: str, job_text: str) -> dict:
    keyword_score, matched, missing = keyword_overlap_score(resume_text, job_text)

    resume_tokens = extract_keyword_set(resume_text)
    job_tokens = extract_keyword_set(job_text)

    semantic_score = 0.0
    if resume_tokens and job_tokens:
        semantic_score = len(resume_tokens & job_tokens) / max(len(job_tokens | resume_tokens), 1)

    final_score = round((0.6 * keyword_score) + (0.4 * (semantic_score * 100)), 2)
    return {
        "keyword_score": keyword_score,
        "semantic_score": round(semantic_score * 100, 2),
        "final_score": final_score,
        "matched_keywords": sorted(matched),
        "missing_keywords": sorted(missing),
    }
