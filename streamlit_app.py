import streamlit as st
from pypdf import PdfReader
from langdetect import detect
from gtts import gTTS
import tempfile
import requests
import pdfplumber
from PIL import Image
import cv2
import numpy as np
from io import BytesIO
import os
import img2pdf
import pytesseract
from pdf2image import convert_from_bytes

# Configure Tesseract path (update for your OS)
# Windows example: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

st.set_page_config(
    page_title="Mogontia Audiobook",
    layout="wide",
    page_icon="🎧",
    menu_items={
        'Get Help': 'https://github.com/mogontia/audiobook-gen',
        'Report a bug': "https://github.com/mogontia/audiobook-gen/issues",
        'About': """
        ## 🎧 Mogontia Audiobook Generator 
        **Version 4.1**  
        Scan, OCR, and convert to audiobook  
        """
    }
)

# Modern UI Styles
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
        height: 100vh;
        overflow: hidden;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0;
        height: calc(100vh - 100px);
    }
    
    .header-gradient {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 1rem 2rem 2rem;
        margin: -1rem -2rem 1rem;
        border-radius: 0 0 20px 20px;
    }
    
    .upload-card {
        background: rgba(43, 45, 66, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .preview-card {
        background: #1A1B2F;
        border-radius: 15px;
        padding: 1rem;
        height: calc(100vh - 300px);
        display: flex;
        flex-direction: column;
    }
    
    .preview-content {
        flex: 1;
        overflow-y: auto;
        padding: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

def process_image(img):
    """Enhance scanned document image"""
    try:
        img_array = np.array(img.convert('RGB'))
        img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB))
    except Exception as e:
        st.error(f"Image processing error: {e}")
        return img

def images_to_searchable_pdf(images):
    """Convert images to searchable PDF with OCR"""
    try:
        pdf_bytes = img2pdf.convert([img.convert("RGB") for img in images])
        text_content = []
        
        for img in images:
            processed = process_image(img)
            text = pytesseract.image_to_string(processed)
            text_content.append(text)
        
        return pdf_bytes, "\n".join(text_content)
    except Exception as e:
        st.error(f"PDF creation failed: {e}")
        return None, ""

def extract_text(pdf_bytes):
    """Extract text from PDF (digital or scanned)"""
    try:
        # Try normal extraction first
        reader = PdfReader(BytesIO(pdf_bytes))
        text = "".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            raise Exception("No text found, using OCR")
        return text
    except Exception:
        # Fallback to OCR
        try:
            images = convert_from_bytes(pdf_bytes)
            return "\n".join(pytesseract.image_to_string(process_image(img)) for img in images)
        except Exception as e:
            st.error(f"OCR failed: {e}")
            return ""

def main():
    st.markdown("""
        <div class="header-gradient">
            <h1 style="color: white; margin: 0; font-size: 1.8rem;">Mogontia Audiobook</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">
                Scan documents ➔ Convert to audiobook
            </p>
        </div>
    """, unsafe_allow_html=True)

    input_method = st.radio(
        "Input method:",
        ["📁 Upload PDF", "🌐 PDF URL", "📷 Scan Document"],
        horizontal=True
    )

    pdf_bytes = None
    scanned_images = []

    if input_method == "📷 Scan Document":
        col1, col2 = st.columns([2, 1])
        with col1:
            try:
                from camera_input import camera_input
                img_data = camera_input("Take document photo")
                if img_data:
                    img = Image.open(BytesIO(img_data))
                    scanned_images.append(process_image(img))
            except ImportError:
                st.error("Camera input requires extra setup. Upload images instead.")
            except Exception as e:
                st.error(f"Camera error: {e}")
                
        with col2:
            if scanned_images:
                st.markdown("**Scanned Pages**")
                cols = st.columns(3)
                for idx, img in enumerate(scanned_images):
                    with cols[idx % 3]:
                        st.image(img, use_column_width=True)
                        if st.button(f"Remove {idx+1}", key=f"del_{idx}"):
                            scanned_images.pop(idx)
                            st.experimental_rerun()
                
                if st.button("Scan New Page"):
                    st.experimental_rerun()
                    
                if scanned_images and st.button("✨ Create PDF"):
                    with st.spinner("Creating searchable PDF..."):
                        pdf_bytes, ocr_text = images_to_searchable_pdf(scanned_images)
                        if pdf_bytes:
                            st.session_state.ocr_text = ocr_text

    elif input_method == "📁 Upload PDF":
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf_file:
            pdf_bytes = pdf_file.read()

    elif input_method == "🌐 PDF URL":
        url = st.text_input("PDF URL")
        if url:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                pdf_bytes = response.content
            except Exception as e:
                st.error(f"Error downloading PDF: {e}")

    if pdf_bytes:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_bytes)
                pdf_path = tmp_file.name
            
            with st.spinner("Extracting text..."):
                full_text = extract_text(pdf_bytes)
                detected_lang = detect(full_text[:500]) if full_text else "en"
            
            col1, col2 = st.columns(2)
            with col1:
                with st.expander("📜 Document Text", expanded=True):
                    st.markdown(f"""
                        <div class="preview-card">
                            <div class="preview-content">
                                <pre style="white-space: pre-wrap;">{full_text[:5000] + ('...' if len(full_text)>5000 else '')}</pre>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                with st.expander("🖼️ Preview", expanded=True):
                    try:
                        with pdfplumber.open(pdf_path) as pdf:
                            img = pdf.pages[0].to_image(resolution=150).original
                            st.image(img, use_column_width=True)
                    except Exception as e:
                        st.error(f"Preview error: {e}")

            st.sidebar.markdown("## Audiobook Settings")
            lang = st.sidebar.text_input("Language", value=detected_lang)
            slow = st.sidebar.checkbox("Slow narration")
            
            if st.sidebar.button("🎧 Generate Audiobook"):
                if not full_text.strip():
                    st.error("No text found to convert")
                else:
                    with st.spinner("Generating audio..."):
                        try:
                            tts = gTTS(full_text, lang=lang, slow=slow)
                            audio_bytes = BytesIO()
                            tts.write_to_fp(audio_bytes)
                            audio_bytes.seek(0)
                            
                            st.audio(audio_bytes, format="audio/mp3")
                            st.download_button(
                                "💾 Download MP3",
                                data=audio_bytes,
                                file_name="audiobook.mp3",
                                mime="audio/mp3"
                            )
                        except Exception as e:
                            st.error(f"Audio generation failed: {e}")

        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

if __name__ == "__main__":
    main()