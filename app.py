from __future__ import annotations

import streamlit as st

from ai.generator import critique_generated_content
from ai.llm import generate_resume_summary
from ai.matching import hybrid_match_score
from config.settings import APP_TITLE
from data.database import get_resume, list_resumes, save_resume
from services.ats_service import ats_score_for_resume
from services.job_service import evaluate_resume_against_job
from services.pdf_service import build_resume_pdf
from services.resume_parser import (
    ResumeParsingError,
    SUPPORTED_RESUME_EXTENSIONS,
    parse_uploaded_resume,
)
from services.resume_service import build_resume_payload
from services.tailoring_service import generate_tailoring_recommendations


st.set_page_config(page_title=APP_TITLE, page_icon="R", layout="wide")

st.markdown(
    """
    <style>
    :root { --ink: #172033; --muted: #657085; --line: #e4e8ef; --accent: #e36b3d; --soft: #fff6f0; }
    .block-container { max-width: 1180px; padding-top: 2rem; }
    h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
    h1 { font-size: 2.4rem; margin-bottom: .35rem; }
    h2 { margin-top: 1.6rem; }
    [data-testid="stMetric"] { background: #fff; border: 1px solid var(--line); padding: 1rem; border-radius: 8px; }
    .eyebrow { color: var(--accent); font-weight: 700; font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; }
    .muted { color: var(--muted); }
    .hero { background: linear-gradient(115deg, #fff7f0 0%, #fff 62%); border: 1px solid #f0ddd0; border-radius: 10px; padding: 2rem; margin-bottom: 1.5rem; }
    .status { border-left: 4px solid var(--accent); background: var(--soft); padding: .9rem 1rem; border-radius: 4px; color: var(--ink); }
    </style>
    """,
    unsafe_allow_html=True,
)


def empty_education() -> dict:
    return {"school": "", "degree": "", "field": "", "start_date": "", "end_date": ""}


def empty_experience() -> dict:
    return {"role": "", "company": "", "start_date": "", "end_date": "", "description": ""}


def empty_project() -> dict:
    return {"name": "", "link": "", "technologies": "", "description": ""}


def resume_text(resume: dict) -> str:
    personal = resume.get("personal", {})
    parts = [personal.get("name", ""), personal.get("headline", ""), personal.get("target_role", ""), resume.get("summary", ""), ", ".join(resume.get("skills", []))]
    for item in resume.get("experience", []) + resume.get("education", []) + resume.get("projects", []):
        parts.extend(str(value) for value in item.values())
    parts.extend(resume.get("certifications", []))
    parts.extend(resume.get("achievements", []))
    for section in resume.get("custom_sections", []):
        parts.extend([section.get("title", ""), section.get("content", "")])
    return "\n".join(part for part in parts if part)


def render_repeater(section: str, items: list[dict], factory, labels: tuple[str, ...]) -> list[dict]:
    st.markdown(f"#### {section}")
    if not items:
        items = [factory()]
    for index, item in enumerate(items):
        st.markdown(f"**{section} {index + 1}**")
        columns = st.columns(2)
        for field_index, label in enumerate(labels):
            with columns[field_index % 2]:
                item[label] = st.text_input(label.replace("_", " ").title(), value=item.get(label, ""), key=f"{section.lower()}_{index}_{label}")
        if section in ("Experience", "Projects"):
            prompt = "What did you accomplish?" if section == "Experience" else "What did you build or deliver?"
            item["description"] = st.text_area(prompt, value=item.get("description", ""), key=f"{section.lower()}_{index}_description", height=90)
    if st.button(f"+ Add another {section.lower()}", key=f"add_{section.lower()}"):
        items.append(factory())
        st.session_state[f"{section.lower()}_items"] = items
        st.rerun()
    st.session_state[f"{section.lower()}_items"] = items
    return items


def render_list_editor(section: str, items: list[str]) -> list[str]:
    st.markdown(f"#### {section}")
    if not items:
        items = [""]
    for index, item in enumerate(items):
        items[index] = st.text_input(f"{section[:-1]} {index + 1}", value=item, key=f"{section.lower()}_{index}")
    if st.button(f"+ Add another {section[:-1].lower()}", key=f"add_{section.lower()}"):
        items.append("")
        st.session_state[f"{section.lower()}_items"] = items
        st.rerun()
    st.session_state[f"{section.lower()}_items"] = items
    return [item.strip() for item in items if item.strip()]


