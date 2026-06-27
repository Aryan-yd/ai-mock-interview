import json
import pandas as pd
import streamlit as st

from database import get_user_interviews, get_interview
from components.hero import hero_section
from components.cards import stat_card, quick_action_card, recent_interview_card, ai_tip
from components.charts import performance_chart, skill_chart, weekly_activity, progress_gauge


def dashboard_page():
    user = st.session_state.get("user", {})
    username = user.get("name", "Maham")
    user_id = user.get("id")

    hero_section(username)

    rows = get_user_interviews(user_id) if user_id else []

    total = len(rows)
    avg = round(sum(r[2] or 0 for r in rows) / total, 1) if total else 0
    best = max([r[2] or 0 for r in rows], default=0)
    success_rate = round((avg / 10) * 100) if avg else 0

    st.markdown("<div class='stats-grid'>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        stat_card("🎯", "Total Interviews", total, "+12% this week")

    with c2:
        stat_card("⭐", "Average Score", f"{avg}/10", "+0.8 improved")

    with c3:
        stat_card("🏆", "Best Score", f"{best}/10", "Excellent")

    with c4:
        stat_card("🚀", "Success Rate", f"{success_rate}%", "Keep growing")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='quick-grid'>", unsafe_allow_html=True)

    q1, q2, q3 = st.columns(3)

    with q1:
        quick_action_card(
            "📄",
            "Resume Analyzer",
            "Upload your resume and let AI extract skills, education, projects and strengths."
        )

    with q2:
        quick_action_card(
            "💼",
            "Job Match",
            "Paste a job description and find your match score with missing skills."
        )

    with q3:
        quick_action_card(
            "🤖",
            "AI Interview",
            "Practice one question at a time and get detailed Gemini-powered feedback."
        )

    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1.4, 0.8])

    with left:
        st.markdown(
            """
            <div class="glass-card">
                <div class="card-title">Performance Analytics</div>
                <div class="card-subtitle">Track your interview score improvement over time.</div>
            """,
            unsafe_allow_html=True
        )

        if rows:
            df = pd.DataFrame(rows, columns=["ID", "Role", "Score", "Date", "Feedback"])
            df["Date"] = pd.to_datetime(df["Date"])
            fig = performance_chart(df.sort_values("Date"))
            st.plotly_chart(fig, width="stretch")
        else:
            sample_df = pd.DataFrame({
                "Date": pd.date_range("2026-01-01", periods=7),
                "Score": [5.5, 6.2, 6.8, 7.4, 7.8, 8.5, 9.0]
            })
            st.plotly_chart(performance_chart(sample_df), width="stretch")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(
            """
            <div class="glass-card">
                <div class="card-title">Skill Breakdown</div>
                <div class="card-subtitle">Your interview readiness by category.</div>
            """,
            unsafe_allow_html=True
        )

        st.plotly_chart(skill_chart(), width="stretch")

        st.markdown("</div>", unsafe_allow_html=True)

    left2, right2 = st.columns([0.9, 1.1])

    with left2:
        st.markdown(
            """
            <div class="glass-card">
                <div class="card-title">Readiness Score</div>
                <div class="card-subtitle">AI estimate based on your practice history.</div>
            """,
            unsafe_allow_html=True
        )

        readiness = success_rate if success_rate else 86
        st.plotly_chart(progress_gauge(readiness), width="stretch")

        st.markdown("</div>", unsafe_allow_html=True)

    with right2:
        st.markdown(
            """
            <div class="glass-card">
                <div class="card-title">Weekly Practice Activity</div>
                <div class="card-subtitle">Stay consistent to improve faster.</div>
            """,
            unsafe_allow_html=True
        )

        st.plotly_chart(weekly_activity(), width="stretch")

        st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.markdown(
            """
            <div class="glass-card">
                <div class="card-title">Recent Interviews</div>
                <div class="card-subtitle">Your latest interview practice sessions.</div>
            """,
            unsafe_allow_html=True
        )

        if rows:
            for row in rows[:5]:
                role = row[1] or "AI Interview"
                score = row[2] or 0
                date = row[3]
                recent_interview_card(role, date, score)
        else:
            recent_interview_card("Huawei AI Engineer", "Demo Session", 9.2)
            recent_interview_card("Google Software Engineer", "Demo Session", 8.8)
            recent_interview_card("Amazon ML Intern", "Demo Session", 8.4)

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            """
            <div class="glass-card">
                <div class="card-title">AI Recommendations</div>
                <div class="card-subtitle">Personalized improvement roadmap.</div>
            """,
            unsafe_allow_html=True
        )

        recommendations = [
            "Practice explaining your projects using STAR method.",
            "Improve technical depth in Python, ML and system design.",
            "Add more confidence examples in HR answers.",
            "Prepare company-specific answers for Huawei and AI roles."
        ]

        if rows:
            areas = []
            for row in rows:
                try:
                    fb = json.loads(row[4] or "{}")
                    areas.extend(fb.get("areas_to_improve", []))
                except Exception:
                    pass

            if areas:
                recommendations = [f"Focus more on {area}." for area in list(set(areas))[:4]]

        for tip in recommendations:
            ai_tip(tip)

        st.markdown("</div>", unsafe_allow_html=True)