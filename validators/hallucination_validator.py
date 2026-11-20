from __future__ import annotations


def validate_no_invented_claims(resume_text: str, known_skills: list[str]) -> dict:
    normalized_skills = {skill.lower().strip() for skill in known_skills if skill.strip()}
    text = resume_text.lower()
    invented = []

    for skill in ["docker", "kubernetes", "aws", "gcp", "azure", "sql", "fastapi", "react", "node", "tensorflow"]:
        if skill in text and skill not in normalized_skills:
            invented.append(skill)

    return {
        "is_valid": not invented,
        "invented_terms": invented,
        "message": "No unsupported claims found." if not invented else "Potential unsupported skills detected.",
    }
