import re
import streamlit as st


def extract_skills_heuristic(text: str) -> list:
    """Heuristic fallback to detect common tech skills if Gemini is offline."""
    known_skills = [
        "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "HTML", "CSS",
        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "SQLite", "Redis",
        "Docker", "Kubernetes", "Git", "GitHub", "Linux", "AWS", "Azure", "GCP",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "NLP",
        "Data Analysis", "Pandas", "NumPy", "Scikit-Learn", "Streamlit",
        "REST API", "GraphQL", "Agile", "Scrum", "CI/CD", "DevOps"
    ]
    found = []
    text_lower = text.lower()
    for skill in known_skills:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def extract_education_heuristic(text: str) -> list:
    """Heuristic fallback to extract degrees and colleges."""
    edu = []
    degrees = ["B.Tech", "B.E.", "B.S.", "B.Sc", "M.Tech", "M.S.", "M.Sc", "MCA", "BCA", "PhD", "Bachelor", "Master"]
    lines = text.split("\n")
    for line in lines:
        line_clean = line.strip()
        if any(deg.lower() in line_clean.lower() for deg in degrees) and len(line_clean) < 120:
            if line_clean not in edu:
                edu.append(line_clean)
    return edu[:4]


def render_resume_insights(resume_info: dict, resume_text: str = ""):
    """Renders a comprehensive, styled resume insights dashboard."""
    if not resume_info and not resume_text:
        st.info("No resume data uploaded yet.")
        return

    # Extract heuristics if AI fields are empty
    skills = resume_info.get("skills") or []
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    if not skills and resume_text:
        skills = extract_skills_heuristic(resume_text)

    education = resume_info.get("education") or []
    if not education and resume_text:
        education = extract_education_heuristic(resume_text)

    projects = resume_info.get("projects") or []
    experience = resume_info.get("experience") or []
    summary = resume_info.get("summary") or ""

    st.markdown(
        """
        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 16px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #38bdf8; margin-top: 0;">📄 Extracted Resume Insights</h3>
            <p style="color: #cbd5e1; font-size: 14px;">
                Verified candidate profile extracted using AI parsing & keyword extraction.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Summary
    if summary:
        st.markdown("#### 📌 Professional Summary")
        st.info(summary)

    # Skills Badges
    st.markdown("#### 🛠️ Detected Skills & Technologies")
    if skills:
        badge_html = "<div style='display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px;'>"
        for sk in skills:
            sk_text = sk if isinstance(sk, str) else str(sk)
            badge_html += (
                f"<span style='background: linear-gradient(135deg, #4f46e5, #06b6d4); "
                f"color: white; padding: 5px 12px; border-radius: 20px; font-size: 13px; "
                f"font-weight: 600; box-shadow: 0 2px 6px rgba(0,0,0,0.25);'>{sk_text}</span>"
            )
        badge_html += "</div>"
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.caption("No specific skills detected.")

    # Two columns for Education and Experience/Projects
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 🎓 Education")
        if education:
            for item in education:
                if isinstance(item, dict):
                    deg = item.get("degree", "Degree")
                    inst = item.get("institution") or item.get("college") or ""
                    yr = item.get("year", "")
                    st.markdown(f"- **{deg}** {f'({yr})' if yr else ''}<br><span style='color:#94a3b8;'>{inst}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"- {item}")
        else:
            st.caption("No formal education entries detected.")

    with c2:
        st.markdown("#### 💼 Experience / Background")
        if experience:
            for item in experience:
                if isinstance(item, dict):
                    role = item.get("role", "Position")
                    company = item.get("company", "")
                    dur = item.get("duration", "")
                    st.markdown(f"- **{role}** - *{company}* ({dur})")
                else:
                    st.markdown(f"- {item}")
        elif projects:
            st.markdown("*(Projects highlighted as key experience)*")
            for item in projects[:3]:
                if isinstance(item, dict):
                    st.markdown(f"- **{item.get('title', 'Project')}**: {item.get('description', '')[:100]}...")
                else:
                    st.markdown(f"- {item}")
        else:
            st.caption("No experience entries detected.")

    # Projects Detailed Section
    if projects and isinstance(projects, list) and isinstance(projects[0], dict):
        with st.expander("🚀 View Extracted Projects"):
            for p in projects:
                st.markdown(f"**{p.get('title', 'Project')}**")
                if p.get("tech_stack"):
                    st.caption(f"Tech: {p.get('tech_stack')}")
                if p.get("description"):
                    st.write(p.get("description"))

    # Raw text expander
    if resume_text:
        with st.expander("📄 View Extracted Raw Text"):
            st.text(resume_text[:4000] + ("..." if len(resume_text) > 4000 else ""))
