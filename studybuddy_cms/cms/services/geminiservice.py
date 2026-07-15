import json
import os

from google import genai


def get_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    return genai.Client(api_key=api_key)


def summarize_notes(text: str) -> str:
    client = get_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Summarize the following notes:\n\n{text}",
    )

    return response.text


def generate_flashcards(text: str) -> str:
    client = get_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
Create 3 study flashcards from these notes.

Format:
Q: question
A: answer

Notes:
{text}
""",
    )

    return response.text


def generate_quiz(text: str) -> list[dict]:
    client = get_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
Create 5 multiple-choice quiz questions from these notes.

Return only valid JSON.
Do not use markdown code fences.
Do not include explanations.

Use this structure:

[
  {{
    "question": "...",
    "choices": ["...", "...", "...", "..."],
    "answer": "..."
  }}
]

Notes:
{text}
""",
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as error:
        raise ValueError("Gemini returned invalid quiz JSON.") from error