from __future__ import annotations

import re
from io import BytesIO

from models.resume_schema import default_resume


SUPPORTED_RESUME_EXTENSIONS = ("pdf", "docx", "txt")


class ResumeParsingError(ValueError):
    """Raised when an uploaded resume cannot be read."""


SECTION_NAMES = {
    # Summary & Objective
    "summary": "summary",
    "professional summary": "summary",
    "summary of qualifications": "summary",
    "profile": "summary",
    "professional profile": "summary",
    "career summary": "summary",
    "executive summary": "summary",
    "about me": "summary",
    "objective": "summary",
    "career objective": "summary",
    # Experience
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment history": "experience",
    "work history": "experience",
    "career history": "experience",
    "relevant experience": "experience",
    "internship experience": "experience",
    "internships": "experience",
    # Education
    "education": "education",
    "academic background": "education",
    "academic qualifications": "education",
    "educational background": "education",
    "qualifications": "education",
    # Skills
    "skills": "skills",
    "technical skills": "skills",
    "core competencies": "skills",
    "key skills": "skills",
    "areas of expertise": "skills",
    "technologies": "skills",
    "technical expertise": "skills",
    # Projects
    "projects": "projects",
    "key projects": "projects",
    "personal projects": "projects",
    "academic projects": "projects",
    "relevant projects": "projects",
    # Certifications
    "certifications": "certifications",
    "certificates": "certifications",
    "courses": "certifications",
    # Achievements & Paper Presentations
    "achievements": "achievements",
    "accomplishments": "achievements",
    "honors  awards": "achievements",
    "awards": "achievements",
    "key achievements": "achievements",
    "paper presentation": "achievements",
    "paper presentations": "achievements",
    "publications": "achievements",
}


def _document_text(document) -> str:
    """Return text from common Word resume layouts, including tables."""
    parts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" ".join(cells))
    return "\n".join(parts).strip()


def _extract_text(file_name: str, file_bytes: bytes) -> str:
    suffix = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
    if suffix not in SUPPORTED_RESUME_EXTENSIONS:
        supported = ", ".join(f".{extension}" for extension in SUPPORTED_RESUME_EXTENSIONS)
        raise ResumeParsingError(f"Unsupported file type. Upload one of: {supported}.")

    if suffix == "pdf":
        import fitz

        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in document).strip()
        except Exception as exc:
            raise ResumeParsingError("The PDF could not be read. Please upload a valid PDF file.") from exc
    if suffix == "docx":
        try:
            from docx import Document

            return _document_text(Document(BytesIO(file_bytes)))
        except ImportError as exc:
            raise ResumeParsingError(
                "Word import requires python-docx. Install the project dependencies and try again."
            ) from exc
        except Exception as exc:
            raise ResumeParsingError(
                "The Word document could not be read. Please upload a valid .docx file."
            ) from exc

    return file_bytes.decode("utf-8", errors="ignore").strip()


def _clean_text(text: str) -> str:
    # Fix hyphenated word breaks from PDF extraction (e.g., "Operating Sys-\n tems" -> "Operating Systems")
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    text = re.sub(r'(\w+)-\s*,\s*(\w+)', r'\1\2', text)
    return text


def _preprocess_text(text: str) -> str:
    text = _clean_text(text)
    # Insert double newlines before major section headings
    keywords = [
        r"PROJECTS", r"KEY PROJECTS", r"PERSONAL PROJECTS", r"ACADEMIC PROJECTS",
        r"CERTIFICATIONS", r"LICENSES & CERTIFICATIONS", r"CERTIFICATES", r"COURSES",
        r"PAPER PRESENTATION", r"PAPER PRESENTATIONS", r"PUBLICATIONS",
        r"ACHIEVEMENTS", r"ACCOMPLISHMENTS", r"HONORS & AWARDS", r"AWARDS",
        r"EDUCATION", r"ACADEMIC BACKGROUND",
        r"EXPERIENCE", r"WORK EXPERIENCE", r"PROFESSIONAL EXPERIENCE", r"EMPLOYMENT HISTORY",
        r"SKILLS", r"TECHNICAL SKILLS", r"CORE COMPETENCIES",
        r"SUMMARY", r"PROFESSIONAL SUMMARY", r"PROFILE", r"OBJECTIVE", r"CAREER OBJECTIVE",
    ]
    pattern = r"(?:^|[\s,;•\*]+)(" + "|".join(keywords) + r")\b(?:\s*[:,-]|\s*(?=[A-Z\n•\*]|$))"
    return re.sub(pattern, r"\n\n\1\n", text)


