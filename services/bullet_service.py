from __future__ import annotations


def generate_resume_bullets(resume: dict) -> list[str]:
    bullets: list[str] = []

    summary = (resume.get("summary") or "").strip()
    if summary:
        bullets.append(summary)

    skills = [skill.strip() for skill in resume.get("skills", []) if skill.strip()]
    if skills:
        bullets.append(f"Worked with {', '.join(skills[:5])} in technical and data-driven projects.")

    for experience in resume.get("experience", [])[:2]:
        role = (experience.get("role") or "Professional").strip()
        company = (experience.get("company") or "the organization").strip()
        description = (experience.get("description") or "").strip()
        if description:
            bullets.append(f"In the {role} role at {company}, {description}.")
        elif role:
            bullets.append(f"Served in the {role} role at {company} and contributed to business and technical outcomes.")

    return bullets[:4]
