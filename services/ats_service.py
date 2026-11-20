from __future__ import annotations

import re

from models.resume_schema import extract_keyword_set



_IMPACT_PATTERN = re.compile(
    r"\b(?:achieved|built|delivered|improved|increased|reduced|launched|led|optimized|saved)\b|\d+\s*(?:%|percent|users|clients|days|hours)",
    re.IGNORECASE,
)


def _content_quality_score(resume_text: str, resume_keywords: set[str]) -> float:
    """Measure basic resume substance without letting it outweigh job relevance."""
    if not resume_text.strip():
        return 0.0

    # A meaningful resume gets up to 15 points for enough distinct content,
    # plus 5 points when it contains an action or quantified achievement.
    content_points = min(len(resume_keywords) / 30, 1) * 15
    impact_points = 5 if _IMPACT_PATTERN.search(resume_text) else 0
    return round(content_points + impact_points, 2)


def ats_score_for_resume(resume_text: str, job_text: str) -> dict:
    """Score ATS relevance against the supplied job description.

    Job-keyword coverage is deliberately the dominant factor. The former
    implementation awarded fixed points for merely having text and one shared
    word, which made almost every ordinary resume score 100.
    """
    resume_keywords = extract_keyword_set(resume_text)
    job_keywords = extract_keyword_set(job_text)

    if not job_keywords:
        return {
            "score": 0,
            "overlap_count": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "keyword_coverage": 0.0,
            "content_quality": _content_quality_score(resume_text, resume_keywords),
        }

    matched_keywords = resume_keywords & job_keywords
    missing_keywords = job_keywords - resume_keywords
    keyword_coverage = len(matched_keywords) / len(job_keywords) * 100
    content_quality = _content_quality_score(resume_text, resume_keywords)
    score = round((keyword_coverage * 0.8) + content_quality, 2)

    return {
        "score": min(score, 100),
        "overlap_count": len(matched_keywords),
        "matched_keywords": sorted(matched_keywords),
        "missing_keywords": sorted(missing_keywords),
        "keyword_coverage": round(keyword_coverage, 2),
        "content_quality": content_quality,
    }
