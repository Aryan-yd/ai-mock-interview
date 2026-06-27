import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

MODEL_NAME = "gemini-1.5-flash"


def configure_model():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_NAME)


def _extract_json(text: str):
    text = text.strip()

    match = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]

    return json.loads(text)


def safe_ai_json(prompt: str, fallback: dict) -> dict:
    model = configure_model()

    if model is None:
        fallback["error"] = "Gemini API key not found. Using local fallback scoring."
        return fallback

    try:
        response = model.generate_content(prompt)
        return _extract_json(response.text)

    except Exception as exc:
        fallback["error"] = str(exc)
        return fallback


def analyze_resume(resume_text: str) -> dict:
    prompt = f"""
You are an AI resume parser.

Extract structured information from this resume.

Return ONLY valid JSON with these keys:
skills, education, projects, experience, summary

Resume:
{resume_text[:12000]}
"""

    fallback = {
        "skills": [],
        "education": [],
        "projects": [],
        "experience": [],
        "summary": ""
    }

    return safe_ai_json(prompt, fallback)


def generate_questions(resume_text: str, job_description: str, role: str, total_questions: int = 10) -> list:
    prompt = f"""
You are an expert interview coach.

Generate {total_questions} interview questions for this role:
{role}

Use the resume and job description.

Include:
- HR questions
- Technical questions
- Behavioral questions
- Project-based questions
- Coding questions if applicable

Return ONLY valid JSON in this format:

{{
  "questions": [
    {{
      "type": "HR",
      "question": "question text",
      "ideal_points": ["point 1", "point 2"]
    }}
  ]
}}

Resume:
{resume_text[:10000]}

Job Description:
{job_description[:10000]}
"""

    fallback = {
        "questions": [
            {
                "type": "HR",
                "question": "Tell me about yourself and why you are suitable for this role.",
                "ideal_points": ["Clear introduction", "Relevant skills", "Role alignment"]
            },
            {
                "type": "Technical",
                "question": "Explain one technical concept from your resume in simple words.",
                "ideal_points": ["Accuracy", "Clarity", "Example"]
            },
            {
                "type": "Behavioral",
                "question": "Describe a time you solved a difficult problem.",
                "ideal_points": ["STAR method", "Impact", "Learning"]
            }
        ]
    }

    data = safe_ai_json(prompt, fallback)
    return data.get("questions", fallback["questions"])


def local_score_answer(answer: str) -> int:
    answer = answer.strip()
    word_count = len(answer.split())

    if word_count == 0:
        return 0
    elif word_count < 8:
        return 2
    elif word_count < 20:
        return 4
    elif word_count < 45:
        return 6
    elif word_count < 80:
        return 7
    elif word_count < 130:
        return 8
    else:
        return 9


def clamp_score(value, default=0):
    try:
        return max(0, min(10, float(value)))
    except Exception:
        return default


def evaluate_answer(question: dict, answer: str, resume_text: str, job_description: str) -> dict:
    answer = answer.strip()
    fallback_score = local_score_answer(answer)

    fallback = {
        "score": fallback_score,
        "correctness": fallback_score,
        "confidence": max(0, fallback_score - 1),
        "completeness": fallback_score,
        "communication": fallback_score,
        "technical_depth": max(0, fallback_score - 1),
        "strengths": [
            "You attempted the question.",
            "Your answer includes some relevant information."
        ],
        "weaknesses": [
            "Add more specific examples.",
            "Include measurable impact or project results.",
            "Structure your answer more clearly."
        ],
        "improved_answer": answer if answer else "A stronger answer should include context, action, tools used, and final result.",
        "tips": [
            "Use the STAR method: Situation, Task, Action, Result.",
            "Mention tools, technologies, and outcomes.",
            "Keep your answer clear, confident, and role-focused."
        ]
    }

    prompt = f"""
You are a strict but fair professional interviewer.

Evaluate the candidate's answer carefully.

Return ONLY valid JSON.
Do not use markdown.
Do not add explanation outside JSON.

JSON format:
{{
  "score": number from 0 to 10,
  "correctness": number from 0 to 10,
  "confidence": number from 0 to 10,
  "completeness": number from 0 to 10,
  "communication": number from 0 to 10,
  "technical_depth": number from 0 to 10,
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "improved_answer": "better interview answer",
  "tips": ["tip 1", "tip 2"]
}}

Scoring rules:
0-2 = empty, irrelevant, incorrect, or very poor answer.
3-4 = weak answer with very little detail.
5-6 = average answer with basic explanation.
7-8 = good answer with structure, relevance, and examples.
9-10 = excellent answer with depth, confidence, examples, and measurable impact.

Important:
- Do NOT give 6 by default.
- Do NOT be overly generous.
- Give different scores based on answer quality.
- If the answer is short, score it low.
- If the answer is detailed, relevant, and structured, score it high.
- Penalize vague answers.
- Reward examples, tools, technologies, results, and clarity.

Question:
{json.dumps(question)}

Candidate Answer:
{answer}

Resume Context:
{resume_text[:4000]}

Job Description Context:
{job_description[:4000]}
"""

    result = safe_ai_json(prompt, fallback)

    result["score"] = clamp_score(result.get("score"), fallback_score)
    result["correctness"] = clamp_score(result.get("correctness"), fallback_score)
    result["confidence"] = clamp_score(result.get("confidence"), max(0, fallback_score - 1))
    result["completeness"] = clamp_score(result.get("completeness"), fallback_score)
    result["communication"] = clamp_score(result.get("communication"), fallback_score)
    result["technical_depth"] = clamp_score(result.get("technical_depth"), max(0, fallback_score - 1))

    for key in ["strengths", "weaknesses", "tips"]:
        if not isinstance(result.get(key), list):
            result[key] = fallback[key]

    if not result.get("improved_answer"):
        result["improved_answer"] = fallback["improved_answer"]

    return result


def final_summary(all_feedback: list) -> dict:
    scores = []

    for feedback in all_feedback:
        try:
            scores.append(float(feedback.get("score", 0)))
        except Exception:
            scores.append(0)

    avg = round(sum(scores) / max(len(scores), 1), 2)

    prompt = f"""
Create final interview feedback from this list.

Return ONLY valid JSON with these keys:
overall_score, strengths, weaknesses, areas_to_improve, final_tips

Average score is {avg}.

Feedback list:
{json.dumps(all_feedback)[:12000]}
"""

    fallback = {
        "overall_score": avg,
        "strengths": ["Completed the mock interview."],
        "weaknesses": ["Needs more structured and detailed answers."],
        "areas_to_improve": ["Technical depth", "Examples", "Confidence"],
        "final_tips": [
            "Practice concise but complete answers.",
            "Prepare 3 strong project stories.",
            "Use STAR method for behavioral questions."
        ]
    }

    result = safe_ai_json(prompt, fallback)
    result["overall_score"] = clamp_score(result.get("overall_score"), avg)

    return result