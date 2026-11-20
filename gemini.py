import os
import json
import re
import urllib.request
import urllib.error
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
_LAST_API_ERROR = None
_LAST_MODEL_USED = None


def get_interview_mode() -> str:
    """Returns 'live' if configured and API key present, else 'demo'."""
    mode = os.getenv("INTERVIEW_MODE", "live").lower().strip()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if mode == "live" and api_key:
        return "live"
    return "demo"


def set_interview_mode(mode: str) -> None:
    """Updates interview mode in environment and persists to .env."""
    mode = "live" if str(mode).lower() == "live" else "demo"
    os.environ["INTERVIEW_MODE"] = mode
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("INTERVIEW_MODE="):
            new_lines.append(f"INTERVIEW_MODE={mode}\n")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"INTERVIEW_MODE={mode}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def is_live_mode() -> bool:
    """Checks if the application is currently running in live Gemini mode."""
    return get_interview_mode() == "live"


def set_gemini_api_key(new_key: str) -> bool:
    """Save API key in environment and persist into .env file securely."""
    new_key = new_key.strip()
    if not new_key:
        return False
    os.environ["GEMINI_API_KEY"] = new_key
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    key_found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("GEMINI_API_KEY="):
            new_lines.append(f"GEMINI_API_KEY={new_key}\n")
            key_found = True
        else:
            new_lines.append(line)
    if not key_found:
        new_lines.append(f"GEMINI_API_KEY={new_key}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return True


def get_gemini_status() -> dict:
    """Returns safe diagnostic information without exposing sensitive keys."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    masked = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else ("***" if key else "Not set")
    return {
        "mode": get_interview_mode(),
        "is_live": is_live_mode(),
        "has_key": bool(key),
        "masked_key": masked,
        "model": os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"),
        "last_error": _LAST_API_ERROR,
        "last_model_used": _LAST_MODEL_USED
    }


def call_gemini_api(prompt: str) -> str:
    """
    Direct HTTPS REST call to Google Gemini API (no grpc/cygrpc dependencies).
    Includes automatic multi-model fallback and granular HTTP error handling.
    """
    global _LAST_API_ERROR, _LAST_MODEL_USED
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        _LAST_API_ERROR = "No Gemini API key found. Using Demo Mode."
        return ""

    preferred_model = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()
    candidate_models = [
        preferred_model,
        "gemini-flash-lite-latest",
        "gemini-flash-latest",
        "gemini-2.5-flash-lite",
        "gemini-pro-latest"
    ]
    seen = set()
    models = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "InterviewOS/1.0"
    }

    last_error = None
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            req = urllib.request.Request(url, data=data_bytes, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as resp:
                result_json = json.loads(resp.read().decode("utf-8"))
                candidates = result_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        _LAST_MODEL_USED = model_name
                        _LAST_API_ERROR = None
                        return parts[0].get("text", "")
        except urllib.error.HTTPError as http_err:
            last_error = http_err
            code = http_err.code
            if code in (401, 403):
                _LAST_API_ERROR = "Invalid Gemini API Key or Unauthorized access (HTTP 401/403)."
                print(f"[Gemini REST API Auth Error] HTTP {code}: Please check your API key.")
                break
            elif code == 429:
                _LAST_API_ERROR = f"Gemini API rate limit or quota exceeded (HTTP 429) on model '{model_name}'."
                print(f"[Gemini REST API Quota] HTTP 429 on {model_name}. Attempting fallback...")
                continue
            elif code == 404:
                # Model unavailable or retired for this key tier
                continue
            else:
                _LAST_API_ERROR = f"Gemini API error (HTTP {code})."
        except urllib.error.URLError as url_err:
            last_error = url_err
            _LAST_API_ERROR = f"Network connection failure: {url_err.reason}"
            print(f"[Gemini REST API Network Error] {url_err.reason}")
            break
        except Exception as exc:
            last_error = exc
            _LAST_API_ERROR = f"Unexpected error: {str(exc)}"

    if _LAST_API_ERROR is None and last_error is not None:
        _LAST_API_ERROR = f"All models failed: {str(last_error)}"

    return ""


def test_gemini_connection() -> tuple:
    """Diagnostic check to test API connectivity. Returns (success: bool, message: str)."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return False, "No Gemini API key is configured. Running in Demo Mode."
    resp = call_gemini_api("Respond with only the single word: OK")
    if resp:
        model = _LAST_MODEL_USED or os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        return True, f"Gemini API Connected successfully via model '{model}'!"
    else:
        err = _LAST_API_ERROR or "Unable to connect to Google Gemini API."
        return False, err


def _extract_json(text: str):
    """Safely extracts and parses JSON object or array from LLM response string."""
    s = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s)
    if match:
        s = match.group(1).strip()
    else:
        start_obj = s.find("{")
        start_arr = s.find("[")
        if start_obj != -1 and (start_arr == -1 or start_obj < start_arr):
            end_obj = s.rfind("}")
            if end_obj != -1:
                s = s[start_obj:end_obj + 1]
        elif start_arr != -1:
            end_arr = s.rfind("]")
            if end_arr != -1:
                s = s[start_arr:end_arr + 1]

    # Clean trailing commas (common LLM JSON formatting artifact)
    s = re.sub(r",\s*([}\]])", r"\1", s)
    return json.loads(s)


