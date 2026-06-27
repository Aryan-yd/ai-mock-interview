# 🎯 AI Interview Coach
### Professional AI-powered mock interview web app using Streamlit + Google Gemini API

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_App-FF4B4B?logo=streamlit)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)

AI Interview Coach helps users prepare for interviews by reading their resume and job description, generating personalized questions, evaluating answers, showing progress, and exporting a PDF report.

---

## ✨ Features

- User sign up and login
- Resume PDF upload and parsing
- Job description paste or PDF upload
- Gemini-powered question generation
- HR, technical, behavioral, project-based, and coding questions
- One-question-at-a-time interview flow
- AI answer evaluation with score and detailed feedback
- Strengths, weaknesses, improved answer, and tips
- SQLite interview history
- Dashboard with progress charts
- PDF report download
- Professional dark glassmorphism UI theme

---

## 🧰 Tech Stack

| Area | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| Database | SQLite |
| Generative AI | Google Gemini API |
| Resume Parsing | PyMuPDF |
| Charts | Plotly |
| Reports | FPDF2 |

---

## 📁 Folder Structure

```text
AI-Interview-Coach/
│
├── app.py
├── login.py
├── interview.py
├── feedback.py
├── database.py
├── pdf_reader.py
├── gemini.py
├── report_generator.py
├── requirements.txt
├── README.md
├── .env.example
├── .streamlit/
│   └── config.toml
├── assets/
├── database/
└── reports/
```

---

## 🚀 How to Run

### 1. Create virtual environment

```bash
python -m venv venv
```

### 2. Activate virtual environment

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

### 3. Install requirements

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Add Gemini API key

Create a file named `.env` in the project folder:

```env
GEMINI_API_KEY=your_google_ai_studio_api_key_here
```

### 5. Run app

```bash
streamlit run app.py
```

---

## 🧠 Skills Demonstrated

- Prompt engineering
- LLM integration
- Resume parsing
- PDF processing
- Authentication
- SQLite database design
- Streamlit UI development
- Dashboard analytics
- PDF report generation

---

## 📌 Notes

This project uses a local SQLite database. It is perfect for portfolio demos and student projects. For production, use stronger password hashing, cloud database storage, secure secrets management, and role-based access control.


## Important Python Version Note

Recommended Python version: **Python 3.11 or Python 3.12**.

Python 3.14 is very new, so some packages may try to compile from source on Windows. If installation fails, create the virtual environment using Python 3.12:

```bash
py -3.12 -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```
