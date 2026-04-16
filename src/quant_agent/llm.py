from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional dependency fallback
    genai = None


@dataclass
class LLMResponse:
    text: str
    used_model: str


class GeminiSummarizer:
    def __init__(self) -> None:
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.model_name = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
        self.enabled = bool(self.api_key and genai is not None)
        if self.enabled:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

    def summarize(self, prompt: str) -> LLMResponse:
        if not self.enabled or self.model is None:
            return LLMResponse(text="", used_model="unavailable")

        response = self.model.generate_content(prompt)
        text = getattr(response, "text", "")
        return LLMResponse(text=text.strip(), used_model=self.model_name)

    def summarize_bullets(self, title: str, bullets: Sequence[str]) -> LLMResponse:
        prompt = (
            f"You are a careful financial research assistant. Summarize the following evidence for {title}. "
            f"Return 3-5 concise bullet points focused on fundamentals, risk, catalysts, and data quality.\n\n"
            + "\n".join(f"- {bullet}" for bullet in bullets)
        )
        return self.summarize(prompt)
