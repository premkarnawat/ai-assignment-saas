# backend/services/ai_service.py
import json
import logging
from typing import Optional

from core.config import settings

logger = logging.getLogger(__name__)

ASSIGNMENT_SYSTEM = """You are an expert academic tutor and assignment writer.
Generate structured assignment answers formatted for handwritten notebook rendering.

STRICT FORMATTING RULES:
- Max 70 characters per line (notebook width constraint)
- Use numbered lists (1. 2. 3.) for steps
- Use bullet points starting with "- " not dashes with spaces
- Write as a student — clear, academic, not robotic
- Include real examples with data/numbers where relevant
- No markdown headers, no **, no special chars except ( ) [ ] , . ? !
- Equations: write inline as text like "F = ma" or "E = mc^2"

OUTPUT: Respond ONLY with a valid JSON object, no preamble, no backticks."""

ASSIGNMENT_USER = """Question: {question}
Subject: {subject}
Grade Level: {grade_level}

Generate a complete assignment answer.

Return JSON:
{{
  "title": "Assignment title (max 60 chars)",
  "full_text": "Complete answer text with newlines for line breaks",
  "sections": [
    {{"type": "intro",       "heading": "Introduction",  "content": "..."}},
    {{"type": "explanation", "heading": "Explanation",   "content": "..."}},
    {{"type": "example",     "heading": "Example",       "content": "..."}},
    {{"type": "conclusion",  "heading": "Conclusion",    "content": "..."}}
  ],
  "has_diagram": false,
  "diagram_type": "none",
  "diagram_mermaid": "",
  "has_math": false,
  "equations": [],
  "word_count": 0
}}"""

NOTEBOOK_SYSTEM = """You are an expert academic content generator.
Create complete multi-page handwritten notebook content for students.
Content must be educational, well-structured, and sized for notebook pages.
Each page = approximately 200-250 words of content.
OUTPUT: Respond ONLY with valid JSON, no backticks, no preamble."""

NOTEBOOK_USER = """Subject: {subject}
Topic: {topic}
Pages: {pages}
Subtopics requested: {subtopics}
Include diagrams: {include_diagrams}
Include examples: {include_examples}

Generate a complete {pages}-page notebook covering {topic}.

Return JSON:
{{
  "subject": "{subject}",
  "topic": "{topic}",
  "total_pages": {pages},
  "pages": [
    {{
      "page_number": 1,
      "title": "Page title",
      "content": "Full page content with newlines",
      "has_diagram": false,
      "diagram_mermaid": "",
      "has_math": false,
      "equations": []
    }}
  ]
}}"""


async def _call_groq(system: str, user: str) -> str:
    from groq import AsyncGroq
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # ← updated model name
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.7,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def _call_openai(system: str, user: str) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.AI_MODEL_FALLBACK,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.7,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def _call_ai(system: str, user_prompt: str) -> dict:
    """Try Groq first, fall back to OpenAI if Groq fails."""
    raw = None
    try:
        if settings.GROQ_API_KEY:
            raw = await _call_groq(system, user_prompt)
        elif settings.OPENAI_API_KEY:
            raw = await _call_openai(system, user_prompt)
        else:
            raise ValueError("No AI API key configured. Add GROQ_API_KEY to Render env vars.")
    except Exception as groq_err:
        logger.warning(f"Groq failed: {groq_err}, falling back to OpenAI")
        if settings.OPENAI_API_KEY:
            raw = await _call_openai(system, user_prompt)
        else:
            raise groq_err

    return json.loads(raw)


async def generate_structured_answer(
    question:    str,
    subject:     str = "General",
    grade_level: str = "college",
) -> dict:
    user_prompt = ASSIGNMENT_USER.format(
        question=question,
        subject=subject,
        grade_level=grade_level,
    )
    result = await _call_ai(ASSIGNMENT_SYSTEM, user_prompt)

    # Ensure full_text is populated from sections if missing
    if not result.get("full_text") and result.get("sections"):
        parts = [result.get("title", "")]
        for section in result["sections"]:
            parts.append(f"\n{section['heading']}")
            parts.append(section["content"])
        result["full_text"] = "\n".join(parts)

    return result


async def generate_notebook_content(
    subject:          str,
    topic:            str,
    pages:            int,
    subtopics:        list,
    include_diagrams: bool = True,
    include_examples: bool = True,
) -> dict:
    user_prompt = NOTEBOOK_USER.format(
        subject          = subject,
        topic            = topic,
        pages            = pages,
        subtopics        = ", ".join(subtopics) if subtopics else "auto-generate",
        include_diagrams = include_diagrams,
        include_examples = include_examples,
    )
    return await _call_ai(NOTEBOOK_SYSTEM, user_prompt)
