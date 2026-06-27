import streamlit as st

def hero_section(username="Maham"):
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-grid">
                <div>
                    <div style="display:inline-block;padding:10px 16px;border-radius:999px;background:rgba(255,255,255,0.10);border:1px solid rgba(255,255,255,0.14);color:#c4b5fd;font-weight:800;margin-bottom:18px;">
                        🚀 AI Powered Interview Preparation
                    </div>

                    <h1>Welcome Back,<br><span class="gradient-text">{username} 👋</span></h1>

                    <p>
                        Practice HR, technical, behavioral and project-based interviews with Gemini AI.
                        Get instant feedback and prepare confidently.
                    </p>
                </div>

                <div class="robot-card">🤖</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    b1, b2 = st.columns([1, 1])

    with b1:
        if st.button("🎯 Start Interview", use_container_width=True):
            st.session_state.page = "Interview"
            st.rerun()

    with b2:
        if st.button("📄 Upload Resume", use_container_width=True):
            st.session_state.page = "Interview"
            st.rerun()