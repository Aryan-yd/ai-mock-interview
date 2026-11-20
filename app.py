import os
import json
import pandas as pd
import plotly.express as px
import streamlit as st

from database import init_db, get_user_interviews, get_interview
from login import auth_page
from interview import setup_interview_page, interactive_interview_page
from resume_viewer import render_resume_insights
from pdf_reader import extract_text_from_pdf
from gemini import (
    analyze_resume,
    set_gemini_api_key,
    get_gemini_status,
    set_interview_mode,
    is_live_mode,
    test_gemini_connection
)


st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

init_db()


CSS = """
<style>
.stApp {
    background: radial-gradient(circle at top left, #312e81 0%, #0f172a 35%, #020617 100%);
    color: white;
}

.block-container {
    padding-top: 2rem;
    max-width: 1250px;
}

#MainMenu, header, footer {
    visibility: hidden;
}

.main-title {
    font-size: 44px;
    font-weight: 900;
    color: white;
}

.sub-title {
    color: #cbd5e1;
    font-size: 18px;
}

.card {
    background: rgba(15, 23, 42, 0.85);
    padding: 25px;
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 18px 45px rgba(0,0,0,0.35);
}

.hero {
    background: linear-gradient(135deg, rgba(124,58,237,.55), rgba(6,182,212,.25));
    padding: 35px;
    border-radius: 28px;
    border: 1px solid rgba(255,255,255,0.14);
    margin-top: 20px;
    margin-bottom: 25px;
}

.stButton > button {
    border-radius: 16px;
    border: none;
    font-weight: 800;
    color: white;
    background: linear-gradient(90deg, #7c3aed, #06b6d4);
    padding: 0.75rem 1.5rem;
}

[data-testid="stMetricValue"] {
    color: white;
}

[data-testid="stMetricLabel"] {
    color: #c4b5fd;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "user" not in st.session_state:
    auth_page()
    st.stop()


# ---------- SIDEBAR: AI ENGINE & MODE SETTINGS ----------
with st.sidebar:
    st.markdown("### ⚙️ Engine & Mode")
    ai_status = get_gemini_status()

    mode_options = ["🟢 Gemini Live Mode", "⚡ Demo Mode (Offline)"]
    current_idx = 0 if ai_status["is_live"] else 1
    selected_option = st.radio(
        "Active Application Mode",
        mode_options,
        index=current_idx,
        key="app_mode_selector",
        help="Gemini Live Mode calls Google's API for dynamic questions & evaluations. Demo Mode works offline without an API key."
    )
    chosen_mode = "live" if "Live" in selected_option else "demo"
    if chosen_mode != ai_status["mode"]:
        set_interview_mode(chosen_mode)
        st.rerun()

    st.write("---")
    st.markdown("### 🔑 Gemini API Details")

    if ai_status["has_key"]:
        st.success(f"**Key Configured:** `{ai_status['masked_key']}`")
        st.caption(f"🤖 Model: `{ai_status['model']}`")

        if st.button("🧪 Test API Connection", key="btn_test_conn", width="stretch"):
            with st.spinner("Pinging Google Gemini API..."):
                ok, msg = test_gemini_connection()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        with st.expander("Update / Change API Key"):
            new_k = st.text_input("New Gemini API Key", type="password", key="sidebar_new_key")
            if st.button("Update Key", key="btn_update_key", width="stretch"):
                if new_k.strip():
                    set_gemini_api_key(new_k.strip())
                    st.success("API Key updated securely in .env!")
                    st.rerun()
    else:
        st.warning("🟡 **API Key:** Not Configured")
        st.caption("Running in Demo Mode. Enter a Google Gemini API key to activate Gemini Live AI.")
        new_k = st.text_input("Enter Gemini API Key", type="password", placeholder="AIzaSy... or AQ...", key="sidebar_key_in")
        if st.button("💾 Save & Activate Live Mode", key="btn_save_key", width="stretch"):
            if new_k.strip():
                set_gemini_api_key(new_k.strip())
                set_interview_mode("live")
                st.success("API Key saved! Gemini Live Mode activated.")
                st.rerun()
            else:
                st.warning("Please paste a valid key.")
        st.markdown("[👉 Get Free Gemini API Key](https://aistudio.google.com/app/apikey)")

    if ai_status.get("last_error"):
        st.caption(f"⚠️ Last status: {ai_status['last_error']}")


# ---------- HEADER ----------
user_display_name = st.session_state.user.get("name", "Candidate") if "user" in st.session_state and st.session_state.user else "Candidate"
ai_status = get_gemini_status()

if ai_status["is_live"]:
    mode_badge_html = f"""<span style="background: rgba(34, 197, 94, 0.2); border: 1px solid #22c55e; color: #86efac; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 700; margin-left: 12px;">🟢 Gemini Live Mode ({ai_status['model']})</span>"""
else:
    mode_badge_html = """<span style="background: rgba(245, 158, 11, 0.2); border: 1px solid #f59e0b; color: #fde68a; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 700; margin-left: 12px;">⚡ Demo Mode (Offline Simulation)</span>"""

st.markdown(
    f"""
    <div class="card">
        <div class="main-title">🤖 AI Interview Coach</div>
        <div class="sub-title">Practice smarter • Improve faster • Get hired</div>
        <br>
        <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 8px;">
            <b>👤 Logged in as {user_display_name}</b>
            {mode_badge_html}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

nav1, nav2, nav3, nav4, nav5, nav6 = st.columns(6)

with nav1:
    if st.button("🏠 Dashboard", width="stretch"):
        st.session_state.page = "Dashboard"
        st.rerun()

with nav2:
    if st.button("🎯 New Interview", width="stretch"):
        st.session_state.page = "New Interview"
        st.rerun()