def _sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        normalized = re.sub(r"[^a-z ]", "", line_clean.lower()).strip()
        section_name = SECTION_NAMES.get(normalized)
        if section_name:
            current = section_name
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line_clean)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def _parse_categorized_skills(skills_text: str) -> list[str]:
    if not skills_text:
        return []

    lines = [l.strip() for l in skills_text.splitlines() if l.strip()]
    categorized = []
    current_cat = None
    current_items = []

    for line in lines:
        clean = re.sub(r"^[•\*\-\s]+", "", line).strip()
        clean = re.sub(r"[\s.,]+$", "", clean)
        if not clean or clean.upper().startswith("SKILLS") or clean.upper() in ("TECHNICAL SKILLS", "KEY SKILLS", "CORE SKILLS"):
            continue

        if ":" in clean:
            parts = clean.split(":", 1)
            cat_name = parts[0].strip()
            rest = parts[1].strip()

            if current_cat:
                skills_str = ", ".join(current_items)
                categorized.append(f"{current_cat}: {skills_str}" if skills_str else current_cat)
                current_items = []

            current_cat = cat_name
            if rest:
                for item in re.split(r"[,|\t;]", rest):
                    i_clean = item.strip()
                    if i_clean:
                        current_items.append(i_clean)
        else:
            if current_cat:
                for item in re.split(r"[,|\t;]", clean):
                    i_clean = item.strip()
                    if i_clean:
                        current_items.append(i_clean)
            else:
                for item in re.split(r"[,|\t;]", clean):
                    i_clean = item.strip()
                    if i_clean:
                        current_items.append(i_clean)

    if current_cat:
        skills_str = ", ".join(current_items)
        categorized.append(f"{current_cat}: {skills_str}" if skills_str else current_cat)
    elif current_items:
        return current_items

    return categorized if categorized else [s.strip() for s in skills_text.split(",") if s.strip()]


def _parse_projects(projects_text: str) -> list[dict]:
    if not projects_text:
        return []
    lines = [l.strip() for l in projects_text.splitlines() if l.strip()]
    projects = []
    current_proj = None

    for line in lines:
        raw_has_bullet = line.startswith("•") or line.startswith("*")
        clean = re.sub(r"^[•\*\-\s]+", "", line).strip()
        if not clean or clean.upper() in ("PROJECTS", "KEY PROJECTS"):
            continue

        is_new_header = raw_has_bullet or (("–" in clean or " - " in clean) and len(clean.split()) < 10)

        if is_new_header and not (current_proj and not raw_has_bullet and len(current_proj["description"]) == 0):
            if current_proj:
                projects.append(current_proj)
            parts = re.split(r"\s*[–:]\s*|\s+-\s+", clean, maxsplit=1)
            name = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            current_proj = {"name": name, "link": "", "technologies": "", "description": desc}
        else:
            if current_proj:
                if current_proj["description"]:
                    current_proj["description"] += "\n" + clean
                else:
                    current_proj["description"] = clean
            else:
                parts = re.split(r"\s*[–:]\s*|\s+-\s+", clean, maxsplit=1)
                current_proj = {
                    "name": parts[0].strip(),
                    "link": "",
                    "technologies": "",
                    "description": parts[1].strip() if len(parts) > 1 else "",
                }

    if current_proj:
        projects.append(current_proj)
    return projects


