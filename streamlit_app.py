import streamlit as st
import re
import tempfile
import base64
import pdfplumber
from pypdf import PdfReader
from PIL import Image
from fpdf import FPDF
import io
from gtts import gTTS
import os
import requests

st.set_page_config(
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
)

st.markdown("""
<style>
/* Your CSS styles here, unchanged... */
[data-testid="stColumns"] {
    display: flex;
    align-items: stretch;
    gap: 2rem;
}
.preview-card {
    background: #1A1B2F;
    border-radius: 15px;
    padding: 1.5rem;
    height: 100% !important;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 15px rgba(10, 10, 30, 0.5);
    transition: background 0.3s ease;
}
.preview-card:hover {
    background: #252742;
}
.scroll-container {
    flex: 1;
    overflow-y: auto;
    padding-right: 0.5rem;
    scrollbar-width: thin;
    scrollbar-color: #4e5aee #1A1B2F;
}
.scroll-container::-webkit-scrollbar {
    width: 8px;
}
.scroll-container::-webkit-scrollbar-track {
    background: #1A1B2F;
    border-radius: 10px;
}
.scroll-container::-webkit-scrollbar-thumb {
    background-color: #4e5aee;
    border-radius: 10px;
    border: 2px solid #1A1B2F;
}
.preview-image-container {
    display: grid;
    gap: 1rem;
    padding-bottom: 1rem;
    margin-top: 0;
}
.preview-image {
    background: #2B2D42;
    border-radius: 8px;
    padding: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    display: flex;
    flex-direction: column;
    align-items: center;
}
.preview-image:first-child {
    margin-top: 0;
}
.preview-image img {
    border-radius: 6px;
    margin-bottom: 0.5rem;
    width: 100%;
    height: auto;
    object-fit: contain;
    user-select: none;
}
.preview-image p {
    text-align: center;
    color: #888;
    margin: 0;
    font-size: 0.9rem;
    font-style: italic;
    user-select: none;
}
body, pre {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #ddd;
    background-color: #0f1123;
}
pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 0.95rem;
    line-height: 1.4;
}
.centered-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 80vh;
    gap: 1rem;
}
@media (max-width: 768px) {
    [data-testid="stColumns"] {
        flex-direction: column;
    }
    .preview-card {
        height: auto !important;
        margin-bottom: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)


def pil_to_base64(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def extract_text_with_ocr(pdf_path, pages):
    from pdf2image import convert_from_path
    import pytesseract
    text = ""
    images = convert_from_path(pdf_path, dpi=300, first_page=min(pages), last_page=max(pages))
    for i, img in zip(pages, images):
        text += f"--- Page {i} (OCR) ---\n"
        text += pytesseract.image_to_string(img)
        text += "\n\n"
    return text

def extract_text_from_pdf(pdf_path, selected_pages):
    reader = PdfReader(pdf_path)
    extracted_text = ""
    pages_without_text = []

    if not selected_pages:
        return "", []

    for i in selected_pages:
        if i < 1 or i > len(reader.pages):
            continue
        page = reader.pages[i - 1]
        text = page.extract_text()
        if text and text.strip():
            extracted_text += f"--- Page {i} ---\n{text}\n\n"
        else:
            pages_without_text.append(i)

    valid_ocr_pages = [p for p in pages_without_text if 1 <= p <= len(reader.pages)]
    if valid_ocr_pages:
        st.warning(f"🔍 Running OCR on pages: {valid_ocr_pages}")
        ocr_text = extract_text_with_ocr(pdf_path, valid_ocr_pages)
        extracted_text += ocr_text

    return extracted_text.strip(), valid_ocr_pages


def generate_audio(text, lang="en", rate=1.0, gender="male"):
    tts = gTTS(text=text, lang=lang, slow=(rate < 1.0))
    temp_audio_path = tempfile.mktemp(suffix=".mp3")
    tts.save(temp_audio_path)
    return temp_audio_path

def save_images_as_pdf(images):
    pdf = FPDF()
    for img in images:
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        image_path = tempfile.mktemp(suffix=".png")
        with open(image_path, "wb") as f:
            f.write(bio.read())
        pdf.add_page()
        pdf.image(image_path, x=10, y=10, w=pdf.w - 20)
        os.remove(image_path)
    pdf_path = tempfile.mktemp(suffix=".pdf")
    pdf.output(pdf_path)
    return pdf_path

def download_pdf(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_file.write(resp.content)
        tmp_file.close()
        return tmp_file.name
    except Exception as e:
        st.error(f"Failed to download PDF from URL: {e}")
        return None

def main():
    st.title("🎧 Peepit Audiobook")

    pdf_file = st.file_uploader("Upload a PDF file (text-based PDFs only)", type=["pdf"])
    pdf_url = st.text_input("Or enter a PDF URL")

    if not pdf_file and not pdf_url:
        # Centered layout before upload
        st.markdown("""
        <div class="centered-container">
            <h1 style='
                background: #2ecc71;
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                font-weight: 600;
                margin: 0;
                width: 100%;
                max-width: 480px;
            '>🎧 PeePit</h1>
            <div style="width: 100%; max-width: 480px;">
                <p style="color: #ddd; text-align:center;">Upload a PDF file or enter a URL to get started</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    pdf_path = None
    if pdf_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            pdf_path = tmp.name
    elif pdf_url:
        pdf_path = download_pdf(pdf_url)

    if not pdf_path:
        st.warning("Please upload a valid PDF file or enter a valid URL to continue.")
        return

    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
        return

    total_pages = len(reader.pages)
    selected_pages = st.multiselect("Select pages to process", list(range(1, total_pages + 1)), default=[1])

    if not selected_pages:
        st.error("Please select at least one valid page")
        return

    # --- Left Column: Full PDF Preview ---
    with st.expander("📄 Full PDF Preview", expanded=True):
        st.write("**PDF Pages**")
        images = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in selected_pages:
                page = pdf.pages[page_num - 1]
                img = page.to_image()
                images.append(img.original)
        for img in images:
            st.image(img