with nav3:
    if st.button("🎙️ Mock Interview", width="stretch"):
        st.session_state.page = "Practice"
        st.rerun()

with nav4:
    if st.button("📄 Resume Insights", width="stretch"):
        st.session_state.page = "Resume Insights"
        st.rerun()

with nav5:
    if st.button("📚 History", width="stretch"):
        st.session_state.page = "History"
        st.rerun()

with nav6:
    if st.button("🚪 Logout", width="stretch"):
        st.session_state.clear()
        st.rerun()


# ---------- DASHBOARD ----------
if st.session_state.page == "Dashboard":
    user_id = st.session_state.user["id"]
    rows = get_user_interviews(user_id)

    st.markdown(
        """
        <div class="hero">
            <h1>Welcome Back 👋</h1>
            <p style="font-size:18px;color:#e0e7ff;">
                Upload your resume, add a job description, practice dynamic adaptive interviews with voice input & live webcam face view,
                and get AI-powered evaluation reports.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    total = len(rows)
    avg = round(sum(r[2] or 0 for r in rows) / total, 2) if total else 0
    best = max([r[2] or 0 for r in rows], default=0)
    progress = round((avg / 10) * 100) if avg else 0

    c1.metric("🎯 Total Interviews", total)
    c2.metric("⭐ Average Score", f"{avg}/10")
    c3.metric("🏆 Best Score", f"{best}/10")
    c4.metric("🚀 Readiness", f"{progress}%")

    st.write("")

    b1, b2 = st.columns(2)

    with b1:
        if st.button("🎯 Start New Interview", width="stretch"):
            st.session_state.page = "New Interview"
            st.rerun()

    with b2:
        if st.button("📄 View Resume Insights", width="stretch"):
            st.session_state.page = "Resume Insights"
            st.rerun()

    st.write("")

    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Role", "Score", "Date", "Feedback"])
        df["Date"] = pd.to_datetime(df["Date"])

        col1, col2 = st.columns([1.3, 0.7])

        with col1:
            st.subheader("📈 Performance Over Time")
            fig = px.line(
                df.sort_values("Date"),
                x="Date",
                y="Score",
                markers=True,
                title="Interview Score Progress"
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white"
            )
            st.plotly_chart(fig, width="stretch")

        with col2:
            st.subheader("🎯 Score Distribution")
            fig2 = px.pie(
                df,
                names="Role",
                values="Score",
                hole=0.55,
                title="Scores by Role"
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white"
            )
            st.plotly_chart(fig2, width="stretch")

    else:
        st.info("No interviews yet. Start your first interview.")

    st.write("")
    st.subheader("⚡ Quick Actions")

    q1, q2, q3 = st.columns(3)

    with q1:
        st.markdown(
            """
            <div class="card">
                <h3>📄 Extracted Resume Insights</h3>
                <p>Inspect extracted skills, education, experience, and executive summaries.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        if st.button("Explore Resume Insights", key="qa_resume", width="stretch"):
            st.session_state.page = "Resume Insights"
            st.rerun()

    with q2:
        st.markdown(
            """
            <div class="card">
                <h3>🎙️ Spoken Mock Interview</h3>
                <p>Record your spoken answers with microphone input and live voice transcription.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        if st.button("Launch Mock Interview", key="qa_practice", width="stretch"):
            st.session_state.page = "Practice"
            st.rerun()

    with q3:
        st.markdown(
            """
            <div class="card">
                <h3>🎯 Dynamic Adaptive Q&A</h3>
                <p>Experience real-time follow-up questions tailored to your previous responses.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        if st.button("Configure Adaptive Session", key="qa_adaptive", width="stretch"):
            st.session_state.page = "New Interview"
            st.rerun()


# ---------- RESUME INSIGHTS PAGE ----------
elif st.session_state.page == "Resume Insights":
    st.header("📄 Resume Analyzer & Extracted Profile Insights")
    st.caption("Upload any resume PDF to inspect the AI-extracted skills, education, projects, and summary.")

    up_resume = st.file_uploader("Upload Resume PDF to Analyze", type=["pdf"], key="page_resume_pdf")

    if up_resume is not None:
        with st.spinner("Analyzing resume content..."):
            txt = extract_text_from_pdf(up_resume)
            info = analyze_resume(txt)
            st.session_state.cached_resume_info = info
            st.session_state.cached_resume_text = txt
            render_resume_insights(info, txt)
    elif "cached_resume_info" in st.session_state:
        st.info("Displaying the most recent resume uploaded in your active session:")
        render_resume_insights(
            st.session_state.cached_resume_info,
            st.session_state.get("cached_resume_text", "")
        )
    else:
        st.info("Please upload a resume PDF above to view extracted profile insights.")


# ---------- NEW INTERVIEW ----------
elif st.session_state.page == "New Interview":
    setup_interview_page()


# ---------- PRACTICE ----------
elif st.session_state.page == "Practice":
    interactive_interview_page()


# ---------- HISTORY ----------
elif st.session_state.page == "History":
    st.subheader("📚 Interview History")

    rows = get_user_interviews(st.session_state.user["id"])

    if not rows:
        st.info("No history found.")
    else:
        for row in rows:
            with st.expander(f"{row[1] or 'Interview'} | Score: {row[2]}/10 | {row[3]}"):
                item = get_interview(row[0], st.session_state.user["id"])

                if item:
                    st.write("### Final Feedback")
                    st.write(item["feedback"])

                    st.write("### Questions and Answers")

                    for i, q in enumerate(item["questions"]):
                        q_display = q.get('question','') if isinstance(q, dict) else str(q)
                        st.markdown(f"**Q{i+1}: {q_display}**")

                        if i < len(item["answers"]):
                            st.write("Answer:", item["answers"][i])
