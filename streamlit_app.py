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
import pytesseract
import pdf2image
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError


st.set_page_config(
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
    menu_items={
        'Get Help': 'https://github.com/mogontia/audiobook-gen',
        'Report a bug': "https://github.com/mogontia/audiobook-gen/issues",
        'About': """
        ## 🎧 PeePit Audiobook Generator 
        **Version 2.1**  
        Transform documents into immersive audio experiences  
        """
    }
)

# CSS Styles (same as yours, unchanged)
st.markdown("""
    <style>
    :root {
        --primary: #25C9A5;
        --secondary: #2B2D42;
        --accent: #FF6B6B;
        --background: #0F0F1C;
    }
    html, body, [class*="css"] {
        background-color: var(--background);
        color: #F8F9FA;
        font-family: 'Inter', sans-serif;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0;
    }
    .header-gradient {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 2rem 2rem 4rem;
        margin: -1rem -2rem 2rem;
        border-radius: 0 0 20px 20px;
    }
    .upload-card {
        background: rgba(43, 45, 66, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 2rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-weight: 600;
        transition: transform 0.2s ease;
    }
    .preview-card {
        background: #1A1B2F;
        border-radius: 15px;
        padding: 1.5rem;
        position: relative;
        height: 70vh;
        display: flex;
        flex-direction: column;
    }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #1A1B2F; }
    ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }
    .preview-content {
        flex: 1;
        overflow-y: auto;
        padding: 0.5rem;
    }
    @media (max-width: 768px) {
        .header-gradient {
            padding: 1rem 1rem 3rem;
            margin: -1rem -1rem 1rem;
        }
        .upload-card {
            padding: 1rem;
        }
        .preview-card {
            height: 50vh !important;
            margin-bottom: 4rem;
        }
        .stButton>button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        [data-testid="column"] {
            width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)


def extract_text_with_ocr(pdf_path, pages):
    try:
        images = pdf2image.convert_from_path(pdf_path, dpi=300)
    except PDFInfoNotInstalledError:
        st.error("⚠️ PDF to image conversion requires 'poppler-utils' installed on the system.")
        return ""
    except PDFPageCountError:
        st.error("❌ Could not read PDF pages for OCR.")
        return ""

    ocr_text = ""
    for i, image in enumerate(images):
        page_num = i + 1
        if page_num in pages:
            text = pytesseract.image_to_string(image)
            ocr_text += text + "\n"
    return ocr_text


def extract_text_from_pdf(pdf_path, pages):
    reader = PdfReader(pdf_path)
    full_text = ""
    pages_without_text = []

    for page_num in pages:
        try:
            page = reader.pages[page_num - 1]
            text = page.extract_text()
            if text and text.strip():
                full_text += text + "\n"
            else:
                pages_without_text.append(page_num)
        except IndexError:
            st.warning(f"Page {page_num} is out of range for this document.")
            continue

    if pages_without_text:
        ocr_text = extract_text_with_ocr(pdf_path, pages_without_text)
        full_text += "\n" + ocr_text

    return full_text.strip()


def save_temp_file(data, suffix):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data)
    tmp.close()
    return tmp.name


def generate_audio(text, lang):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
        tts = gTTS(text=text, lang=lang)
        tts.save(audio_file.name)
        return audio_file.name


def fetch_pdf_from_url(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"❌ Error fetching PDF from URL: {e}")
        return None


def render_pdf_images(pdf_path, pages):
    try:
        images = pdf2image.convert_from_path(
            pdf_path,
            dpi=100,
            first_page=min(pages),
            last_page=max(pages),
            thread_count=2,
        )
        # Show only selected pages images
        for idx, img in enumerate(images, start=min(pages)):
            if idx in pages:
                st.image(img, use_column_width=True)
    except PDFInfoNotInstalledError:
        st.error("⚠️ Poppler-utils not installed; visual preview unavailable.")
    except Exception as e:
        st.error(f"Error rendering PDF preview: {str(e)}")


def main():
    st.markdown("""
        <div class="header-gradient">
            <h1 style="color: white; margin: 0;">🎧PeePit</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem;">
                Peep your doc after transforming it into immersive mp3 Audiobook
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
            pdf_bytes = pdf_file.read()
            pdf_path = save_temp_file(pdf_bytes, ".pdf")
        elif pdf_url:
            pdf_bytes = fetch_pdf_from_url(pdf_url)
            if pdf_bytes:
                pdf_path = save_temp_file(pdf_bytes, ".pdf")
            else:
                return

        # Validate PDF and get page count
        try:
            pdf_reader = PdfReader(pdf_path)
            total_pages = len(pdf_reader.pages)
        except Exception as e:
            st.error(f"❌ Error reading PDF: {e}")
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)
            return

        if total_pages == 0:
            st.warning("PDF has no pages.")
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)
            return

        st.sidebar.markdown("## 📄 Page Selection")
        selected_pages = st.sidebar.multiselect(
            "Select pages to convert:",
            options=list(range(1, total_pages + 1)),
            default=[1],
        )
        if not selected_pages:
            st.info("Select at least one page to process.")
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)
            return

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            with st.expander("📜 Document Text", expanded=True):
                with st.spinner("Extracting text..."):
                    full_text = extract_text_from_pdf(pdf_path, selected_pages)

                if full_text:
                    st.markdown(f"""
                        <div class="preview-card">
                            <div class="preview-content">
                                <pre style="color: #e0e0e0; white-space: pre-wrap;">{full_text}</pre>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No text found on selected pages.")

        with col_right:
            with st.expander("🖼️ Visual Preview", expanded=True):
                if selected_pages:
                    render_pdf_images(pdf_path, selected_pages)
                else:
                    st.info("No pages selected for preview.")

        if full_text:
            try:
                detected_lang = detect(full_text[:500])
                st.success(f"🌍 Detected language: {detected_lang.upper()}")
            except Exception:
                detected_lang = "en"
                st.warning("Could not detect language. Defaulting to English.")

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("🎧 Generate Audiobook"):
                    with st.spinner("Generating audio..."):
                        try:
                            audio_file_path = generate_audio(full_text, detected_lang)
                            with open(audio_file_path, "rb") as f:
                                audio_bytes = f.read()
                            st.audio(audio_bytes, format="audio/mp3")
                            st.download_button(
                                label="💾 Download Audiobook",
                                data=audio_bytes,
                                file_name="audiobook.mp3",
                                mime="audio/mp3",
                            )
                            # Cleanup audio file
                            os.unlink(audio_file_path)
                        except Exception as e:
                            st.error(f"Error generating audio: {e}")

            with btn_col2:
                st.caption("Quality may vary based on document complexity.")

        # Clean up PDF temp file after use
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
    else:
        st.info("Upload a PDF file or enter a PDF URL to get started.")


if __name__ == "__main__":
    main()
