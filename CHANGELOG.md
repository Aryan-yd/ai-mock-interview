# CHANGELOG - AI Interview Coach (InterviewOS)

All notable changes to the AI Interview Coach project since Milestone 1 are documented below.

## [Milestone 2 Final Release] - 2026-11-21
### Added
- **Google Gemini REST API Integration**: Direct HTTPS client utilizing `gemini-flash-lite-latest` with sub-second response times, markdown stripping, and resilient JSON error recovery.
- **Multimodal Interview Pipeline**: Live candidate webcam presence monitor (`st.camera_input`) and real-time speech-to-text voice transcription via `streamlit-mic-recorder`.
- **Dynamic Adaptive Follow-Up Branching**: Dynamic branching logic evaluating candidate response score (threshold >= 7/10) to trigger advanced technical drill-downs or clarifying scenarios.
- **Role-Competency Prompt Re-engineering**: Eliminated resume-project looping bias to mandate core role competencies (e.g., SQL window functions, CTEs, and KPIs for Data Analyst roles).
- **Dual Engine Architecture**: Seamless switching between Gemini Live AI and an Offline Demo Mode with pre-calibrated role question banks.
- **Automated Scorecard PDF**: Generates comprehensive multi-page PDF evaluation report with candidate snapshot and radar charts.
- **Verification Suite**: 10 rigorous test cases covering Normal, Edge (Hinglish, minimal resume), and Invalid (one-word 'idk', empty answer) scenarios.

## [Milestone 1 Baseline] - 2026-11-02
### Initial
- Static Streamlit UI dashboard and basic SQLite user authentication.
- Heuristic PDF resume parser with static mock interview questions.
