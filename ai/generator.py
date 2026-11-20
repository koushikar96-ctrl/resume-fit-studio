from __future__ import annotations

from models.resume_schema import extract_keyword_set


def generate_summary_from_resume(resume: dict) -> str:
    personal = resume.get("personal", {})
    name = personal.get("name", "Professional").strip() or "Professional"
    skills = ", ".join(resume.get("skills", []))
    summary = resume.get("summary", "").strip()

    if summary:
        return summary

    return f"{name} is a professional with experience in {skills or 'relevant technical and business domains'}, focused on delivering high-impact results in software and data-driven work."


def critique_generated_content(content: str, original_data: dict) -> dict:
    known_skills = set(extract_keyword_set(" ".join(original_data.get("skills", []))))
    content_keywords = extract_keyword_set(content)

    unsupported = sorted(content_keywords - known_skills - {"professional", "experience", "with", "technical", "business", "results", "software", "data", "driven", "high"})

    return {
        "is_valid": not unsupported,
        "unsupported_terms": unsupported,
        "suggestions": ["Keep phrasing grounded in the user-provided skills and experience."] if unsupported else ["Content looks aligned with the existing resume data."],
    }
