from __future__ import annotations

from models.resume_schema import extract_keyword_set


def tailor_resume_to_job(resume: dict, job_description: str) -> dict:
    resume_text = " ".join(
        [
            resume.get("summary", ""),
            " ".join(resume.get("skills", [])),
            " ".join(exp.get("description", "") for exp in resume.get("experience", [])),
        ]
    )

    resume_keywords = extract_keyword_set(resume_text)
    job_keywords = extract_keyword_set(job_description)

    matched = sorted(resume_keywords & job_keywords)
    missing = sorted(job_keywords - resume_keywords)

    return {
        "matched_keywords": matched,
        "missing_keywords": missing,
        "guardrail": "No unsupported claims were added.",
        "recommended_action": "Only add missing skills if they are supported by real experience.",
    }


def generate_tailoring_recommendations(resume: dict, job_description: str) -> dict:
    base = tailor_resume_to_job(resume, job_description)

    missing_tech = [kw for kw in base["missing_keywords"] if len(kw) > 1][:8]

    recommendations = []
    if missing_tech:
        tech_str = ", ".join(kw.upper() for kw in missing_tech)
        recommendations.append(f"Key technical skills missing for this role: {tech_str}")
        recommendations.append("Highlight hands-on project achievements with metrics (e.g., accuracy %, model latency, dataset scale).")
        recommendations.append("Only include missing frameworks or tools if you have genuine practical experience.")
    else:
        recommendations.append("Your resume already covers all key technical requirements for this role!")

    return {
        "matched_keywords": base["matched_keywords"],
        "missing_keywords": missing_tech,
        "guardrail": "Only add missing skills if they are supported by real experience.",
        "recommended_improvements": recommendations,
    }