def render_custom_sections(items: list[dict]) -> list[dict]:
    st.markdown("#### Custom sections")
    st.caption("Add sections such as Awards, Publications, Volunteering, Languages, Interests, or anything unique to your career.")
    if not items:
        items = [{"title": "", "content": ""}]
    for index, item in enumerate(items):
        title_col, remove_col = st.columns([5, 1])
        with title_col:
            item["title"] = st.text_input("Section title", value=item.get("title", ""), key=f"custom_title_{index}")
        with remove_col:
            if st.button("Remove", key=f"remove_custom_{index}") and len(items) > 1:
                items.pop(index)
                st.session_state["custom_sections_items"] = items
                st.rerun()
        item["content"] = st.text_area("Section content", value=item.get("content", ""), key=f"custom_content_{index}", height=100)
    if st.button("+ Add custom section", key="add_custom_section"):
        items.append({"title": "", "content": ""})
        st.session_state["custom_sections_items"] = items
        st.rerun()
    st.session_state["custom_sections_items"] = items
    return [item for item in items if item.get("title", "").strip() or item.get("content", "").strip()]


def readiness(resume: dict | None) -> tuple[int, list[str]]:
    if not resume:
        return 0, ["Start by creating or importing a resume."]
    personal = resume.get("personal", {})
    checks = {
        "name": bool(personal.get("name")),
        "email": bool(personal.get("email")),
        "summary": bool(resume.get("summary")),
        "skills": bool(resume.get("skills")),
        "experience": any(item.get("role") or item.get("company") for item in resume.get("experience", [])),
        "education": any(item.get("school") or item.get("degree") for item in resume.get("education", [])),
    }
    missing = [label.title() for label, present in checks.items() if not present]
    return round(sum(checks.values()) / len(checks) * 100), missing


def home_page() -> None:
    resume = st.session_state.get("resume")
    score, missing = readiness(resume)
    st.markdown('<div class="eyebrow">Career workspace</div>', unsafe_allow_html=True)
    st.title("Build a resume that gets read.")
    st.markdown('<div class="hero"><h3>Your next best action</h3><p class="muted">Create a focused resume, compare it with a real job, then export a clean final copy.</p></div>', unsafe_allow_html=True)
    if resume:
        st.markdown(f'<div class="status">Resume loaded for <b>{resume.get("personal", {}).get("name", "your profile")}</b>. Readiness: <b>{score}%</b>.</div>', unsafe_allow_html=True)
        metrics = st.columns(4)
        metrics[0].metric("Readiness", f"{score}%")
        metrics[1].metric("Skills", len(resume.get("skills", [])))
        metrics[2].metric("Experience", len(resume.get("experience", [])))
        metrics[3].metric("Education", len(resume.get("education", [])))
        if missing:
            st.info("Complete next: " + ", ".join(missing))
    else:
        st.info("No resume loaded yet. Open Build Resume to import an existing file or start fresh.")
    st.subheader("How this workspace works")
    cols = st.columns(4)
    for col, number, title, text in zip(cols, ["01", "02", "03", "04"], ["Build", "Improve", "Match", "Export"], ["Add evidence and achievements.", "Create an ATS-friendly summary.", "Find gaps against a target role.", "Download and save your final copy."]):
        with col:
            st.markdown(f"**{number}  {title}**")
            st.caption(text)


def load_resume_into_session_state(resume: dict) -> None:
    st.session_state["resume"] = resume

    widget_prefixes = ("contact_", "resume_", "education_", "experience_", "projects_", "certifications_", "achievements_", "custom_", "add_", "remove_")
    for key in list(st.session_state.keys()):
        if any(key.startswith(prefix) for prefix in widget_prefixes):
            del st.session_state[key]

    personal = resume.get("personal", {})
    st.session_state["contact_name"] = personal.get("name", "")
    st.session_state["contact_email"] = personal.get("email", "")
    st.session_state["contact_phone"] = personal.get("phone", "")
    st.session_state["contact_location"] = personal.get("location", "")
    st.session_state["contact_portfolio"] = personal.get("portfolio", "")
    st.session_state["resume_headline"] = personal.get("headline", "")
    st.session_state["resume_target_role"] = personal.get("target_role", "")
    st.session_state["resume_summary"] = resume.get("summary", "")
    st.session_state["resume_skills"] = ", ".join(resume.get("skills", []))

    edu_list = resume.get("education", [])
    st.session_state["education_items"] = edu_list
    for idx, item in enumerate(edu_list):
        for label in ("school", "degree", "field", "start_date", "end_date"):
            st.session_state[f"education_{idx}_{label}"] = item.get(label, "")

    exp_list = resume.get("experience", [])
    st.session_state["experience_items"] = exp_list
    for idx, item in enumerate(exp_list):
        for label in ("role", "company", "start_date", "end_date"):
            st.session_state[f"experience_{idx}_{label}"] = item.get(label, "")
        st.session_state[f"experience_{idx}_description"] = item.get("description", "")

    proj_list = resume.get("projects", [])
    st.session_state["projects_items"] = proj_list
    for idx, item in enumerate(proj_list):
        for label in ("name", "link", "technologies"):
            tech_val = item.get(label, "")
            if isinstance(tech_val, list):
                tech_val = ", ".join(tech_val)
            st.session_state[f"projects_{idx}_{label}"] = str(tech_val)
        st.session_state[f"projects_{idx}_description"] = item.get("description", "")

    cert_list = resume.get("certifications", [])
    st.session_state["certifications_items"] = cert_list
    for idx, cert in enumerate(cert_list):
        st.session_state[f"certifications_{idx}"] = cert

    ach_list = resume.get("achievements", [])
    st.session_state["achievements_items"] = ach_list
    for idx, ach in enumerate(ach_list):
        st.session_state[f"achievements_{idx}"] = ach

    custom_list = resume.get("custom_sections", [])
    st.session_state["custom_sections_items"] = custom_list
    for idx, c in enumerate(custom_list):
        st.session_state[f"custom_title_{idx}"] = c.get("title", "")
        st.session_state[f"custom_content_{idx}"] = c.get("content", "")


