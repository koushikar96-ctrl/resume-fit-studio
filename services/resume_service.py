from __future__ import annotations

from models.resume_schema import default_resume


def build_resume_payload(form_data: dict) -> dict:
    resume = default_resume()
    resume["personal"].update(
        {
            "name": form_data.get("name", ""),
            "email": form_data.get("email", ""),
            "phone": form_data.get("phone", ""),
            "location": form_data.get("location", ""),
            "portfolio": form_data.get("portfolio", ""),
        }
    )
    resume["summary"] = form_data.get("summary", "")
    resume["skills"] = [skill.strip() for skill in str(form_data.get("skills", "")).split(",") if skill.strip()]
    resume["experience"] = [
        {
            "role": form_data.get("role", ""),
            "company": form_data.get("company", ""),
            "location": form_data.get("location", ""),
            "start_date": form_data.get("start_date", ""),
            "end_date": form_data.get("end_date", ""),
            "description": form_data.get("experience_description", ""),
        }
    ]
    return resume
