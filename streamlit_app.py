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

# Configure Tesseract path (auto-detection)
try:
    pytesseract.pytesseract.tesseract_cmd = st.secrets.get("TESSERACT_PATH", "/usr/bin/tesseract")
except Exception as e:
    st.error(f"Tesseract configuration error: {str(e)}")

st.set_page_config(
    page_title="Doc2Audio Pro",
    layout="centered",
    page_icon="🔊",
    menu_items={
        'Get Help': 'https://doc2audio.help',
        'Report a bug': "https://github.com/doc2audio/issues",
        'About': "## AI-Powered Document to Audiobook Converter"
    }
)

def enhance_image(img):
    """Optimized image processing pipeline"""
    try:
        img_np = np.array(img.convert('L'))  # Convert to grayscale
        img_np = cv2.medianBlur(img_np, 3)
        _, thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(thresh)
    except Exception as e:
        st.error(f"Image enhancement failed: {str(e)}")
        return img

def create_searchable_pdf(images):
    """Robust PDF creation with OCR"""
    try:
        enhanced_images = [enhance_image(img) for img in images]
        pdf_bytes = img2pdf.convert([img.convert("RGB") for img in enhanced_images])
        
        # OCR processing
        ocr_text = []
        for img in enhanced_images:
            text = pytesseract.image_to_string(img)
            ocr_text.append(text)
        
        return pdf_bytes, "\n\n".join(ocr_text)
    except Exception as e:
        st.error(f"PDF creation error: {str(e)}")
        return None, ""

def extract_text_content(pdf_bytes):
    """Hybrid text extraction with fallback"""
    try:
        # Try standard PDF text extraction
        reader = PdfReader(BytesIO(pdf_bytes))
        text = "".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return text
        
        # Fallback to OCR
        images = convert_from_bytes(pdf_bytes)
        return "\n\n".join(pytesseract.image_to_string(enhance_image(img)) for img in images)
    
    except Exception as e:
        st.error(f"Text extraction failed: {str(e)}")
        return ""

def main():
    st.title("📖 Doc2Audio Pro")
    st.write("Convert documents to audiobooks with AI-powered OCR")
    
    input_method = st.radio(
        "Select input type:",
        ["📁 Upload PDF", "🌐 Web PDF", "📷 Scan Pages"],
        horizontal=True
    )
    
    pdf_content = None
    scanned_pages = []

    if input_method == "📷 Scan Pages":
        try:
            from camera_input import camera_input
            col1, col2 = st.columns([2, 1])
            
            with col1:
                img_data = camera_input("Capture Document")
                if img_data:
                    img = Image.open(BytesIO(img_data))
                    scanned_pages.append(img)
            
            with col2:
                if scanned_pages:
                    st.subheader("Scanned Pages")
                    for idx, page in enumerate(scanned_pages):
                        st.image(page, use_column_width=True)
                        if st.button(f"Remove Page {idx+1}", key=f"del_{idx}"):
                            scanned_pages.pop(idx)
                            st.rerun()
                    
                    if st.button("✨ Finalize PDF"):
                        with st.spinner("Creating searchable PDF..."):
                            pdf_content, _ = create_searchable_pdf(scanned_pages)
        
        except ImportError:
            st.error("Camera support requires extra setup. Upload images instead.")
            uploaded_images = st.file_uploader(
                "Upload Document Images", 
                type=["jpg", "png", "jpeg"],
                accept_multiple_files=True
            )
            if uploaded_images:
                scanned_pages = [Image.open(img) for img in uploaded_images]

    elif input_method == "📁 Upload PDF":
        pdf_file = st.file_uploader("Upload PDF Document", type=["pdf"])
        if pdf_file:
            pdf_content = pdf_file.read()

    elif input_method == "🌐 Web PDF":
        pdf_url = st.text_input("Enter PDF URL")
        if pdf_url:
            try:
                response = requests.get(pdf_url, timeout=10)
                response.raise_for_status()
                pdf_content = response.content
            except Exception as e:
                st.error(f"Download failed: {str(e)}")

    if pdf_content:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(pdf_content)
            pdf_path = tmp_pdf.name
        
        try:
            with st.spinner("Analyzing document..."):
                text_content = extract_text_content(pdf_content)
                lang = detect(text_content[:500]) if text_content else "en"
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.subheader("Extracted Text")
                st.markdown(f"""
                    <div style="
                        background: #1a1a1a;
                        padding: 1rem;
                        border-radius: 8px;
                        max-height: 50vh;
                        overflow-y: auto;
                    ">
                        <pre style="white-space: pre-wrap;">{text_content[:10000] + ('...' if len(text_content)>10000 else '')}</pre>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.subheader("Document Preview")
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        page = pdf.pages[0]
                        img = page.to_image(resolution=150).original
                        st.image(img, use_column_width=True)
                except Exception as e:
                    st.error(f"Preview unavailable: {str(e)}")
            
            st.sidebar.header("Audiobook Settings")
            lang = st.sidebar.text_input("Language Code", value=lang)
            voice_speed = st.sidebar.select_slider("Narration Speed", ["Slow", "Normal", "Fast"], value="Normal")
            
            if st.sidebar.button("Generate Audiobook", type="primary"):
                if not text_content.strip():
                    st.error("No text found in document")
                else:
                    with st.spinner("Generating audio..."):
                        try:
                            tts = gTTS(
                                text=text_content,
                                lang=lang,
                                slow=(voice_speed == "Slow")
                            )
                            audio_bytes = BytesIO()
                            tts.write_to_fp(audio_bytes)
                            audio_bytes.seek(0)
                            
                            st.audio(audio_bytes, format="audio/mp3")
                            st.download_button(
                                "Download Audiobook",
                                data=audio_bytes,
                                file_name="audiobook.mp3",
                                mime="audio/mpeg"
                            )
                        except Exception as e:
                            st.error(f"Audio generation failed: {str(e)}")
        
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

if __name__ == "__main__":
    main()