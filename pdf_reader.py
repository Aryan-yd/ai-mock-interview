from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract readable text from an uploaded PDF file."""
    if uploaded_file is None:
        return ""

    text_parts = []
    try:
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            text = page.extract_text() or ""
            text_parts.append(text)
    except Exception as exc:
        return f"PDF text extraction failed: {exc}"

    return "\n".join(text_parts).strip()
