import os
import re
import textwrap
from pathlib import Path
from fpdf import FPDF


def clean_text(text):
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("•", "-")
    text = text.replace("✅", "").replace("❌", "").replace("⭐", "")
    text = text.replace("🎯", "").replace("🤖", "").replace("📄", "")
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    return text.strip()


def safe_write(pdf, text, font_size=10):
    pdf.set_font("Arial", "", font_size)
    text = clean_text(text)

    if not text:
        return

    page_width = pdf.w - pdf.l_margin - pdf.r_margin

    for paragraph in text.split("\n"):
        lines = textwrap.wrap(paragraph, width=80)

        if not lines:
            pdf.ln(6)

        for line in lines:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(page_width, 7, line)

def section_title(pdf, title):
    pdf.ln(5)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, clean_text(title), ln=True)
    pdf.set_x(pdf.l_margin)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(3)


def generate_report(username, role, questions, answers, feedback, final_feedback, interview_id=None):
    os.makedirs("reports", exist_ok=True)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 12, "AI Interview Coach Report", ln=True, align="C")

    pdf.ln(5)

    pdf.set_font("Arial", "", 11)
    safe_write(pdf, f"Candidate: {username}")
    safe_write(pdf, f"Target Role: {role}")

    overall_score = final_feedback.get("overall_score", 0) if isinstance(final_feedback, dict) else 0
    safe_write(pdf, f"Overall Score: {overall_score}/10")

    section_title(pdf, "Questions and Answers")

    for i, question in enumerate(questions):
        q_text = question.get("question", question) if isinstance(question, dict) else question
        q_type = question.get("type", "General") if isinstance(question, dict) else "General"
        ans = answers[i] if i < len(answers) else "No answer provided."

        pdf.set_font("Arial", "B", 11)
        safe_write(pdf, f"Question {i + 1} ({q_type}): {q_text}", 10)

        pdf.set_font("Arial", "", 10)
        safe_write(pdf, f"Answer: {ans}", 10)
        pdf.ln(2)

    section_title(pdf, "Answer Feedback")

    if isinstance(feedback, list):
        for i, fb in enumerate(feedback):
            pdf.set_font("Arial", "B", 11)
            safe_write(pdf, f"Feedback for Question {i + 1}", 11)

            if isinstance(fb, dict):
                safe_write(pdf, f"Score: {fb.get('score', 0)}/10")

                for key in ["strengths", "weaknesses", "tips"]:
                    values = fb.get(key, [])
                    if values:
                        pdf.set_font("Arial", "B", 10)
                        safe_write(pdf, key.replace("_", " ").title())
                        pdf.set_font("Arial", "", 10)

                        if isinstance(values, list):
                            for item in values:
                                safe_write(pdf, f"- {item}")
                        else:
                            safe_write(pdf, values)

                improved = fb.get("improved_answer", "")
                if improved:
                    pdf.set_font("Arial", "B", 10)
                    safe_write(pdf, "Improved Answer")
                    pdf.set_font("Arial", "", 10)
                    safe_write(pdf, improved)
            else:
                safe_write(pdf, fb)

            pdf.ln(3)

    section_title(pdf, "Final Feedback")

    if isinstance(final_feedback, dict):
        for key, value in final_feedback.items():
            pdf.set_font("Arial", "B", 11)
            safe_write(pdf, key.replace("_", " ").title(), 11)

            pdf.set_font("Arial", "", 10)

            if isinstance(value, list):
                for item in value:
                    safe_write(pdf, f"- {item}")
            else:
                safe_write(pdf, value)

            pdf.ln(2)
    else:
        safe_write(pdf, final_feedback)

    filename = f"interview_report_{interview_id or 'latest'}.pdf"
    file_path = Path("reports") / filename
    pdf.output(str(file_path))

    return file_path