def safe_ai_json(prompt: str, fallback: dict) -> dict:
    """Calls Gemini API and parses JSON; falls back cleanly if in demo mode or on API error."""
    if not is_live_mode():
        return fallback

    try:
        resp_text = call_gemini_api(prompt)
        if resp_text:
            return _extract_json(resp_text)
        else:
            return fallback
    except Exception as exc:
        print(f"[Gemini JSON Parse Fallback] {exc}")
        return fallback


# =====================================================================
# DEMO MODE QUESTION BANKS & PREDEFINED EVALUATION RUBRIC
# =====================================================================

DEMO_QUESTION_BANKS = {
    "software": [
        {
            "type": "HR / Opening",
            "question": "Could you walk us through your professional journey and highlight the most impactful technical project you've developed?",
            "ideal_points": ["Clear technical career arc", "Specific project context & architecture", "Measurable engineering outcome"]
        },
        {
            "type": "Technical / Architecture",
            "question": "How do you handle concurrency, state management, and race conditions in modern scalable backend applications?",
            "ideal_points": ["Locks / Mutexes / Semaphores", "Stateless service design & immutability", "Database isolation levels & optimistic locking"]
        },
        {
            "type": "System Design / Scalability",
            "question": "How would you design a distributed rate limiter or task queue handling millions of requests per second?",
            "ideal_points": ["Token bucket / Sliding window algorithms", "Redis caching & atomic Lua operations", "Backpressure handling & worker auto-scaling"]
        },
        {
            "type": "Behavioral (STAR Method)",
            "question": "Tell me about a time a critical production bug or outage occurred under your watch. How did you diagnose, resolve, and prevent it?",
            "ideal_points": ["Systematic debugging & logging analysis", "Rapid mitigation (rollback/hotfix)", "Blameless post-mortem and automated guardrails"]
        },
        {
            "type": "Engineering Practices",
            "question": "What is your approach to automated testing, CI/CD pipelines, and maintaining high code quality across collaborative teams?",
            "ideal_points": ["Unit, integration, and contract test pyramids", "Automated linting & security scans in CI", "Constructive peer code review guidelines"]
        }
    ],
    "data_ai": [
        {
            "type": "HR / Opening",
            "question": "Could you introduce yourself and discuss how your background aligns with Data Science and Machine Learning Engineering?",
            "ideal_points": ["ML & statistical foundations", "Core frameworks (PyTorch, TensorFlow, Scikit-learn)", "Driving business value from data"]
        },
        {
            "type": "Technical / ML Modeling",
            "question": "How do you detect and mitigate data drift, concept drift, and model bias in production machine learning pipelines?",
            "ideal_points": ["Population Stability Index (PSI) & statistical tests", "Continuous monitoring & automated retraining", "Fairness metrics and data balancing"]
        },
        {
            "type": "GenAI & LLMs",
            "question": "Explain the architecture of a Retrieval-Augmented Generation (RAG) system and how you prevent hallucinations in generative responses.",
            "ideal_points": ["Chunking strategies & dense vector embeddings", "Vector databases & hybrid semantic search", "Grounding checks and prompt constraints"]
        },
        {
            "type": "Data Engineering",
            "question": "How do you design scalable ETL pipelines to process high-velocity streaming data while guaranteeing idempotency?",
            "ideal_points": ["Streaming engines (Kafka, Flink, Spark Streaming)", "Deduplication & checkpointing mechanisms", "Data lake partitioning & schema enforcement"]
        },
        {
            "type": "Behavioral / Problem Solving",
            "question": "Describe a scenario where a machine learning model performed well in training but underperformed in deployment. How did you troubleshoot it?",
            "ideal_points": ["Identifying train/test distribution skew", "Analyzing feature pipeline discrepancies", "Iterative calibration and stakeholder communication"]
        }
    ],
    "general": [
        {
            "type": "HR / Introduction",
            "question": "Tell me about yourself, your core professional strengths, and what motivates you to excel in this role.",
            "ideal_points": ["Concise professional summary", "Core key strengths", "Enthusiasm for the role and mission"]
        },
        {
            "type": "Behavioral (STAR Method)",
            "question": "Describe a situation where you had to manage conflicting priorities and tight deadlines. How did you prioritize your deliverables?",
            "ideal_points": ["Situation & Task context", "Structured prioritization (Eisenhower / Impact-Effort)", "Successful outcome and lessons learned"]
        },
        {
            "type": "Teamwork & Conflict Resolution",
            "question": "Can you describe a time you had a significant disagreement with a colleague or manager regarding a project direction? How did you resolve it?",
            "ideal_points": ["Active listening & emotional intelligence", "Data-driven argumentation", "Commitment to team consensus"]
        },
        {
            "type": "Adaptability",
            "question": "Tell me about a project where the goals or requirements changed completely midway through. How did you adapt your approach?",
            "ideal_points": ["Agility & calm mindset", "Re-scoping and proactive stakeholder alignment", "Successful on-time delivery"]
        },
        {
            "type": "Continuous Learning",
            "question": "How do you proactively develop your skills, and what is one new concept or tool you learned recently that made you more effective?",
            "ideal_points": ["Self-directed learning habit", "Practical application to current work", "Knowledge sharing with teammates"]
        }
    ]
}


