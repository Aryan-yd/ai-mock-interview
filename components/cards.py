import streamlit as st


def stat_card(icon, label, value, change="+0%"):
    html = f"""
    <div class="stat-card">
        <div class="stat-icon">{icon}</div>
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
        <div class="stat-change">{change}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def quick_action_card(icon, title, description):
    html = f"""
    <div class="quick-card">
        <div class="quick-icon">{icon}</div>
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def recent_interview_card(role, date, score):
    html = f"""
    <div class="recent-row">
        <div>
            <div style="font-weight:800;font-size:17px;color:white;">{role}</div>
            <div style="color:#94a3b8;font-size:13px;">{date}</div>
        </div>
        <div class="score-badge">{score}/10</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def ai_tip(text):
    html = f"""
    <div class="tip-box">
        ✅ {text}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)