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

# Configure Tesseract path (update for your system)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

st.set_page_config(
    page_title="Doc2Audio Pro",
    layout="wide",
    page_icon="🎧",
    menu_items={
        'Get Help': 'https://doc2audio.help',
        'Report a bug': "https://github.com/doc2audio/issues",
        'About': "## AI-Powered Document to Audiobook Converter"
    }
)

def enhance_image(img):
    """Optimized document enhancement pipeline"""
    try:
        # Convert to grayscale and apply adaptive thresholding
        img_np = np.array(img.convert('L'))
        img_np = cv2.medianBlur(img_np, 3)
        _, thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(thresh)
    except Exception as e:
        st.error(f"Image processing error: {str(e)}")
        return img

def video_frame_callback(frame):
    """Real-time document processing for camera feed"""
    img = frame.to_ndarray(format="bgr24")
    processed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return av.VideoFrame.from_ndarray(thresh, format="bgr24")

def process_document(content, is_pdf=True):
    """Unified document processing with OCR fallback"""
    try:
        if is_pdf:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(content)
                pdf_path = tmp_file.name
            
            text = ""
            try:
                reader = PdfReader(pdf_path)
                text = "".join(page.extract_text() or "" for page in reader.pages)
                if not text.strip():
                    raise Exception("No text found, using OCR")
            except:
                images = convert_from_bytes(content)
                text = "\n\n".join(pytesseract.image_to_string(enhance_image(img)) for img in images)
            
            os.remove(pdf_path)
            return text
        else:
            img = Image.open(BytesIO(content))
            return pytesseract.image_to_string(enhance_image(img))
    except Exception as e:
        st.error(f"Processing error: {str(e)}")
        return ""

def main():
    st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #25C9A5, #2B2D42); border-radius: 15px;">
            <h1 style="color: white;">Doc2Audio Pro</h1>
            <p style="color: rgba(255,255,255,0.8);">Transform documents into audiobooks</p>
        </div>
    """, unsafe_allow_html=True)

    # Input Method Selection
    input_method = st.radio(
        "Choose input method:",
        ["📷 Document Scanner", "📁 File Upload", "🌐 Web URL"],
        horizontal=True,
        label_visibility="collapsed"
    )

    content = None
    is_pdf = False
    captured_image = None

    # Document Scanner Section
    if input_method == "📷 Document Scanner":
        st.header("Document Scanner")
        
        # Configure for rear camera preference
        media_stream_constraints = {
            "video": {
                "facingMode": "environment",  # Force rear camera
                "width": {"ideal": 1280},
                "height": {"ideal": 720}
            },
            "audio": False
        }

        ctx = webrtc_streamer(
            key="document-scanner",
            mode=WebRtcStreamerContext.SENDONLY,
            media_stream_constraints=media_stream_constraints,
            video_frame_callback=video_frame_callback,
            rtc_configuration={"iceServers": []}
        )

        if ctx.video_receiver:
            if st.button("Capture Document Page"):
                frame = ctx.video_receiver.get_frame()
                if frame is not None:
                    captured_image = frame.to_ndarray(format="bgr24")
                    content = cv2.imencode('.jpg', captured_image)[1].tobytes()
                    st.session_state.captured_image = content

        if 'captured_image' in st.session_state:
            st.image(st.session_state.captured_image, caption="Captured Document", use_column_width=True)
            if st.button("Retake Photo"):
                del st.session_state.captured_image
                st.rerun()

    # File Upload Section
    elif input_method == "📁 File Upload":
        uploaded_file = st.file_uploader(
            "Upload document (PDF/IMG)", 
            type=["pdf", "jpg", "png", "jpeg"],
            label_visibility="collapsed"
        )
        if uploaded_file:
            content = uploaded_file.read()
            is_pdf = uploaded_file.type == "application/pdf"

    # Web URL Section
    elif input_method == "🌐 Web URL":
        url = st.text_input("Enter document URL", "")
        if url:
            try:
                response = requests.get(url)
                response.raise_for_status()
                content = response.content
                is_pdf = url.lower().endswith('.pdf')
            except Exception as e:
                st.error(f"Download error: {str(e)}")

    # Document Processing and Preview
    if content:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.expander("📜 Extracted Text", expanded=True):
                with st.spinner("Processing document..."):
                    text_content = process_document(content, is_pdf)
                    if text_content:
                        st.markdown(f"""
                            <div style="
                                background: #1a1a1a;
                                padding: 1rem;
                                border-radius: 8px;
                                max-height: 60vh;
                                overflow-y: auto;
                            ">
                                <pre style="white-space: pre-wrap;">{text_content[:5000] + ('...' if len(text_content)>5000 else '')}</pre>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("No text found in document")

        with col2:
            with st.expander("🖼️ Document Preview", expanded=True):
                try:
                    if is_pdf:
                        with pdfplumber.open(BytesIO(content)) as pdf:
                            page = pdf.pages[0]
                            img = page.to_image(resolution=150).original
                            st.image(img, use_column_width=True)
                    else:
                        img = Image.open(BytesIO(content))
                        st.image(img, use_column_width=True)
                except Exception as e:
                    st.error(f"Preview error: {str(e)}")

        # Audiobook Generation
        st.sidebar.header("Audio Settings")
        lang = st.sidebar.text_input("Language Code", value="en")
        speed = st.sidebar.select_slider("Narration Speed", ["Slow", "Normal", "Fast"], value="Normal")
        
        if st.sidebar.button("🎧 Generate Audiobook", type="primary"):
            if text_content.strip():
                with st.spinner("Generating audio..."):
                    try:
                        tts = gTTS(
                            text=text_content,
                            lang=lang,
                            slow=(speed == "Slow")
                        )
                        audio_bytes = BytesIO()
                        tts.write_to_fp(audio_bytes)
                        audio_bytes.seek(0)
                        
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            "💾 Download Audiobook",
                            data=audio_bytes,
                            file_name="audiobook.mp3",
                            mime="audio/mpeg"
                        )
                    except Exception as e:
                        st.error(f"Audio generation failed: {str(e)}")
            else:
                st.error("No text content to convert")

if __name__ == "__main__":
    main()