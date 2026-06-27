import streamlit as st


def show_feedback_card(feedback):
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    score = feedback.get("score", 0)
    st.metric("Answer Score", f"{score}/10")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Correct", feedback.get("correctness", 0))
    c2.metric("Confidence", feedback.get("confidence", 0))
    c3.metric("Complete", feedback.get("completeness", 0))
    c4.metric("Communication", feedback.get("communication", 0))
    c5.metric("Depth", feedback.get("technical_depth", 0))

    st.subheader("✅ Strengths")
    for item in feedback.get("strengths", []):
        st.write("•", item)
    st.subheader("⚠️ Weaknesses")
    for item in feedback.get("weaknesses", []):
        st.write("•", item)
    st.subheader("✨ Improved Answer")
    st.info(feedback.get("improved_answer", ""))
    st.subheader("💡 Tips")
    for item in feedback.get("tips", []):
        st.write("•", item)
    st.markdown("</div>", unsafe_allow_html=True)


def show_final_feedback(final_feedback):
    st.markdown("<div class='hero-card'>", unsafe_allow_html=True)
    st.header("🏆 Final Interview Result")
    st.metric("Overall Score", f"{final_feedback.get('overall_score', 0)}/10")
    for title, key in [("Strengths", "strengths"), ("Weaknesses", "weaknesses"), ("Areas to Improve", "areas_to_improve"), ("Final Tips", "final_tips")]:
        st.subheader(title)
        for item in final_feedback.get(key, []):
            st.write("•", item)
    st.markdown("</div>", unsafe_allow_html=True)
