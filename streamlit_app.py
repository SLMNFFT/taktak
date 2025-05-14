import streamlit as st
import cv2
import numpy as np
import pytesseract
from PIL import Image
from pypdf import PdfReader
from gtts import gTTS
import tempfile
import requests
import pdfplumber
import img2pdf
import os
from io import BytesIO
from pdf2image import convert_from_bytes
from streamlit_webrtc import webrtc_streamer, WebRtcStreamerContext
import av

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def handle_error(e, message="An error occurred"):
    st.error(f"{message}: {str(e)}")
    st.stop()

try:
    st.set_page_config(
        page_title="Doc2Audio Pro",
        layout="wide",
        page_icon="🎧",
        menu_items={
            'Get Help': 'https://doc2audio.help',
            'Report a bug': "https://github.com/doc2audio/issues",
            'About': "## AI Document to Audiobook Converter"
        }
    )
except Exception as e:
    handle_error(e, "Page configuration failed")

def safe_image_processing(img):
    try:
        img_gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(thresh)
    except Exception as e:
        handle_error(e, "Image processing error")

def video_frame_callback(frame):
    try:
        img = frame.to_ndarray(format="bgr24")
        processed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return av.VideoFrame.from_ndarray(thresh, format="bgr24")
    except Exception as e:
        st.warning(f"Frame processing skipped: {str(e)}")
        return frame

def document_processing_flow():
    st.markdown("""
        <div style="text-align: center; padding: 2rem; 
            background: linear-gradient(135deg, #25C9A5, #2B2D42); 
            border-radius: 15px;">
            <h1 style="color: white;">Doc2Audio Pro</h1>
            <p style="color: rgba(255,255,255,0.8);">Scan, Convert, Listen</p>
        </div>
    """, unsafe_allow_html=True)

    input_method = st.radio(
        "Input Method:",
        ["📷 Scan Document", "📁 Upload Files", "🌐 Web URL"],
        horizontal=True
    )

    content = None
    is_pdf = False

    try:
        if input_method == "📷 Scan Document":
            ctx = webrtc_streamer(
                key="doc-scan",
                mode=WebRtcStreamerContext.SENDONLY,
                media_stream_constraints={
                    "video": {"facingMode": "environment", "width": 1280, "height": 720},
                    "audio": False
                },
                video_frame_callback=video_frame_callback,
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
            )

            if ctx.video_receiver:
                if st.button("Capture Document"):
                    frame = ctx.video_receiver.get_frame()
                    if frame:
                        content = cv2.imencode('.jpg', frame.to_ndarray(format="bgr24"))[1].tobytes()

        elif input_method == "📁 Upload Files":
            uploaded_file = st.file_uploader(
                "Upload Document", 
                type=["pdf", "jpg", "png", "jpeg"]
            )
            if uploaded_file:
                content = uploaded_file.read()
                is_pdf = uploaded_file.type == "application/pdf"

        elif input_method == "🌐 Web URL":
            url = st.text_input("Document URL")
            if url:
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    content = response.content
                    is_pdf = url.lower().endswith('.pdf')
                except Exception as e:
                    handle_error(e, "URL download failed")

        if content:
            process_and_preview(content, is_pdf)

    except Exception as e:
        handle_error(e, "Application error")

def process_and_preview(content, is_pdf):
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("Extracted Text", expanded=True):
            try:
                text = process_content(content, is_pdf)
                st.markdown(f"""
                    <div style="
                        background: #1a1a1a;
                        padding: 1rem;
                        border-radius: 8px;
                        max-height: 60vh;
                        overflow-y: auto;
                    ">
                        <pre style="white-space: pre-wrap;">{text[:5000] + ('...' if len(text)>5000 else '')}</pre>
                    </div>
                """, unsafe_allow_html=True)
                generate_audio(text)
            except Exception as e:
                handle_error(e, "Text processing failed")

    with col2:
        with st.expander("Document Preview", expanded=True):
            try:
                if is_pdf:
                    with pdfplumber.open(BytesIO(content)) as pdf:
                        st.image(pdf.pages[0].to_image(resolution=150).original, use_column_width=True)
                else:
                    st.image(Image.open(BytesIO(content)), use_column_width=True)
            except Exception as e:
                st.warning(f"Preview unavailable: {str(e)}")

def process_content(content, is_pdf):
    try:
        if is_pdf:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(content)
                try:
                    text = "".join(page.extract_text() or "" for page in PdfReader(tmp_file.name).pages)
                    if not text.strip():
                        raise Exception("No text found in PDF")
                except:
                    text = "\n\n".join(pytesseract.image_to_string(safe_image_processing(img)) 
                                    for img in convert_from_bytes(content))
                os.remove(tmp_file.name)
                return text
        else:
            return pytesseract.image_to_string(safe_image_processing(Image.open(BytesIO(content))))
    except Exception as e:
        handle_error(e, "Content processing failed")

def generate_audio(text):
    st.sidebar.header("Audio Settings")
    lang = st.sidebar.text_input("Language", "en")
    speed = st.sidebar.select_slider("Speed", ["Slow", "Normal", "Fast"], "Normal")
    
    if st.sidebar.button("Generate Audiobook"):
        try:
            tts = gTTS(text=text, lang=lang, slow=(speed == "Slow"))
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                tts.save(f.name)
                st.audio(f.name)
                st.download_button(
                    "Download Audiobook",
                    data=open(f.name, "rb"),
                    file_name="document_audio.mp3"
                )
        except Exception as e:
            handle_error(e, "Audio generation failed")

if __name__ == "__main__":
    document_processing_flow()