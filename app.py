import json
import pandas as pd
import plotly.express as px
import streamlit as st

from database import init_db, get_user_interviews, get_interview
from login import auth_page
from interview import setup_interview_page, interactive_interview_page


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


# ---------- HEADER ----------
st.markdown(
    f"""
    <div class="card">
        <div class="main-title">🤖 AI Interview Coach</div>
        <div class="sub-title">Practice smarter • Improve faster • Get hired</div>
        <br>
        <b>👤 Logged in as {st.session_state.user.get("name", "Maham")}</b>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

nav1, nav2, nav3, nav4, nav5 = st.columns(5)

with nav1:
    if st.button("🏠 Dashboard", width="stretch"):
        st.session_state.page = "Dashboard"
        st.rerun()

with nav2:
    if st.button("🎯 New Interview", width="stretch"):
        st.session_state.page = "New Interview"
        st.rerun()

with nav3:
    if st.button("💬 Interactive Interview", width="stretch"):
        st.session_state.page = "Practice"
        st.rerun()

with nav4:
    if st.button("📚 History", width="stretch"):
        st.session_state.page = "History"
        st.rerun()

with nav5:
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
                Upload your resume, add a job description, practice interviews,
                and get AI-powered feedback.
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
        if st.button("📄 Upload Resume / JD", width="stretch"):
            st.session_state.page = "New Interview"
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
                <h3>📄 Resume Analyzer</h3>
                <p>Upload your resume and let AI extract your skills, education, and projects.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with q2:
        st.markdown(
            """
            <div class="card">
                <h3>💼 Job Description</h3>
                <p>Paste a job description and generate role-specific interview questions.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with q3:
        st.markdown(
            """
            <div class="card">
                <h3>🤖 AI Feedback</h3>
                <p>Get score, strengths, weaknesses, improved answer, and tips.</p>
            </div>
            """,
            unsafe_allow_html=True
        )


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
                        st.markdown(f"**Q{i+1}: {q.get('question','')}**")

                        if i < len(item["answers"]):
                            st.write("Answer:", item["answers"][i])