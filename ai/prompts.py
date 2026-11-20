from __future__ import annotations


SUMMARY_PROMPT = """
Write a professional summary based only on the resume data below.
Rules:
- Do not invent jobs, companies, achievements, or skills.
- Keep it concise and ATS-friendly.
- Use active professional language.

Resume data:
{resume_data}
"""

CRITIC_PROMPT = """
Review the generated resume content for accuracy, professionalism, and ATS readability.
Check the following:
- No invented experience or qualifications
- Skills match the user's actual data
- Clear action-oriented bullets
- No unsupported claims

Return a JSON object with:
{
  "is_valid": bool,
  "issues": [str],
  "suggestions": [str]
}

Generated content:
{content}
"""