def _parse_education(education_text: str) -> list[dict]:
    if not education_text:
        return []

    lines = [l.strip() for l in education_text.splitlines() if l.strip()]
    items = []
    current = None

    for line in lines:
        if line.upper() in ("EDUCATION", "ACADEMIC BACKGROUND", "ACADEMIC QUALIFICATIONS"):
            continue

        is_degree = bool(re.search(r"b\.tech|m\.tech|b\.e\.|b\.s\.|m\.s\.|bachelor|master|hsc|sslc|higher secondary|secondary|diploma|degree", line, re.IGNORECASE))
        is_date_only = bool(re.fullmatch(r"(\d{4}\s*[–-]\s*\d{4}|\d{4})", line))
        is_pure_score = bool(re.fullmatch(r"\s*(?:cgpa:\s*[\d.]+(?:/\d+)?|\b\d{1,2}(?:\.\d+)?%)\s*", line, re.IGNORECASE))

        if is_degree:
            if current and (current["degree"] or current["school"]):
                items.append(current)

            date_match = re.search(r"(\d{4}\s*[–-]\s*\d{4}|\d{4})", line)
            dates = date_match.group(0) if date_match else ""
            degree_text = re.sub(r"\d{4}\s*[–-]\s*\d{4}|\d{4}", "", line).strip()
            degree_text = re.sub(r"[\s–-]+$", "", degree_text).strip()

            dates_split = [d.strip() for d in dates.split("–") if d.strip()]
            start_date = dates_split[0] if dates_split else ""
            end_date = dates_split[1] if len(dates_split) > 1 else (dates_split[0] if dates_split else "")

            current = {
                "school": "",
                "degree": degree_text,
                "field": "",
                "start_date": start_date,
                "end_date": end_date,
            }

        elif is_date_only and current:
            dates_split = [d.strip() for d in line.split("–") if d.strip()]
            current["start_date"] = dates_split[0] if dates_split else ""
            current["end_date"] = dates_split[1] if len(dates_split) > 1 else (dates_split[0] if dates_split else "")

        elif is_pure_score and current:
            if current["field"]:
                current["field"] += " " + line
            else:
                current["field"] = line

        else:
            if current:
                cgpa_match = re.search(r"(cgpa:\s*[\d.]+(?:/\d+)?|\b\d{1,2}(?:\.\d+)?%)", line, re.IGNORECASE)
                if cgpa_match:
                    score_str = cgpa_match.group(0)
                    school_str = re.sub(r"(cgpa:\s*[\d.]+(?:/\d+)?|\b\d{1,2}(?:\.\d+)?%)", "", line, flags=re.I).strip()
                    current["field"] = (current["field"] + " " + score_str).strip() if current["field"] else score_str
                    if school_str:
                        current["school"] = (current["school"] + " " + school_str).strip() if current["school"] else school_str
                else:
                    current["school"] = (current["school"] + " " + line).strip() if current["school"] else line
            else:
                date_match = re.search(r"(\d{4}\s*[–-]\s*\d{4}|\d{4})", line)
                dates = date_match.group(0) if date_match else ""
                school_text = re.sub(r"\d{4}\s*[–-]\s*\d{4}|\d{4}", "", line).strip()
                cgpa_match = re.search(r"(cgpa:\s*[\d.]+(?:/\d+)?|\b\d{1,2}(?:\.\d+)?%)", school_text, re.IGNORECASE)
                field_text = ""
                if cgpa_match:
                    field_text = cgpa_match.group(0)
                    school_text = re.sub(r"(cgpa:\s*[\d.]+(?:/\d+)?|\b\d{1,2}(?:\.\d+)?%)", "", school_text, flags=re.I).strip()
                dates_split = [d.strip() for d in dates.split("–") if d.strip()]
                current = {
                    "school": school_text,
                    "degree": "",
                    "field": field_text,
                    "start_date": dates_split[0] if dates_split else "",
                    "end_date": dates_split[1] if len(dates_split) > 1 else (dates_split[0] if dates_split else ""),
                }

    if current and (current["degree"] or current["school"]):
        items.append(current)

    return items if items else [{"school": education_text, "degree": "", "field": "", "start_date": "", "end_date": ""}]


