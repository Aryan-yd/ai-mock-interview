import os
import streamlit as st
from streamlit_mic_recorder import speech_to_text
from gemini import (
    analyze_resume,
    generate_questions,
    evaluate_answer,
    final_summary,
    generate_adaptive_question,
    set_gemini_api_key,
    get_gemini_status,
    is_live_mode
)
from database import save_interview
from pdf_reader import extract_text_from_pdf
from feedback import show_feedback_card, show_final_feedback
from report_generator import generate_report
from resume_viewer import render_resume_insights
from audio_handler import transcribe_audio


def setup_interview_page():
    st.header("🧠 Start New Interview")
    st.caption("Configure your target role, resume, and interview mode.")

    ai_status = get_gemini_status()
    if ai_status["is_live"]:
        st.info(f"🟢 **Session Engine: Google Gemini Live AI** (`{ai_status['model']}`) — Real-time dynamic questioning, adaptive branching, and AI rubric evaluation.")
    else:
        st.warning("⚡ **Session Engine: Demo Mode (Offline Simulation)** — Using curated question banks & heuristic evaluation. No API key needed.")

    current_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not current_key:
        with st.expander("🔑 Add Google Gemini API Key (Recommended for Live AI)", expanded=False):
            st.markdown(
                "You can get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey). "
                "*(If left empty, the coach runs with local heuristic evaluation).* "
            )
            c_k1, c_k2 = st.columns([3, 1])
            with c_k1:
                key_in = st.text_input("Gemini API Key", type="password", placeholder="Paste AIzaSy... or AQ... here", key="setup_key_input")
            with c_k2:
                st.write("")
                st.write("")
                if st.button("💾 Save Key", key="btn_save_setup_key", width="stretch"):
                    if key_in.strip():
                        set_gemini_api_key(key_in.strip())
                        st.success("API Key saved! Google Gemini AI is now connected.")
                        st.rerun()
                    else:
                        st.warning("Please paste a valid key.")

    role = st.text_input("Target Job Role", placeholder="Example: AI/ML Engineer, Python Developer, Data Analyst")

    col_res, col_jd = st.columns(2)
    with col_res:
        resume_pdf = st.file_uploader("Upload Resume PDF", type=["pdf"])
    with col_jd:
        jd_file = st.file_uploader("Upload Job Description PDF (optional)", type=["pdf"], key="jd_pdf")

    jd_text = st.text_area("Or paste Job Description (optional)", height=120)

    # Configuration options
    col_opt1, col_opt2, col_opt3 = st.columns(3)
    with col_opt1:
        total_questions = st.slider("Total Number of Questions", min_value=3, max_value=15, value=6)
    with col_opt2:
        adaptive_mode = st.toggle(
            "🎯 Dynamic Adaptive Follow-up Mode",
            value=True,
            help="When enabled, the AI evaluates each response and dynamically generates challenging follow-up questions tailored to your actual answers!"
        )
    with col_opt3:
        camera_mode = st.toggle(
            "🎥 Live Camera / Face-Visible Mode",
            value=True,
            help="Simulate a real-life video interview! Shows your live camera feed alongside questions for posture and presence monitoring."
        )

    # Live Resume Insights Preview if resume is uploaded
    if resume_pdf is not None:
        with st.spinner("Extracting & analyzing resume profile..."):
            resume_text = extract_text_from_pdf(resume_pdf)
            if "cached_resume_name" not in st.session_state or st.session_state.cached_resume_name != resume_pdf.name:
                st.session_state.cached_resume_info = analyze_resume(resume_text)
                st.session_state.cached_resume_name = resume_pdf.name
                st.session_state.cached_resume_text = resume_text

        with st.expander("📄 View Extracted Resume Profile & Insights (AI Parser)", expanded=True):
            render_resume_insights(
                st.session_state.get("cached_resume_info", {}),
                st.session_state.get("cached_resume_text", "")
            )

    st.write("")

    if st.button("🚀 Begin Interview Session", width="stretch"):
        if not role:
            st.warning("Please enter a target job role.")
            return

        with st.spinner("Initializing interview session..."):
            resume_text = extract_text_from_pdf(resume_pdf) if resume_pdf else ""
            jd_pdf_text = extract_text_from_pdf(jd_file) if jd_file else ""
            final_jd = jd_text or jd_pdf_text

            resume_info = st.session_state.get("cached_resume_info") or (analyze_resume(resume_text) if resume_text else {})

            if adaptive_mode:
                # In adaptive mode: start with an opening question batch of 1-2 questions, then dynamically branch!
                opening_questions = generate_questions(resume_text, final_jd, role, total_questions=2)
                initial_questions = opening_questions[:1] if opening_questions else [
                    {
                        "type": "HR / Opening",
                        "question": f"Welcome! Could you introduce yourself and explain what makes you a strong fit for the {role} position?",
                        "ideal_points": ["Clear introduction", "Relevant technical skills", "Alignment with role"]
                    }
                ]
            else:
                initial_questions = generate_questions(resume_text, final_jd, role, total_questions=total_questions)

            st.session_state.interview_data = {
                "role": role,
                "resume_text": resume_text,
                "job_description": final_jd,
                "resume_info": resume_info,
                "questions": initial_questions,
                "answers": [],
                "feedback": [],
                "index": 0,
                "target_total": total_questions,
                "adaptive_mode": adaptive_mode,
                "enable_camera": camera_mode,
                "candidate_photos": {},
                "mode": ai_status["mode"]
            }

            st.session_state.page = "Practice"
            st.success("Session ready! Redirecting to Interactive Interview...")
            st.rerun()


