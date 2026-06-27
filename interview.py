import streamlit as st
from gemini import analyze_resume, generate_questions, evaluate_answer, final_summary
from database import save_interview
from pdf_reader import extract_text_from_pdf
from feedback import show_feedback_card, show_final_feedback
from report_generator import generate_report


def setup_interview_page():
    st.header("🧠 Start New Interview")
    role = st.text_input("Target Role", placeholder="Example: AI/ML Engineer, Python Developer, Data Analyst")
    resume_pdf = st.file_uploader("Upload Resume PDF", type=["pdf"])
    jd_file = st.file_uploader("Upload Job Description PDF (optional)", type=["pdf"], key="jd_pdf")
    jd_text = st.text_area("Or paste Job Description", height=160)
    total_questions = st.slider("Number of Questions", min_value=3, max_value=15, value=8)

    if st.button("Generate Interview Questions", width="stretch"):
        if not role:
            st.warning("Please enter a target role.")
            return
        with st.spinner("Reading resume and generating questions..."):
            resume_text = extract_text_from_pdf(resume_pdf) if resume_pdf else ""
            jd_pdf_text = extract_text_from_pdf(jd_file) if jd_file else ""
            final_jd = jd_text or jd_pdf_text
            resume_info = analyze_resume(resume_text) if resume_text else {}
            questions = generate_questions(resume_text, final_jd, role, total_questions)
            st.session_state.interview_data = {
                "role": role, "resume_text": resume_text, "job_description": final_jd,
                "resume_info": resume_info, "questions": questions, "answers": [], "feedback": [], "index": 0
            }
            st.success("Questions generated. Go to Interactive Interview from the sidebar.")


def interactive_interview_page():
    st.header("🎙️ Interactive Interview")
    data = st.session_state.get("interview_data")
    if not data:
        st.info("Please generate questions first from Start New Interview.")
        return

    questions = data["questions"]
    idx = data.get("index", 0)
    st.progress(min(idx / max(len(questions), 1), 1.0))

    if idx >= len(questions):
        if "final_feedback" not in data:
            with st.spinner("Preparing final feedback..."):
                data["final_feedback"] = final_summary(data["feedback"])
                interview_id = save_interview(
                    st.session_state.user["id"], data["role"], data["resume_text"], data["job_description"],
                    data["questions"], data["answers"], data["final_feedback"], data["final_feedback"].get("overall_score", 0)
                )
                data["interview_id"] = interview_id
        show_final_feedback(data["final_feedback"])
        report_path = generate_report(
            st.session_state.user["name"], data["role"], data["questions"], data["answers"],
            data["feedback"], data["final_feedback"], data.get("interview_id")
        )
        with open(report_path, "rb") as f:
            st.download_button("📄 Download PDF Report", data=f, file_name=report_path.name, mime="application/pdf", width="stretch")
        if st.button("Start Another Interview", width="stretch"):
            st.session_state.pop("interview_data", None)
            st.rerun()
        return

    q = questions[idx]
    st.markdown(f"<div class='question-card'><b>Question {idx+1}/{len(questions)}</b><br><span>{q.get('type','General')}</span><h3>{q.get('question','')}</h3></div>", unsafe_allow_html=True)
    answer = st.text_area("Your Answer", height=180, key=f"answer_{idx}")

    if st.button("Submit Answer & Get Feedback", width="stretch"):
        if not answer.strip():
            st.warning("Please write your answer first.")
            return
        with st.spinner("Evaluating your answer..."):
            fb = evaluate_answer(q, answer, data["resume_text"], data["job_description"])
            data["answers"].append(answer)
            data["feedback"].append(fb)
            data["last_feedback"] = fb
            data["index"] = idx + 1
            st.rerun()

    if data.get("last_feedback") and idx > 0:
        show_feedback_card(data["last_feedback"])
