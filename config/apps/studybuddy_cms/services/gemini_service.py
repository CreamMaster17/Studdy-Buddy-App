import json
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

from ...studybuddy_quiz.quiz_generator import GEMINI_MODEL

def get_client():
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    return genai.Client(api_key=GEMINI_API_KEY)

MAIN_PROMPT = """
You are StudyBuddy, an expert AI study assistant helping students learn from their notes.

Your goal is to transform student-provided notes into useful study materials.

General Rules:
- Only use information provided in the student's notes.
- Do not invent facts, examples, or explanations that are not supported by the notes.
- Preserve important terminology, definitions, formulas, dates, names, and concepts.
- Make the material clear and easy for a student to review.
- Use concise, student-friendly language.
- Organize information logically.
- Prioritize understanding over simply shortening the notes.

The student will request one of three study tools:
1. Summary - create organized review notes.
2. Flashcards - create memorization questions and answers.
3. Quiz - create practice assessment questions.

Return ONLY valid JSON.
Do not use markdown code fences.
Do not include explanations outside of the JSON.
"""
def summarize_notes(text: str) -> dict:
    client = get_client()

    prompt = f"""{MAIN_PROMPT}


Create a structured study summary from the student's notes.

The summary should:
- Identify the main topics and concepts.
- Break large sections into smaller understandable sections.
- Include important definitions, formulas, dates, and vocabulary.
- Explain difficult concepts in simpler terms.
- Remove unnecessary repetition.
- Create a useful review sheet for studying.

Return JSON using exactly this format:


{{
    "title": "...",
    "topics": [
        {{
            "heading": "...",
            "points": [
                "..."
            ]
        }}
    ],
    "key_takeaways": [
        "..."
    ]
}}

- The topics array may contain multiple topic objects
- Each "points" array may contain multiple strings
- The "key_takeaways" array should contain 3-5 strings.

- Do not include any text before or after this format.

Student Notes:
{text}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError("Gemini returned invalid summary JSON.") from e


def generate_flashcards(text: str) -> dict:
    client = get_client()

    prompt = f"""{MAIN_PROMPT}


Create study flashcards from the student's notes.

The flashcards should:
- Cover the most important concepts.
- Focus on information that requires memorization.
- Test understanding rather than copying sentences.
- Use clear questions with concise answers.
- Include important definitions, processes, vocabulary, formulas, or facts.

Create 10 flashcards unless the notes do not contain enough information.

Return JSON using exactly this format:


{{
    "flashcards": [
        {{
            "question": "...",
            "answer": "..."
        }}

    ]
}}

- The flashcards array may contain multiple flashcard objects.
- Do not create duplicate flashcards.
- Do not include information that is not found in the notes.

-Do not include any text before or after this format.

Student Notes:
{text}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError("Gemini returned invalid summary JSON.") from e


def generate_quiz(text: str) -> dict:
    client = get_client()

    prompt = f"""{MAIN_PROMPT}
    
    
Create a practice quiz from the student's notes.

The quiz should:
- Test important concepts from the notes.
- Include a mixture of recall and understanding questions.
- Have exactly 5 multiple-choice questions.
- Include only one correct answer per question.

Return JSON using exactly this format:
    
    
{{
    "quiz": [
        {{
            "question": "...",
            "choices": [
                    "...",
                    "...",
                    "...",
                    "..."
                ],
            "answer": "..."
        }}
    ]
}}
    
- Each question must have exactly 4 answer choices.
- The correct answer must appear exactly in the choices list.
- Wrong choices should be believable but incorrect.
- Do not use trick questions.
- Do not include explanations.
- Do not add information not present in the notes.
    
-Do not include any text before or after this format.
    
Student Notes:
{text}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as error:
        raise ValueError("Gemini returned invalid quiz JSON.") from error
