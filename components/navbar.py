import streamlit as st

def navbar(active="Dashboard"):
    user = st.session_state.get("user", {})
    username = user.get("name", "Maham")

    html = f"""
<div class="main-navbar"><div class="logo-box"><div class="logo-icon">🤖</div><div><div style="font-size:24px;font-weight:800;">AI Interview Coach</div><div style="font-size:13px;color:#cbd5e1;">Practice • Improve • Get Hired</div></div></div><div class="nav-links"><div class="nav-pill {'active' if active == 'Dashboard' else ''}">Dashboard</div><div class="nav-pill {'active' if active == 'Interview' else ''}">Interview</div><div class="nav-pill {'active' if active == 'Practice' else ''}">Practice</div><div class="nav-pill {'active' if active == 'History' else ''}">History</div><div class="nav-pill {'active' if active == 'Reports' else ''}">Reports</div></div><div style="display:flex;align-items:center;gap:14px;"><div style="font-size:22px;">🔔</div><div style="font-weight:800;color:white;">{username}</div></div></div>
"""
    st.html(html)