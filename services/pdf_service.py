from __future__ import annotations

from html import escape
from io import BytesIO
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _clean_str(text: str) -> str:
    if not text:
        return ""
    s = str(text).strip()
    s = re.sub(r"[\s,|]+$", "", s)
    s = re.sub(r"\.,", ".", s)
    s = re.sub(r",\.", ".", s)
    s = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", s)
    return escape(s)


def build_resume_pdf(resume: dict, template: str = "classic") -> bytes:
    buffer = BytesIO()

    primary_color = "#1E3A8A"  # Deep Blue Accent
    text_color = "#0F172A"     # Dark Charcoal Text
    secondary_color = "#475569"# Medium Slate Gray

    margin = 0.5 * inch

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=margin,
        leftMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "ResName",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor(primary_color),
        alignment=1,  # Centered
        fontName="Helvetica-Bold",
        spaceAfter=3,
    )

    headline_style = ParagraphStyle(
        "ResHeadline",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor(secondary_color),
        alignment=1,  # Centered
        fontName="Helvetica-Oblique",
        spaceAfter=4,
    )

    contact_style = ParagraphStyle(
        "ResContact",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor(secondary_color),
        alignment=1,  # Centered
        fontName="Helvetica",
        spaceAfter=8,
    )

    section_heading_style = ParagraphStyle(
        "ResSecHead",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor(primary_color),
        fontName="Helvetica-Bold",
        spaceBefore=9,
        spaceAfter=2,
    )

    sub_heading_style = ParagraphStyle(
        "ResSubHead",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor(text_color),
        fontName="Helvetica-Bold",
        spaceAfter=2,
    )

    body_style = ParagraphStyle(
        "ResBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor(text_color),
        fontName="Helvetica",
        spaceAfter=3,
    )

    bullet_style = ParagraphStyle(
        "ResBullet",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3,
    )

    sub_bullet_style = ParagraphStyle(
        "ResSubBullet",
        parent=body_style,
        leftIndent=24,
        firstLineIndent=-8,
        spaceAfter=2,
    )

    story = []
    personal = resume.get("personal", {})

    # 1. Header (Name, Headline, Contact details)
    name = _clean_str(personal.get("name", "KOUSHIKA R"))
    story.append(Paragraph(name, name_style))

    headline = _clean_str(personal.get("headline", ""))
    if not headline:
        headline = "B.Tech in Artificial Intelligence &amp; Data Science Engineer"
    story.append(Paragraph(headline, headline_style))

    contact_items = []
    for field in ("email", "phone", "location", "portfolio"):
        val = _clean_str(personal.get(field, ""))
        if val:
            contact_items.append(val)

    if contact_items:
        contact_line = " &nbsp;•&nbsp; ".join(contact_items)
        story.append(Paragraph(contact_line, contact_style))

    # Top divider line
    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor(primary_color),
            spaceBefore=2,
            spaceAfter=6,
        )
    )

    def add_section_header(title: str):
        story.append(Paragraph(title.upper(), section_heading_style))

    # 2. Professional Summary
    summary = resume.get("summary", "")
    if summary:
        add_section_header("Professional Summary")
        story.append(Paragraph(_clean_str(summary).replace("\n", "<br/>"), body_style))

    # 3. Technical Skills
    skills = resume.get("skills", [])
    if skills:
        add_section_header("Technical Skills")
        categorized = []
        plain = []
        for s in skills:
            cleaned = _clean_str(s)
            if not cleaned:
                continue
            if ":" in cleaned:
                parts = cleaned.split(":", 1)
                cat = parts[0].strip()
                val = parts[1].strip()
                categorized.append((cat, val))
            else:
                plain.append(cleaned)

        for cat, val in categorized:
            if val:
                story.append(Paragraph(f"• <b>{cat}:</b> {val}", bullet_style))
            else:
                story.append(Paragraph(f"• <b>{cat}</b>", bullet_style))

        if plain:
            plain_str = ", ".join(plain)
            story.append(Paragraph(f"• {plain_str}", bullet_style))

    # 4. Key Projects
    projects = resume.get("projects", [])
    valid_proj = [p for p in projects if p.get("name") or p.get("description")]
    if valid_proj:
        add_section_header("Key Projects")
        for proj in valid_proj:
            name = _clean_str(proj.get("name", ""))
            link = _clean_str(proj.get("link", ""))
            techs = proj.get("technologies", [])
            if isinstance(techs, list):
                tech_str = ", ".join(_clean_str(t) for t in techs if t)
            else:
                tech_str = _clean_str(str(techs))

            header_text = f"• <b>{name}</b>"
            if tech_str:
                header_text += f" | <i>{tech_str}</i>"
            if link:
                header_text += f" ({link})"

            story.append(Paragraph(header_text, bullet_style))

            desc = proj.get("description", "")
            if desc:
                bullets = [b.strip() for b in desc.splitlines() if b.strip()]
                for b in bullets:
                    clean_b = re.sub(r"^[•\*\-\s]+", "", b)
                    story.append(Paragraph(f"- {_clean_str(clean_b)}", sub_bullet_style))

    # 5. Experience
    experience = resume.get("experience", [])
    valid_exp = [e for e in experience if e.get("role") or e.get("description")]
    if valid_exp:
        add_section_header("Work Experience")
        for exp in valid_exp:
            role = _clean_str(exp.get("role", ""))
            company = _clean_str(exp.get("company", ""))
            dates = _clean_str(exp.get("dates", f"{exp.get('start_date', '')} {exp.get('end_date', '')}".strip()))

            header_text = f"• <b>{role}</b>" + (f" — <i>{company}</i>" if company else "")
            if dates:
                header_text += f" &nbsp;({dates})"

            story.append(Paragraph(header_text, bullet_style))

            desc = exp.get("description", "")
            if desc:
                bullets = [b.strip() for b in desc.splitlines() if b.strip()]
                for b in bullets:
                    clean_b = re.sub(r"^[•\*\-\s]+", "", b)
                    story.append(Paragraph(f"- {_clean_str(clean_b)}", sub_bullet_style))

    # 6. Education
    education = resume.get("education", [])
    valid_edu = [e for e in education if e.get("school") or e.get("degree")]
    if valid_edu:
        add_section_header("Education")
        for edu in valid_edu:
            school = _clean_str(edu.get("school", ""))
            degree = _clean_str(edu.get("degree", ""))
            field = _clean_str(edu.get("field", ""))
            dates = _clean_str(f"{edu.get('start_date', '')} {edu.get('end_date', '')}".strip())

            deg_str = f"{degree} {field}".strip()
            header_text = f"• <b>{deg_str or school}</b>" + (f" — {school}" if deg_str and school else "")
            if dates:
                header_text += f" &nbsp;({dates})"

            story.append(Paragraph(header_text, bullet_style))

    # 7. Certifications
    certs = resume.get("certifications", [])
    if certs:
        add_section_header("Certifications")
        for c in certs:
            story.append(Paragraph(f"• {_clean_str(c)}", bullet_style))

    # 8. Honors & Achievements
    achievements = resume.get("achievements", [])
    if achievements:
        add_section_header("Honors & Achievements")
        for a in achievements:
            story.append(Paragraph(f"• {_clean_str(a)}", bullet_style))

    # 9. Custom Sections
    for custom in resume.get("custom_sections", []):
        if custom.get("title") and custom.get("content"):
            add_section_header(_clean_str(custom["title"]))
            content_lines = custom["content"].splitlines()
            for line in content_lines:
                if line.strip():
                    story.append(Paragraph(f"• {_clean_str(re.sub(r'^[•\*\-\s]+', '', line))}", bullet_style))

    doc.build(story)
    return buffer.getvalue()
