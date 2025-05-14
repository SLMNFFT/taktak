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
import base64
import os
import img2pdf
import pytesseract
from pdf2image import convert_from_bytes
from camera_input import camera_input

# Configure Tesseract path (update for your system)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux/Mac/WSL

st.set_page_config(
    page_title="Mogontia Audiobook",
    layout="wide",
    page_icon="🎧",
    menu_items={
        'Get Help': 'https://github.com/mogontia/audiobook-gen',
        'Report a bug': "https://github.com/mogontia/audiobook-gen/issues",
        'About': """
        ## 🎧 Mogontia Audiobook Generator 
        **Version 4.0**  
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
    
    /* ... (keep previous styles) ... */
    </style>
""", unsafe_allow_html=True)

def process_image(img):
    """Enhance scanned document image"""
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB))

def images_to_searchable_pdf(images):
    """Convert images to searchable PDF with OCR"""
    pdf_bytes = img2pdf.convert([img.convert("RGB") for img in images])
    
    # Add OCR text layer
    pdf_images = convert_from_bytes(pdf_bytes)
    text_content = []
    
    for img in pdf_images:
        processed = process_image(img)
        text = pytesseract.image_to_string(processed)
        text_content.append(text)
    
    return pdf_bytes, "\n".join(text_content)

def extract_text(pdf_bytes):
    """Extract text from PDF (digital or scanned)"""
    try:
        # Try normal extraction first
        reader = PdfReader(BytesIO(pdf_bytes))
        return "".join(page.extract_text() for page in reader.pages)
    except:
        # Fallback to OCR
        images = convert_from_bytes(pdf_bytes)
        return "\n".join(pytesseract.image_to_string(process_image(img)) for img in images)

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
            img_data = camera_input("Take document photo")
            if img_data:
                img = Image.open(BytesIO(img_data))
                scanned_images.append(process_image(img))
                
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
                    
                if scanned_images:
                    if st.button("✨ Create PDF"):
                        with st.spinner("Creating searchable PDF..."):
                            pdf_bytes, ocr_text = images_to_searchable_pdf(scanned_images)
                            st.session_state.ocr_text = ocr_text

    elif input_method == "📁 Upload PDF":
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf_file:
            pdf_bytes = pdf_file.read()

    elif input_method == "🌐 PDF URL":
        url = st.text_input("PDF URL")
        if url:
            try:
                response = requests.get(url)
                pdf_bytes = response.content
            except Exception as e:
                st.error(f"Error downloading PDF: {e}")

    if pdf_bytes:
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
                with pdfplumber.open(pdf_path) as pdf:
                    img = pdf.pages[0].to_image(resolution=150).original
                    img_base64 = base64.b64encode(img.convert("RGB").tobytes()).decode()
                    st.image(img, use_column_width=True)

        st.sidebar.markdown("## Audiobook Settings")
        lang = st.sidebar.text_input("Language", value=detected_lang)
        slow = st.sidebar.checkbox("Slow narration")
        
        if st.sidebar.button("🎧 Generate Audiobook"):
            with st.spinner("Generating audio..."):
                try:
                    tts = gTTS(full_text, lang=lang, slow=slow)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                        tts.save(f.name)
                        st.audio(f.name)
                        st.download_button(
                            "💾 Download MP3",
                            data=open(f.name, "rb"),
                            file_name="audiobook.mp3"
                        )
                except Exception as e:
                    st.error(f"Audio generation failed: {e}")

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    main()