def get_demo_questions(role: str, total_questions: int = 5) -> list:
    """Returns curated demo questions tailored to role category."""
    role_lower = (role or "").lower()
    if any(k in role_lower for k in ["data", "ai", "ml", "machine learning", "nlp", "vision", "deep learning"]):
        bank = DEMO_QUESTION_BANKS["data_ai"]
    elif any(k in role_lower for k in ["dev", "engineer", "software", "python", "backend", "frontend", "fullstack", "cloud"]):
        bank = DEMO_QUESTION_BANKS["software"]
    else:
        bank = DEMO_QUESTION_BANKS["general"]

    # Cycle or slice to reach requested count
    questions = []
    for i in range(total_questions):
        q = bank[i % len(bank)].copy()
        if i >= len(bank):
            q["question"] = f"{q['question']} (Follow-up drill {i // len(bank) + 1})"
        questions.append(q)
    return questions


def local_score_answer(answer: str) -> int:
    """Heuristic scoring based on length, structure, and depth."""
    answer = answer.strip()
    word_count = len(answer.split())
    if word_count == 0:
        return 0
    elif word_count < 10:
        return 3
    elif word_count < 25:
        return 5
    elif word_count < 55:
        return 7
    elif word_count < 95:
        return 8
    elif word_count < 150:
        return 9
    else:
        return 9


def clamp_score(value, default=0):
    try:
        return max(0, min(10, float(value)))
    except Exception:
        return default


def get_demo_evaluation(question: dict, answer: str) -> dict:
    """Provides a realistic, structured rubric evaluation in Demo Mode."""
    answer = answer.strip()
    score = local_score_answer(answer)
    words = len(answer.split())

    strengths = []
    weaknesses = []
    tips = []

    if words >= 40:
        strengths.append("Provided a well-explained response with substantial technical context.")
        strengths.append("Demonstrated clear familiarity with core domain principles.")
    elif words >= 15:
        strengths.append("Addressed the core question directly.")
        weaknesses.append("Elaborate further with concrete examples and quantifiable business impact.")
    else:
        weaknesses.append("Answer is too brief. Interviewers expect a comprehensive explanation.")
        weaknesses.append("Missing specific tools, architecture, and project context.")

    strengths.append("Maintained a professional, direct communication style.")
    tips.append("Structure answers using the STAR method: Situation, Task, Action, and Result.")
    tips.append("Mention specific metrics (e.g., latency reduction, team size, uptime improvements).")

    q_text = question.get("question", "the topic") if isinstance(question, dict) else str(question)
    improved_ans = f"In my previous role, I addressed {q_text.lower()} by first establishing clear architecture benchmarks, implementing resilient modular patterns, and validating outcomes through automated end-to-end testing, resulting in improved team velocity and system reliability."

    return {
        "score": score,
        "correctness": score,
        "confidence": max(0, score - 1) if score > 3 else score,
        "completeness": score,
        "communication": min(10, score + 1) if score >= 6 else score,
        "technical_depth": max(0, score - 1),
        "strengths": strengths,
        "weaknesses": weaknesses if weaknesses else ["Add further metrics and benchmark comparisons."],
        "improved_answer": improved_ans,
        "tips": tips
    }


