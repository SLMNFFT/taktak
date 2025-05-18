import streamlit as st
import pdfplumber
import tempfile
import re
import base64
import arabic_reshaper
from bidi.algorithm import get_display
from gtts import gTTS
from langdetect import detect
from fpdf import FPDF

# Map language codes for Tesseract if needed (expand if OCR included)
TESSERACT_LANG_MAP = {
    "ar": "ara",
    "en": "eng",
    # add others if used
}

# Custom CSS for RTL Arabic text display
st.markdown(
    """
    <style>
    .rtl-text {
        direction: rtl;
        text-align: right;
        font-family: 'Arial', sans-serif;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .text-container {
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 5px;
        max-height: 400px;
        overflow-y: auto;
        background-color: #f9f9f9;
    }
    mark {
        background-color: yellow;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def extract_text_from_pdf(pdf_path, pages):
    full_text = ""
    ocr_pages = set()  # pages where only OCR text found (if OCR implemented)
    with pdfplumber.open(pdf_path) as pdf:
        for p in pages:
            if p-1 < len(pdf.pages):
                page = pdf.pages[p-1]
                text = page.extract_text()
                if text:
                    full_text += f"--- Page {p} ---\n{text}\n\n"
                else:
                    # OCR fallback could be added here if needed
                    ocr_pages.add(p)
                    full_text += f"--- Page {p} ---\n[No extractable text found - OCR needed]\n\n"
    return full_text, ocr_pages

def detect_content_language(text):
    try:
        return detect(text)
    except:
        return "en"

def export_text_to_pdf(text, lang="en"):
    # For Arabic, reshape text for proper PDF display
    if lang == "ar":
        reshaped_text = arabic_reshaper.reshape(text)
        display_text = get_display(reshaped_text)
    else:
        display_text = text

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    # Split text into lines
    for line in display_text.split("\n"):
        pdf.multi_cell(0, 10, line)
    # Save to temp file
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)
    return tmp_pdf.name

def main():
    st.title("Peepit Audiobook PDF Text Extractor & Exporter")
    st.write("Upload a PDF to extract text (supports Arabic with proper display).")

    uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            pdf_path = tmp.name

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            selected_pages = st.multiselect("Select pages to process", list(range(1, total_pages + 1)), default=[1])

        if not selected_pages:
            st.error("Please select at least one page")
            return

        with st.spinner("Extracting text..."):
            full_text, ocr_pages = extract_text_from_pdf(pdf_path, selected_pages)
            if not full_text.strip():
                st.error("No extractable text found in selected pages.")
                return

            content_lang = detect_content_language(full_text)
            if content_lang not in TESSERACT_LANG_MAP:
                st.warning(f"Detected language '{content_lang}' may not be fully supported.", icon="⚠️")

            col_left, col_right = st.columns(2)

            with col_left:
                with st.expander("📜 Extracted Text", expanded=True):
                    search_term = st.text_input("🔎 Search within text", "")
                    show_ocr = st.checkbox("Show OCR-only pages text", value=True)

                    filtered_text = ""
                    if show_ocr:
                        filtered_text = full_text
                    else:
                        # Filter out OCR pages text
                        for p in selected_pages:
                            if p not in ocr_pages:
                                pattern = f"--- Page {p} ---\\n(.*?)(?=--- Page|$)"
                                match = re.search(pattern, full_text, re.DOTALL)
                                if match:
                                    filtered_text += match.group(1).strip() + "\n\n"

                    if search_term:
                        filtered_text = re.sub(
                            f"(?i)({re.escape(search_term)})",
                            r"<mark>\1</mark>",
                            filtered_text,
                            flags=re.DOTALL,
                        )

                    # For Arabic, reshape and bidi for correct display
                    if content_lang == "ar":
                        reshaped = arabic_reshaper.reshape(filtered_text)
                        display_text = get_display(reshaped)
                        text_class = "rtl-text"
                    else:
                        display_text = filtered_text
                        text_class = ""

                    st.markdown(
                        f'<div class="text-container {text_class}">{display_text.replace("\n", "<br>")}</div>',
                        unsafe_allow_html=True,
                    )

                    if st.button("📄 Export Extracted Text as PDF"):
                        pdf_export = export_text_to_pdf(filtered_text, lang=content_lang)
                        with open(pdf_export, "rb") as f:
                            pdf_bytes = f.read()
                        b64 = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/octet-stream;base64,{b64}" download="extracted_text.pdf">Download PDF</a>'
                        st.markdown(href, unsafe_allow_html=True)

    else:
        st.info("Please upload a PDF file to get started.")

if __name__ == "__main__":
    main()