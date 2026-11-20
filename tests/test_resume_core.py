from ai.llm import generate_resume_summary
from models.resume_schema import default_resume, extract_keyword_set
from services.ats_service import ats_score_for_resume
from services.job_service import evaluate_resume_against_job, extract_job_requirements
from services.resume_parser import parse_uploaded_resume
from services.tailoring_service import generate_tailoring_recommendations, tailor_resume_to_job


def test_default_resume_has_required_sections():
    resume = default_resume()
    assert "personal" in resume
    assert "summary" in resume
    assert "experience" in resume
    assert "skills" in resume


def test_parse_uploaded_text_resume_extracts_core_fields():
    content = b"Aisha Patel\naisha@example.com\n\nProfessional Summary\nPython developer\n\nSkills\nPython, SQL\n\nEducation\nState University"

    resume = parse_uploaded_resume("resume.txt", content)

    assert resume["personal"]["name"] == "Aisha Patel"
    assert resume["personal"]["email"] == "aisha@example.com"
    assert resume["summary"] == "Python developer"
    assert resume["skills"] == ["Python", "SQL"]
    assert resume["education"][0]["school"] == "State University"


def test_parse_uploaded_word_resume_extracts_core_fields_and_table_text():
    from io import BytesIO

    from docx import Document

    document = Document()
    document.add_paragraph("Aisha Patel")
    document.add_paragraph("aisha@example.com")
    document.add_paragraph("Professional Summary")
    document.add_paragraph("Python developer")
    document.add_paragraph("Skills")
    document.add_paragraph("Python, SQL")
    document.add_paragraph("Education")
    document.add_paragraph("State University")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "LinkedIn"
    table.cell(0, 1).text = "linkedin.com/in/aisha-patel"
    buffer = BytesIO()
    document.save(buffer)

    resume = parse_uploaded_resume("resume.docx", buffer.getvalue())

    assert resume["personal"]["name"] == "Aisha Patel"
    assert resume["personal"]["email"] == "aisha@example.com"
    assert resume["summary"] == "Python developer"
    assert resume["skills"] == ["Python", "SQL"]
    assert "linkedin.com/in/aisha-patel" in resume["source_text"]


def test_extract_keyword_set_ignores_noise_and_duplicates():
    text = "Python, FastAPI, SQL, python, Docker, SQL, aws, React"
    keywords = extract_keyword_set(text)
    assert "python" in keywords
    assert "fastapi" in keywords
    assert "sql" in keywords
    assert "docker" in keywords
    assert "aws" in keywords
    assert "react" in keywords
    assert len(keywords) == 6


def test_tailor_resume_to_job_preserves_only_existing_skills():
    resume = {
        "personal": {"name": "Aisha Patel"},
        "summary": "Python developer with SQL experience.",
        "skills": ["Python", "SQL", "FastAPI"],
        "experience": [{"role": "Software Engineer", "description": "Built APIs in Python."}],
    }
    job = "We need a Python engineer with SQL, FastAPI, Docker, and AWS experience."

    tailored = tailor_resume_to_job(resume, job)

    assert "docker" in tailored["missing_keywords"]
    assert "aws" in tailored["missing_keywords"]
    assert "fastapi" in tailored["matched_keywords"]
    assert "python" in tailored["matched_keywords"]
    assert tailored["guardrail"] == "No unsupported claims were added."


def test_generate_resume_summary_uses_known_data_only():
    resume = {
        "personal": {"name": "Aisha Patel"},
        "summary": "",
        "skills": ["Python", "SQL", "FastAPI"],
        "experience": [{"description": "Built APIs in Python and SQL."}],
    }

    summary = generate_resume_summary(resume)

    assert "Python" in summary
    assert "SQL" in summary
    assert "Docker" not in summary
    assert "AWS" not in summary


def test_generate_tailoring_recommendations_are_evidence_based():
    resume = {
        "summary": "Python developer with SQL and FastAPI experience.",
        "skills": ["Python", "SQL", "FastAPI"],
        "experience": [{"description": "Developed API services in Python and SQL."}],
    }
    job = "Python engineer with SQL, FastAPI, Docker, and AWS experience."

    recommendation = generate_tailoring_recommendations(resume, job)

    assert "python" in recommendation["matched_keywords"]
    assert "docker" in recommendation["missing_keywords"]
    assert "aws" in recommendation["missing_keywords"]
    assert "Only add missing skills if" in recommendation["guardrail"]
    assert recommendation["recommended_improvements"]


def test_extract_job_requirements_and_evaluate_resume_against_job():
    resume = {
        "summary": "Python developer with SQL and FastAPI experience.",
        "skills": ["Python", "SQL", "FastAPI"],
        "experience": [{"description": "Developed Python APIs and SQL services."}],
    }
    job = "Senior Python engineer with SQL, FastAPI, Docker, and AWS experience."

    requirements = extract_job_requirements(job)
    evaluation = evaluate_resume_against_job(resume, job)

    assert "python" in requirements
    assert "sql" in requirements
    assert "docker" in requirements
    assert "aws" in requirements
    assert evaluation["match_score"] >= 50
    assert "docker" in evaluation["missing_keywords"]


def test_ats_score_reflects_job_keyword_coverage_instead_of_defaulting_to_100():
    job = "Python developer with SQL, FastAPI, Docker, AWS, and Kubernetes experience."
    matching_resume = (
        "Python developer built FastAPI services with SQL, Docker, AWS, and Kubernetes. "
        "Improved deployment time by 25 percent."
    )
    unrelated_resume = (
        "Accountant with Excel, bookkeeping, invoicing, payroll, reconciliation, tax, and audit experience. "
        "Improved month-end reporting by 25 percent."
    )

    matching_score = ats_score_for_resume(matching_resume, job)
    unrelated_score = ats_score_for_resume(unrelated_resume, job)

    assert matching_score["keyword_coverage"] == 100.0
    assert matching_score["score"] > unrelated_score["score"]
    assert unrelated_score["keyword_coverage"] == 0.0
    assert unrelated_score["score"] < 25
    assert "docker" in unrelated_score["missing_keywords"]