def get_demo_adaptive_question(role: str, previous_question: dict, previous_answer: str, previous_feedback: dict, index: int, total: int) -> dict:
    """Generates realistic adaptive follow-ups in Demo Mode."""
    score = previous_feedback.get("score", 5) if isinstance(previous_feedback, dict) else 5
    if score >= 7:
        return {
            "type": "Technical (Adaptive Follow-up)",
            "question": f"Building on your strong response for {role}: what are the primary architectural bottlenecks, fault tolerance strategies, or trade-offs you would optimize under 10x traffic?",
            "ideal_points": ["Scalability & bottlenecks", "Graceful degradation", "High-concurrency trade-offs"],
            "adaptive_reason": f"High-depth technical drill-down triggered by your solid answer (Score: {score}/10)."
        }
    else:
        return {
            "type": "Practical & Clarifying (Adaptive Follow-up)",
            "question": f"Let's ground this in practical execution: could you describe a specific project or challenge where you applied this, the roadblock you encountered, and how you overcame it?",
            "ideal_points": ["Concrete project context", "Problem solving approach", "STAR structure"],
            "adaptive_reason": f"Clarifying follow-up to give you an opportunity to elaborate with real-world examples (Score: {score}/10)."
        }


# =====================================================================
# WORKFLOW FUNCTIONS (RESUME, QUESTIONS, ADAPTIVE, EVALUATION, SUMMARY)
# =====================================================================

def analyze_resume(resume_text: str) -> dict:
    """Parses resume text into structured JSON using Gemini API in Live Mode or heuristics in Demo Mode."""
    fallback = {
        "skills": [],
        "education": [],
        "projects": [],
        "experience": [],
        "summary": ""
    }

    if is_live_mode():
        prompt = f"""
You are an expert AI resume parser.
Extract structured information from this resume.
Return ONLY valid JSON with these keys: skills, education, projects, experience, summary.

Resume:
{resume_text[:12000]}
"""
        result = safe_ai_json(prompt, fallback)
    else:
        result = fallback.copy()

    # Apply heuristic fallback helpers if keys are empty
    try:
        from resume_viewer import extract_skills_heuristic, extract_education_heuristic
        if not result.get("skills"):
            result["skills"] = extract_skills_heuristic(resume_text)
        if not result.get("education"):
            result["education"] = extract_education_heuristic(resume_text)
        if not result.get("summary") and resume_text:
            first_lines = [l.strip() for l in resume_text.split("\n") if len(l.strip()) > 30]
            if first_lines:
                result["summary"] = first_lines[0]
    except Exception as exc:
        print(f"[Resume Parsing Warning] {exc}")

    return result


def generate_questions(resume_text: str, job_description: str, role: str, total_questions: int = 6) -> list:
    """Generates tailored interview questions via Gemini API or Demo bank."""
    if not is_live_mode():
        return get_demo_questions(role, total_questions)

    prompt = f"""
You are an expert technical and HR interview coach.
Generate {total_questions} tailored interview questions for this target role:
{role}

Incorporate the candidate's resume and job description:
- HR / Background opening
- Core Technical questions
- Behavioral / Scenario-based questions
- Architecture / Problem-solving questions

Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{
      "type": "Technical",
      "question": "question text here",
      "ideal_points": ["point 1", "point 2", "point 3"]
    }}
  ]
}}

Resume Context:
{resume_text[:8000]}

Job Description Context:
{job_description[:8000]}
"""
    fallback_questions = get_demo_questions(role, total_questions)
    data = safe_ai_json(prompt, {"questions": fallback_questions})
    questions = data.get("questions", fallback_questions)
    return questions if isinstance(questions, list) and questions else fallback_questions


