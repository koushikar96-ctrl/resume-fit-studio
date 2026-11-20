from __future__ import annotations

import json
import os
from typing import Any

import requests

from ai.generator import generate_summary_from_resume


class LLMClient:
    """Provider-independent LLM integration with a safe fallback."""

    def __init__(self, provider: str = "openrouter", api_key: str | None = None, model: str | None = None):
        self.provider = provider
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    def generate(self, prompt: str, schema: dict | None = None) -> dict[str, Any]:
        if not self.api_key:
            return {
                "status": "fallback",
                "provider": self.provider,
                "prompt": prompt,
                "schema": schema,
                "content": "No API key configured. Using local generation fallback.",
            }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if schema:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "AI Resume Builder",
        }

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {"status": "success", "provider": self.provider, "content": content}
        except Exception:
            return {
                "status": "fallback",
                "provider": self.provider,
                "content": "LLM request failed. Falling back to local generation.",
            }


def generate_resume_summary(resume: dict) -> str:
    base_summary = generate_summary_from_resume(resume)
    if not resume.get("personal", {}).get("name") and not resume.get("skills"):
        return base_summary

    llm_client = LLMClient()
    prompt = (
        "You are writing a concise ATS-friendly professional summary. "
        "Use only the facts in the resume below. Do not invent companies, "
        "certifications, job titles, tools, or achievements.\n\n"
        f"Resume data:\n{json.dumps(resume, ensure_ascii=False, indent=2)}\n\n"
        "Return only the final summary text, no markdown, no headers."
    )
    result = llm_client.generate(prompt)

    if result.get("status") == "success":
        content = str(result.get("content", "")).strip()
        invented_markers = ["docker", "aws", "kubernetes", "tensorflow", "gcp", "azure"]
        if content and not any(keyword in content.lower() for keyword in invented_markers):
            return content

    return base_summary