def interactive_interview_page():
    data = st.session_state.get("interview_data")

    if not data:
        st.header("🎙️ Interactive Mock Interview")
        st.info("No active interview in progress. Please start an interview from 'Start New Interview'.")
        return

    col_h1, col_h2 = st.columns([1.6, 0.9])
    with col_h1:
        st.header("🎙️ Interactive Mock Interview")
    with col_h2:
        enable_camera = st.toggle(
            "🎥 Camera / Face-Visible Mode",
            value=data.get("enable_camera", True),
            key="active_interview_cam_toggle",
            help="Toggle live webcam face monitor on/off anytime during your interview."
        )
        data["enable_camera"] = enable_camera

    questions = data["questions"]
    idx = data.get("index", 0)
    target_total = data.get("target_total", len(questions))

    # Progress Bar
    progress_val = min(float(idx) / max(float(target_total), 1.0), 1.0)
    st.progress(progress_val)
    st.caption(f"Progress: Question {idx + 1 if idx < target_total else target_total} of {target_total}")

    # Expandable Resume Insights for reference
    with st.expander("📄 View Extracted Resume Profile & Insights", expanded=False):
        render_resume_insights(data.get("resume_info", {}), data.get("resume_text", ""))

    # Interview Finished state
    if idx >= target_total or (idx >= len(questions) and not data.get("adaptive_mode", False)):
        if "final_feedback" not in data:
            with st.spinner("Analyzing overall performance and generating final report..."):
                data["final_feedback"] = final_summary(data["feedback"])
                interview_id = save_interview(
                    st.session_state.user["id"],
                    data["role"],
                    data["resume_text"],
                    data["job_description"],
                    data["questions"],
                    data["answers"],
                    data["final_feedback"],
                    data["final_feedback"].get("overall_score", 0)
                )
                data["interview_id"] = interview_id

        show_final_feedback(data["final_feedback"])

        if data.get("candidate_photos"):
            st.write("---")
            st.subheader("📸 Candidate Video Interview Highlights")
            photos = data["candidate_photos"]
            cols = st.columns(min(len(photos), 4))
            for i, (q_idx, p_data) in enumerate(photos.items()):
                with cols[i % len(cols)]:
                    st.image(p_data, caption=f"Snapshot from Q{int(q_idx) + 1}", use_container_width=True)

        report_path = generate_report(
            st.session_state.user["name"],
            data["role"],
            data["questions"],
            data["answers"],
            data["feedback"],
            data["final_feedback"],
            data.get("interview_id")
        )

        with open(report_path, "rb") as f:
            st.download_button(
                "📄 Download Professional PDF Report",
                data=f,
                file_name=report_path.name,
                mime="application/pdf",
                width="stretch"
            )

        if st.button("🔄 Start Another Interview", width="stretch"):
            st.session_state.pop("interview_data", None)
            st.session_state.page = "New Interview"
            st.rerun()
        return

    # Current Question
    q = questions[idx]
    q_type = q.get("type", "General")
    q_text = q.get("question", "")
    adaptive_reason = q.get("adaptive_reason", "")

    # Layout: Split into main interview column and camera column if enabled
    if data.get("enable_camera", True):
        col_main, col_video = st.columns([1.25, 0.75])
    else:
        col_main = st.container()
        col_video = None

    with col_main:
        sess_mode = data.get("mode", get_gemini_status()["mode"])
        if sess_mode == "live":
            mode_pill = '<span style="background: rgba(34, 197, 94, 0.18); border: 1px solid #22c55e; color: #86efac; padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 700; margin-left: 10px;">🟢 Live AI</span>'
        else:
            mode_pill = '<span style="background: rgba(245, 158, 11, 0.18); border: 1px solid #f59e0b; color: #fde68a; padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 700; margin-left: 10px;">⚡ Demo</span>'

        # Display Question Card with badge
        card_html = f"""
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.3);
                    border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div>
                    <span style="font-weight: 700; color: #38bdf8; font-size: 16px;">Question {idx + 1} of {target_total}</span>
                    {mode_pill}
                </div>
                <span style="background: rgba(99, 102, 241, 0.2); border: 1px solid #818cf8; color: #c7d2fe;
                             padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 600;">{q_type}</span>
            </div>
            <h3 style="color: white; margin-top: 5px; line-height: 1.4;">{q_text}</h3>
        """
        if adaptive_reason:
            card_html += f"""
            <div style="margin-top: 12px; padding: 10px 14px; background: rgba(14, 165, 233, 0.12);
                        border-left: 3px solid #0ea5e9; border-radius: 6px; font-size: 13px; color: #bae6fd;">
                🎯 <b>Adaptive Follow-up:</b> {adaptive_reason}
            </div>
            """
        card_html += "</div>"
        st.markdown(card_html, unsafe_allow_html=True)

        # Key for the candidate answer in session state
        ans_key = f"answer_text_{idx}"
        if ans_key not in st.session_state:
            st.session_state[ans_key] = ""

        # ---------- VOICE / MICROPHONE INPUT SECTION ----------
        st.markdown("#### 🎙️ Spoken Response (Microphone Input)")
        st.caption("🗣️ **Instant Voice Input:** Click the microphone button below, speak your answer clearly, then click Stop. Your spoken response will automatically be typed into the answer box below!")

        c_stt, c_info = st.columns([1.3, 0.7])
        with c_stt:
            spoken_text = speech_to_text(
                language="en",
                start_prompt="🎙️ Click to Speak (Live Speech-to-Text)",
                stop_prompt="🛑 Stop & Insert into Answer",
                just_once=True,
                use_container_width=True,
                key=f"stt_widget_{idx}"
            )
        with c_info:
            if spoken_text:
                st.success("Transcribing speech...")

        if spoken_text:
            existing = st.session_state.get(ans_key, "").strip()
            if existing:
                st.session_state[ans_key] = f"{existing} {spoken_text}"
            else:
                st.session_state[ans_key] = spoken_text
            st.session_state[f"last_trans_{idx}"] = spoken_text
            st.rerun()

        # Expandable alternative audio recorder
        with st.expander("🎵 Audio File Recorder & Player (Alternative Option)", expanded=False):
            st.caption("Record full audio clips or replay your recording:")
            audio_clip = st.audio_input("Record audio clip", key=f"mic_{idx}")
            if audio_clip is not None:
                if st.button("📝 Transcribe Recorded Clip", key=f"retrans_{idx}", width="stretch"):
                    with st.spinner("Transcribing audio clip..."):
                        speech_text = transcribe_audio(audio_clip)
                        if speech_text and not speech_text.startswith("["):
                            existing = st.session_state.get(ans_key, "").strip()
                            if existing:
                                st.session_state[ans_key] = f"{existing} {speech_text}"
                            else:
                                st.session_state[ans_key] = speech_text
                            st.session_state[f"last_trans_{idx}"] = speech_text
                            st.rerun()
                        elif speech_text.startswith("["):
                            st.error(speech_text)
                        else:
                            st.warning("⚠️ No speech recognized in recording.")

        if f"last_trans_{idx}" in st.session_state:
            st.success(f"✅ Last Transcribed Speech: \"{st.session_state[f'last_trans_{idx}']}\" (typed into box below)")

        st.markdown("#### ✍️ Candidate Answer")
        answer = st.text_area(
            "Type or edit your response (voice transcription auto-populates here):",
            key=ans_key,
            height=160,
            placeholder="Click '🎙️ Click to Speak' above or type your detailed response here..."
        )

        col_sub, col_skip = st.columns([1.5, 0.5])
        with col_sub:
            submit_btn = st.button("📤 Submit Answer & Get Real-Time Feedback", width="stretch")
        with col_skip:
            skip_btn = st.button("⏩ Skip Question", width="stretch")

    if col_video is not None:
        with col_video:
            st.markdown(
                """
                <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.35);
                            border-radius: 16px; padding: 14px; margin-bottom: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; color: #38bdf8; font-size: 15px;">🎥 Candidate Live Feed</span>
                        <span style="background: rgba(34, 197, 94, 0.2); border: 1px solid #22c55e; color: #86efac;
                                     padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 700;">
                            🟢 LIVE
                        </span>
                    </div>
                    <p style="font-size: 12px; color: #94a3b8; margin: 0;">
                        Look straight into the camera to simulate real video interview eye contact.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            cam_shot = st.camera_input(
                "Candidate Live Webcam Monitor",
                key=f"cam_feed_{idx}",
                label_visibility="collapsed"
            )
            if cam_shot is not None:
                data.setdefault("candidate_photos", {})[idx] = cam_shot.getvalue()
                st.caption("📸 Snapshot recorded for session summary!")

            st.markdown(
                """
                <div style="background: rgba(30, 41, 59, 0.65); border: 1px solid rgba(148, 163, 184, 0.2);
                            border-radius: 14px; padding: 14px; margin-top: 12px; font-size: 12px; color: #cbd5e1;">
                    <div style="font-weight: 700; color: #f8fafc; margin-bottom: 8px; font-size: 13px;">
                        🎯 Video Interview Presence Tips:
                    </div>
                    <div style="margin-bottom: 5px;">👁️ <b>Eye Contact:</b> Keep eyes aligned with camera</div>
                    <div style="margin-bottom: 5px;">💡 <b>Lighting:</b> Face well-lit from front</div>
                    <div style="margin-bottom: 5px;">👔 <b>Posture:</b> Sit upright, shoulders balanced</div>
                    <div>🗣️ <b>Clarity:</b> Articulate clearly at a steady pace</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    if submit_btn:
        if not answer.strip():
            st.warning("Please type or record an answer before submitting.")
            return

        with st.spinner("AI Interviewer is evaluating your answer..."):
            fb = evaluate_answer(q, answer, data["resume_text"], data["job_description"])
            data["answers"].append(answer)
            data["feedback"].append(fb)
            data["last_feedback"] = fb

            # Adaptive follow-up question generation for next step
            if data.get("adaptive_mode", False) and (idx + 1 < target_total):
                with st.spinner("AI is formulating the next adaptive follow-up question based on your response..."):
                    next_q = generate_adaptive_question(
                        data["role"],
                        data["resume_text"],
                        data["job_description"],
                        q,
                        answer,
                        fb,
                        idx + 1,
                        target_total
                    )
                    data["questions"].append(next_q)

            data["index"] = idx + 1
            st.rerun()

    elif skip_btn:
        fb = {
            "score": 0, "correctness": 0, "confidence": 0, "completeness": 0, "communication": 0, "technical_depth": 0,
            "strengths": ["Skipped question."],
            "weaknesses": ["No answer provided."],
            "improved_answer": "Review the core concepts for this question.",
            "tips": ["Try to attempt every question, even with partial knowledge."]
        }
        data["answers"].append("[Skipped]")
        data["feedback"].append(fb)
        data["last_feedback"] = fb

        if data.get("adaptive_mode", False) and (idx + 1 < target_total):
            next_q = generate_adaptive_question(
                data["role"], data["resume_text"], data["job_description"], q, "[Skipped]", fb, idx + 1, target_total
            )
            data["questions"].append(next_q)

        data["index"] = idx + 1
        st.rerun()

    # Show previous question's feedback
    if data.get("last_feedback") and idx > 0:
        st.write("---")
        st.subheader(f"📊 Feedback for Previous Question (Question {idx})")
        show_feedback_card(data["last_feedback"])
