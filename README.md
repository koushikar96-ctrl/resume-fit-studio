# AI Resume Builder & Job Matching Assistant

A Streamlit-based GenAI product prototype for creating ATS-friendly resumes, matching them against job descriptions, and validating tailoring decisions.

## System goal

The system follows the workflow: Create → Improve → Analyze → Tailor → Validate → Export.

It helps users:

- create a structured resume from personal and professional details
- generate an ATS-friendly summary without inventing experience
- match the resume against a job description
- evaluate keyword and semantic relevance
- check ATS readiness and missing requirements
- store and export resumes as PDFs

## Core design principles

1. Structured resume data model
   - Candidate information is stored in a consistent JSON schema instead of raw free-form text.

2. Guardrails against hallucination
   - The AI can improve wording, but it must not invent qualifications, companies, certifications, or achievements.

3. Hybrid job matching
   - Keyword matching is combined with semantic relevance scoring.

4. Explainability
   - Every score is tied to visible keyword overlap and missing requirements.

5. Product simplicity
   - The system remains manageable and implementable while still demonstrating real GenAI concepts.

## Architecture overview

- Streamlit UI for user interaction
- Resume schema and validation logic
- LLM wrapper with safe fallback
- Matching and ATS analysis services
- Storage layer for saved resumes
- PDF export layer

## Folder structure

- `app.py` — main application entry point
- `config/settings.py` — app configuration
- `models/resume_schema.py` — resume schema and keyword utilities
- `ai/` — generation, LLM, and prompt logic
- `services/` — job matching, ATS scoring, PDF, and tailoring services
- `data/` — SQLite resume storage
- `ui/` — dashboard and reusable UI blocks
- `validators/` — guardrails and quality checks
- `tests/` — core project tests

## Workflow

1. User creates or uploads resume information.
2. The app stores a structured resume object.
3. The system generates a summary and supporting bullets.
4. A critique check verifies that claims remain grounded in the user data.
5. The user pastes a job description.
6. The app extracts job requirements and compares them against the resume.
7. ATS and match scores are produced.
8. Tailoring recommendations are generated only when evidence supports them.
9. The final resume can be saved and exported as a PDF.

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
streamlit run app.py
```

## Current implemented features

- structured resume creation form
- ATS-friendly summary generation
- basic content critique
- keyword extraction and relevance matching
- ATS scoring
- missing-keyword recommendation flow
- SQLite resume persistence
- PDF export
- saved resume loading

## Planned future improvements

- provider-backed LLM integration with API key support
- stronger structured output for project and experience rewrite
- role-specific prompt templates
- PDF styling for professional templates
- resume upload parsing from PDF, Word (.docx), and TXT
- optional RAG-based ATS guidance

## Guardrails

This project intentionally follows a strict rule:

> AI-generated content can improve wording and structure, but it cannot invent qualifications, certifications, achievements, companies, or skills.

Every recommendation is validated against the user’s documented data before being accepted.

## Viva-ready explanation

The project demonstrates a practical GenAI system for resume optimization:

- it uses LLM generation for summary and bullet drafting
- it uses structured data to keep the resume consistent and explainable
- it applies keyword and semantic matching for job relevance
- it uses ATS checks and validation guardrails to reduce hallucination
- it provides a simple but realistic product workflow from resume authoring to export

This makes it a strong demonstration of GenAI design, product thinking, and engineering discipline without becoming over-engineered.
