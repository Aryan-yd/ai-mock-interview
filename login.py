import streamlit as st
from database import create_user, authenticate_user


def auth_page():
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    st.title("🎯 AI Interview Coach")
    st.caption("Practice smarter. Improve faster. Get interview-ready with Gemini AI.")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            user = authenticate_user(email, password)
            if user:
                st.session_state.user = user
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with tab2:
        name = st.text_input("Full Name")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Create Account", use_container_width=True):
            if not name or not new_email or not new_password:
                st.warning("Please fill all fields.")
            elif len(new_password) < 6:
                st.warning("Password should be at least 6 characters.")
            else:
                ok, msg = create_user(name, new_email, new_password)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
    st.markdown("</div>", unsafe_allow_html=True)
