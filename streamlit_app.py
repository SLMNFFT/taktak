import streamlit as st
from pypdf import PdfReader
from langdetect import detect
from gtts import gTTS
import tempfile
import requests
import pdfplumber
from PIL import Image
from io import BytesIO
import base64
import os

# OCR requirements
import pytesseract
from pdf2image import convert_from_path

st.set_page_config(
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
)

# Modern UI Styles
st.markdown("""
    <style>
    html, body, [class*="css"] {
        background-color: #0F0F1C;
        color: #F8F9FA;
        font-family: 'Inter', sans-serif;
    }
    .block-container { padding-top: 1rem; padding-bottom: 0; }
    .header-gradient {
        background: linear-gradient(135deg, #25C9A5 0%, #2B2D42 100%);
        padding: 2rem 2rem 4rem;
        margin: -1rem -2rem 2rem;
        border-radius: 0 0 20px 20px;
    }
    .upload-card {
        background: rgba(43, 45, 66, 0.5);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
    }
    .preview-card {
        background: #1A1B2F;
        border-radius: 15px;
        padding: 1.5rem;
        height: 70vh;
        overflow-x: auto;
        white-space: nowrap;
    }
    .preview-image {
        display: inline-block;
        max-height: 500px;
        margin-right: 1rem;
        border-radius: 8px;
        vertical-align: top;
    }
    .preview-image img {
        border-radius: 8px;
        max-height: 500px;
        display: block;
    }
    .preview-image p {
        text-align: center;
        color: #aaa;
        margin: 0.3rem 0 0 0;  /* Remove top margin */
        font-size: 0.9rem;
    }
    pre {
        white-space: pre-wrap;
        word-break: break-word;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        line-height: 1.4;
        color: #ddd;
        background-color: transparent;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)


def pil_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def extract_text_with_ocr(pdf_path, selected_pages):
    images = convert_from_path(pdf_path, dpi=300)
    text_content = ""
    for i, img in enumerate(images):
        if (i + 1) in selected_pages:
            text = pytesseract.image_to_string(img, lang='eng')
            text_content += f"--- Page {i + 1} ---\n{text}\n\n"
    return text_content


def extract_text_from_pdf(pdf_path, selected_pages):
    reader = PdfReader(pdf_path)
    extracted_text = ""
    pages_without_text = []

    for i in selected_pages:
        page = reader.pages[i - 1]
        text = page.extract_text()
        if text and text.strip():
            extracted_text += f"--- Page {i} ---\n{text}\n\n"
        else:
            pages_without_text.append(i)

    if pages_without_text:
        st.warning(f"🔍 Some pages lacked extractable text. Running OCR on pages: {pages_without_text}")
        ocr_text = extract_text_with_ocr(pdf_path, pages_without_text)
        extracted_text += ocr_text

    return extracted_text


def main():
    st.markdown("""
        <div class="header-gradient">
            <h1 style="color: white; margin: 0;">🎧 PeePit</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem; margin-top: 0;">
                Legere eam Drusus<br>
                Transform your doc into immersive mp3 (no PDF images and image PDFs)
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    pdf_file = None
    pdf_url = None

    with col1:
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        pdf_file = st.file_uploader("📤 Upload PDF", type=["pdf"])
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        pdf_url = st.text_input("🌐 PDF URL", placeholder="Enter document URL...")
        st.markdown('</div>', unsafe_allow_html=True)

    pdf_path = None
    if pdf_file or pdf_url:
        if pdf_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_file.read())
                pdf_path = tmp_file.name
        elif pdf_url:
            try:
                response = requests.get(pdf_url, timeout=10)
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(response.content)
                    pdf_path = tmp_file.name
            except Exception as e:
                st.error(f"❌ Error fetching PDF: {str(e)}")
                return

        with st.spinner("🔍 Analyzing document..."):
            pdf_reader = PdfReader(pdf_path)
            total_pages = len(pdf_reader.pages)

            st.sidebar.markdown("## 📄 Page Selection")
            selected_pages = st.sidebar.multiselect(
                "Select pages to convert:",
                options=list(range(1, total_pages + 1)),
                default=[1]
            )

            if not selected_pages:
                st.warning("Please select at least one page.")
                return

            col_left, col_right = st.columns(2)

            with st.spinner("📜 Extracting text..."):
                full_text = extract_text_from_pdf(pdf_path, selected_pages)

            with col_left:
                with st.expander("📜 Extracted Text", expanded=True):
                    st.markdown(f"""
                        <div class="preview-card" style="overflow-y:auto;">
                            <pre>{full_text}</pre>
                        </div>
                    """, unsafe_allow_html=True)

            if full_text.strip():
                try:
                    lang = detect(full_text[:500])
                    st.success(f"🌍 Detected language: {lang.upper()}")

                    if st.button("🎧 Generate Audiobook"):
                        with st.spinner("🔊 Generating audio..."):
                            tts = gTTS(text=full_text, lang=lang)
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                                tts.save(fp.name)
                                st.audio(fp.name, format="audio/mp3")
                                with open(fp.name, "rb") as audio_file:
                                    st.download_button(
                                        label="💾 Download Audiobook",
                                        data=audio_file,
                                        file_name="audiobook.mp3",
                                        mime="audio/mp3"
                                    )
                except Exception as e:
                    st.error(f"Audio generation error: {e}")
            else:
                st.warning("⚠️ No text found to convert.")

            # Visual preview of selected PDF pages
            with col_right:
                with st.expander("🖼️ Visual Preview", expanded=True):
                    st.markdown("""<div class="preview-card">""", unsafe_allow_html=True)
                    with pdfplumber.open(pdf_path) as pdf:
                        for i, page in enumerate(pdf.pages):
                            if (i + 1) in selected_pages:
                                img = page.to_image(resolution=150).original
                                img_base64 = pil_to_base64(img)
                                st.markdown(f"""
                                    <div class="preview-image">
                                        <img src="data:image/png;base64,{img_base64}" />
                                        <p>Page {i + 1}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            # Full PDF preview (only works for public URLs)
            if pdf_url:
                st.markdown("### 📄 Full PDF Preview (URL only)", unsafe_allow_html=True)
                # Google Docs viewer only works with publicly accessible URLs, not local files
                google_docs_url = f"https://docs.google.com/gview?url={pdf_url}&embedded=true"
                try:
                    st.components.v1.iframe(google_docs_url, height=800, scrolling=True)
                except Exception as e:
                    st.error(f"Could not render full PDF preview: {e}")
            elif pdf_file:
                st.info("Full PDF preview only works for PDF URL uploads.")

    else:
        st.markdown("""
            <div style="text-align: center; padding: 4rem 0; opacity: 0.8;">
                <div style="font-size: 4rem;">📚</div>
                <h3>Upload a document to begin</h3>
                <p>Supported format: PDF</p>
            </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