def build_page() -> None:
    st.title("Build your resume")
    st.caption("Import an existing resume or enter the details manually. We keep your claims grounded in your information.")
    uploaded_file = st.file_uploader(
        "Import a PDF, Word, or text resume",
        type=SUPPORTED_RESUME_EXTENSIONS,
        help="Supported formats: PDF, Word (.docx), and TXT. For legacy .doc files, save them as .docx first.",
    )
    if uploaded_file and st.button("Import and review extracted details", type="primary"):
        try:
            parsed = parse_uploaded_resume(uploaded_file.name, uploaded_file.getvalue())
        except ResumeParsingError as exc:
            st.error(str(exc))
        else:
            load_resume_into_session_state(parsed)
            st.session_state["import_notice"] = f"Imported {uploaded_file.name}. Review the fields below before saving."
            st.rerun()
    if st.session_state.pop("import_notice", None):
        st.success("Resume imported. Review and edit the fields below.")

    resume = st.session_state.get("resume", {})
    personal = resume.get("personal", {})
    st.subheader("Contact details")
    first, second = st.columns(2)
    with first:
        name = st.text_input("Full name", value=personal.get("name", ""), key="contact_name")
        email = st.text_input("Email", value=personal.get("email", ""), key="contact_email")
        phone = st.text_input("Phone", value=personal.get("phone", ""), key="contact_phone")
    with second:
        location = st.text_input("City and country", value=personal.get("location", ""), key="contact_location")
        portfolio = st.text_input("LinkedIn or portfolio", value=personal.get("portfolio", ""), key="contact_portfolio")
    st.subheader("Professional positioning")
    headline = st.text_input("Professional headline", value=personal.get("headline", ""), placeholder="Example: Software Engineer | Python & Cloud Systems", key="resume_headline")
    target_role = st.text_input("Target role", value=personal.get("target_role", ""), placeholder="Example: Backend Engineer", key="resume_target_role")
    summary = st.text_area("Summary", value=resume.get("summary", ""), height=120, placeholder="Describe your role, strongest skills, and the value you bring.", key="resume_summary")
    skills = st.text_input("Skills", value=", ".join(resume.get("skills", [])), help="Separate skills with commas.", key="resume_skills")

    education_items = render_repeater("Education", st.session_state.get("education_items", resume.get("education", [empty_education()])), empty_education, ("school", "degree", "field", "start_date", "end_date"))
    experience_items = render_repeater("Experience", st.session_state.get("experience_items", resume.get("experience", [empty_experience()])), empty_experience, ("role", "company", "start_date", "end_date"))
    project_items = render_repeater("Projects", st.session_state.get("projects_items", resume.get("projects", [empty_project()])), empty_project, ("name", "link", "technologies"))
    certifications = render_list_editor("Certifications", st.session_state.get("certifications_items", resume.get("certifications", [])))
    achievements = render_list_editor("Achievements", st.session_state.get("achievements_items", resume.get("achievements", [])))
    custom_sections = render_custom_sections(st.session_state.get("custom_sections_items", resume.get("custom_sections", [])))
    submitted = st.button("Generate Resume", type="primary", use_container_width=True)
    if submitted:
        exp_0 = experience_items[0] if experience_items else empty_experience()
        payload = build_resume_payload({"name": name, "email": email, "phone": phone, "location": location, "portfolio": portfolio, "summary": summary, "skills": skills, "role": exp_0.get("role", ""), "company": exp_0.get("company", ""), "start_date": exp_0.get("start_date", ""), "end_date": exp_0.get("end_date", ""), "experience_description": exp_0.get("description", "")})
        payload["personal"]["headline"] = headline
        payload["personal"]["target_role"] = target_role
        payload["education"] = education_items
        payload["experience"] = experience_items
        payload["projects"] = [
            {**item, "technologies": [technology.strip() for technology in str(item.get("technologies", "")).split(",") if technology.strip()]}
            for item in project_items
            if item.get("name") or item.get("description") or item.get("link")
        ]
        payload["certifications"] = certifications
        payload["achievements"] = achievements
        payload["custom_sections"] = custom_sections
        st.session_state["resume"] = payload
        st.success("Resume generated with all sections. Continue to Match Job or Finalize & Export.")