def generate_adaptive_question(role: str, resume_text: str, job_description: str, previous_question: dict, previous_answer: str, previous_feedback: dict, question_index: int, total_questions: int) -> dict:
    """Generates dynamic branching follow-up questions tailored to previous performance."""
    if not is_live_mode():
        return get_demo_adaptive_question(role, previous_question, previous_answer, previous_feedback, question_index, total_questions)

    prev_q_text = previous_question.get("question", "") if isinstance(previous_question, dict) else str(previous_question)
    score = previous_feedback.get("score", 5) if isinstance(previous_feedback, dict) else 5

    prompt = f"""
You are an expert interviewer conducting an adaptive interview for the role of: {role}.

The candidate was previously asked (Question {question_index} of {total_questions}):
"{prev_q_text}"

The candidate responded:
"{previous_answer}"

Evaluation of previous response:
Score: {score}/10
Strengths: {previous_feedback.get('strengths', [])}
Weaknesses: {previous_feedback.get('weaknesses', [])}

Job Description Context:
{job_description[:3000]}

Resume Context:
{resume_text[:3000]}

Generate the NEXT adaptive follow-up interview question ({question_index + 1} of {total_questions}).
Rules:
1. If score >= 7, challenge with deeper technical drill-down, edge-cases, scalability, or architecture trade-offs.
2. If score < 7, ask a targeted clarifying question with practical real-world scenario to give them an opportunity to elaborate.
3. Return ONLY valid JSON:
{{
  "type": "Technical (Adaptive Follow-up)",
  "question": "The question text",
  "ideal_points": ["point 1", "point 2"],
  "adaptive_reason": "Why this was generated based on candidate's previous response"
}}
"""
    fallback_q = get_demo_adaptive_question(role, previous_question, previous_answer, previous_feedback, question_index, total_questions)
    return safe_ai_json(prompt, fallback_q)


def evaluate_answer(question: dict, answer: str, resume_text: str, job_description: str) -> dict:
    """Evaluates candidate response with multi-metric rubric using Gemini in Live Mode or Demo engine."""
    if not is_live_mode():
        return get_demo_evaluation(question, answer)

    demo_eval = get_demo_evaluation(question, answer)
    fallback_score = demo_eval["score"]

    prompt = f"""
You are a strict, fair, expert interviewer.
Evaluate the candidate's answer carefully.
Return ONLY valid JSON without markdown fences.

Required JSON format:
{{
  "score": number from 0 to 10,
  "correctness": number from 0 to 10,
  "confidence": number from 0 to 10,
  "completeness": number from 0 to 10,
  "communication": number from 0 to 10,
  "technical_depth": number from 0 to 10,
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "improved_answer": "stronger model interview answer",
  "tips": ["tip 1", "tip 2"]
}}

Scoring Guidelines:
0-2: Empty, irrelevant, or inaccurate.
3-4: Surface-level response with minimal substance.
5-6: Acceptable answer covering basic principles.
7-8: Strong, structured answer with solid examples.
9-10: Exceptional answer with deep architecture, metrics, and STAR structure.

Question:
{json.dumps(question)}

Candidate Answer:
{answer}

Resume Context:
{resume_text[:4000]}

Job Description Context:
{job_description[:4000]}
"""
    result = safe_ai_json(prompt, demo_eval)

    # Sanitize and clamp numeric metrics
    result["score"] = clamp_score(result.get("score"), fallback_score)
    result["correctness"] = clamp_score(result.get("correctness"), fallback_score)
    result["confidence"] = clamp_score(result.get("confidence"), max(0, fallback_score - 1))
    result["completeness"] = clamp_score(result.get("completeness"), fallback_score)
    result["communication"] = clamp_score(result.get("communication"), fallback_score)
    result["technical_depth"] = clamp_score(result.get("technical_depth"), max(0, fallback_score - 1))

    for key in ["strengths", "weaknesses", "tips"]:
        if not isinstance(result.get(key), list):
            result[key] = demo_eval[key]

    if not result.get("improved_answer"):
        result["improved_answer"] = demo_eval["improved_answer"]

    return result


def final_summary(all_feedback: list) -> dict:
    """Synthesizes overall interview performance into final feedback summary."""
    scores = []
    for feedback in all_feedback:
        try:
            scores.append(float(feedback.get("score", 0)))
        except Exception:
            scores.append(0)

    avg = round(sum(scores) / max(len(scores), 1), 2)

    fallback = {
        "overall_score": avg,
        "strengths": ["Completed the comprehensive mock interview.", "Demonstrated core domain communication."],
        "weaknesses": ["Deepen technical explanations with quantitative metrics.", "Structure complex scenarios using STAR method."],
        "areas_to_improve": ["Technical Depth", "Architecture Trade-offs", "Concrete Production Metrics"],
        "final_tips": [
            "Use STAR method (Situation, Task, Action, Result) consistently.",
            "Quantify business and engineering impact in every project answer.",
            "Review core scalability and concurrency patterns before the live interview."
        ]
    }

    if not is_live_mode():
        return fallback

    prompt = f"""
Synthesize overall mock interview performance into a final summary.
Average score: {avg}/10.

Return ONLY valid JSON with these keys:
overall_score, strengths, weaknesses, areas_to_improve, final_tips

Feedback details:
{json.dumps(all_feedback)[:12000]}
"""
    result = safe_ai_json(prompt, fallback)
    result["overall_score"] = clamp_score(result.get("overall_score"), avg)
    return result