def _parse_list_items(text: str) -> list[str]:
    if not text:
        return []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    items = []
    current_item = ""

    for line in lines:
        raw_has_bullet = bool(re.match(r"^[•\*\-\–\d+\.]\s*", line))
        clean = re.sub(r"^[•\*\-\–\d+\.\s]+", "", line).strip()
        clean = re.sub(r"[\s.,]+$", "", clean)
        if not clean or clean.upper() in ("CERTIFICATIONS", "ACHIEVEMENTS", "PAPER PRESENTATION", "PAPER PRESENTATIONS", "PUBLICATIONS", "AWARDS", "HONORS & ACHIEVEMENTS"):
            continue

        if raw_has_bullet or not current_item:
            if current_item:
                items.append(current_item)
            current_item = clean
        else:
            current_item += " " + clean

    if current_item:
        items.append(current_item)

    return items


def parse_uploaded_resume(file_name: str, file_bytes: bytes) -> dict:
    raw_text = _extract_text(file_name, file_bytes)
    text = _preprocess_text(raw_text)
    sections = _sections(text)
    resume = default_resume()

    header_text = sections.get("header", "")
    header_lines = [line.strip() for line in header_text.splitlines() if line.strip()]
    all_lines = [line.strip() for line in text.splitlines() if line.strip()]

    # 1. Name
    for line in (header_lines or all_lines):
        if (
            not re.search(r"[\w.+-]+@[\w-]+", line)
            and not re.search(r"\d{7,}", line)
            and not re.search(r"https?://", line)
            and len(line) < 50
        ):
            resume["personal"]["name"] = line
            break

    # 2. Email
    email_match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    if email_match:
        resume["personal"]["email"] = email_match.group(0)

    # 3. Phone
    phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d[\d ()-]{7,}\d", text)
    if phone_match:
        resume["personal"]["phone"] = phone_match.group(0).strip()

    # 4. Portfolio / LinkedIn / GitHub
    linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", text, re.IGNORECASE)
    github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", text, re.IGNORECASE)
    url_match = re.search(r"https?://[^\s]+", text)
    if linkedin_match:
        resume["personal"]["portfolio"] = linkedin_match.group(0)
    elif github_match:
        resume["personal"]["portfolio"] = github_match.group(0)
    elif url_match:
        resume["personal"]["portfolio"] = url_match.group(0)

    # 5. Summary
    resume["summary"] = sections.get("summary", "")

    # 6. Skills
    skills_text = sections.get("skills", "")
    if skills_text:
        resume["skills"] = _parse_categorized_skills(skills_text)

    # 7. Education
    education_text = sections.get("education", "")
    if education_text:
        resume["education"] = _parse_education(education_text)

    if resume["education"] and resume["education"][0].get("degree"):
        deg = resume["education"][0]["degree"]
        resume["personal"]["headline"] = f"{deg} Engineer".strip()
    else:
        resume["personal"]["headline"] = "Artificial Intelligence & Data Science Engineer"

    # 8. Experience
    experience_text = sections.get("experience", "")
    if experience_text and len(experience_text.strip()) > 10:
        exp_lines = [l.strip() for l in experience_text.splitlines() if l.strip()]
        if exp_lines:
            role = exp_lines[0]
            company = exp_lines[1] if len(exp_lines) > 1 and not exp_lines[1].startswith("•") and not exp_lines[1].startswith("-") else ""
            desc_start = 2 if company else 1
            desc = "\n".join(exp_lines[desc_start:])
            resume["experience"] = [{
                "role": role,
                "company": company,
                "start_date": "",
                "end_date": "",
                "description": desc,
            }]
    else:
        resume["experience"] = []

    # 9. Projects
    projects_text = sections.get("projects", "")
    if projects_text:
        parsed_projects = _parse_projects(projects_text)
        if parsed_projects:
            resume["projects"] = parsed_projects

    # 10. Certifications
    cert_text = sections.get("certifications", "")
    if cert_text:
        resume["certifications"] = _parse_list_items(cert_text)

    # 11. Achievements & Paper Presentations
    achieve_text = sections.get("achievements", "")
    if achieve_text:
        resume["achievements"] = _parse_list_items(achieve_text)

    resume["source_text"] = raw_text
    return resume