def match_page() -> None:
    st.title("Match your resume to a job")
    resume = st.session_state.get("resume")
    if not resume:
        st.warning("Build or import a resume first.")
        return
    job_text = st.text_area("Paste the target job description", height=220, placeholder="Paste the complete job description here...")
    if st.button("Analyze fit", type="primary") and job_text:
        result = hybrid_match_score(resume_text(resume), job_text)
        evaluation = evaluate_resume_against_job(resume, job_text)
        ats = ats_score_for_resume(resume_text(resume), job_text)
        first, second, third = st.columns(3)
        first.metric("Overall match", f"{result['final_score']}%")
        second.metric("ATS score", f"{ats['score']}%")
        third.metric("Matched keywords", len(result["matched_keywords"]))
        st.caption(
            f"ATS score: {ats['keyword_coverage']}% job-keyword coverage "
            f"({ats['overlap_count']} matched) plus {ats['content_quality']}/20 for resume substance."
        )
        st.subheader("What to improve")
        st.write("Missing keywords:", ", ".join(result["missing_keywords"]) or "None found")
        recommendations = generate_tailoring_recommendations(resume, job_text)
        for item in recommendations["recommended_improvements"]:
            st.write("-", item)
        st.caption("Recommendations are evidence-based. Do not add a skill unless you can support it with real experience.")


def finalize_page() -> None:
    st.title("Finalize and export")
    resume = st.session_state.get("resume")
    if not resume:
        st.warning("Build or import a resume first.")
        return
    score, missing = readiness(resume)
    st.metric("Resume readiness", f"{score}%")
    if missing:
        st.warning("Still to review: " + ", ".join(missing))
    if st.button("Generate ATS-friendly summary", type="primary"):
        st.session_state["generated_summary"] = generate_resume_summary(resume)
    generated_summary = st.session_state.get("generated_summary")
    if generated_summary:
        st.subheader("Suggested summary")
        st.info(generated_summary)
        critique = critique_generated_content(generated_summary, resume)
        if critique.get("is_valid", True):
            st.success("The summary only uses information already present in your resume.")
        if st.button("Accept suggested summary"):
            resume["summary"] = generated_summary
            st.session_state["resume"] = resume
            st.success("Summary added to your resume.")
    st.subheader("Export")
    st.download_button("Download PDF resume", data=build_resume_pdf(resume), file_name="resume.pdf", mime="application/pdf", type="primary")
    if st.button("Save to my resumes"):
        resume_id = save_resume(resume.get("personal", {}).get("name") or "Untitled Resume", resume)
        st.success(f"Saved resume #{resume_id}.")


def saved_page() -> None:
    st.title("Saved resumes")
    resumes = list_resumes()
    if not resumes:
        st.info("No saved resumes yet. Finish a resume and save it from Finalize & Export.")
        return
    for item in resumes:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{item['title']}**  ·  {item['created_at']}")
        with col2:
            if st.button("Load", key=f"load_{item['id']}"):
                loaded = get_resume(item["id"])
                if loaded:
                    load_resume_into_session_state(loaded)
                    st.success("Resume loaded. Open Build Resume to review it.")


with st.sidebar:
    st.markdown("## Resume Studio")
    st.caption("A practical workspace for better applications")
    option = st.radio("", ["Home", "Build Resume", "Match Job", "Finalize & Export", "Saved Resumes"], label_visibility="collapsed")
    st.divider()
    if st.session_state.get("resume"):
        score, _ = readiness(st.session_state["resume"])
        st.caption(f"Current resume readiness: {score}%")

if option == "Home":
    home_page()
elif option == "Build Resume":
    build_page()
elif option == "Match Job":
    match_page()
elif option == "Finalize & Export":
    finalize_page()
else:
    saved_page()
