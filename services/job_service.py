from __future__ import annotations

from models.resume_schema import extract_keyword_set


def extract_job_requirements(job_description: str) -> list[str]:
    keywords = sorted(extract_keyword_set(job_description))
    return [keyword for keyword in keywords if len(keyword) > 2][:12]


def evaluate_resume_against_job(resume: dict, job_description: str) -> dict:
    resume_text = " ".join(
        [
            resume.get("summary", ""),
            " ".join(resume.get("skills", [])),
            " ".join(exp.get("description", "") for exp in resume.get("experience", [])),
        ]
    )
    resume_keywords = extract_keyword_set(resume_text)
    job_keywords = set(extract_job_requirements(job_description))

    matched = sorted(resume_keywords & job_keywords)
    missing = sorted(job_keywords - resume_keywords)
    match_score = round((len(matched) / max(len(job_keywords), 1)) * 100, 2)

    return {
        "match_score": match_score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "requirements": sorted(job_keywords),
        "guardrail": "Only job requirements are scored; no invented skills are added to the resume.",
    }
