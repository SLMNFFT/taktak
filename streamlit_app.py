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
from streamlit_webrtc import webrtc_streamer, WebRtcStreamerContext, VideoProcessorBase

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

st.set_page_config(
    page_title="DocScan Pro",
    layout="wide",
    page_icon="📖",
    menu_items={
        'Get Help': 'https://docscan.help',
        'Report a bug': "https://github.com/docscan/issues",
        'About': "## AI-Powered Document Scanner & Audiobook Converter"
    }
)

class DocumentScanner(VideoProcessorBase):
    def __init__(self):
        self.scanned_pages = []
        self.frame_count = 0

    def process_image(self, img):
        """Enhanced document processing pipeline"""
        try:
            img_np = np.array(img.convert('L'))  # Grayscale conversion
            img_np = cv2.medianBlur(img_np, 3)
            _, thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return Image.fromarray(thresh)
        except Exception as e:
            st.error(f"Image processing error: {str(e)}")
            return img

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        processed_img = self.process_image(Image.fromarray(img))
        
        # Save every 10th frame to prevent duplicates
        if self.frame_count % 10 == 0:
            self.scanned_pages.append(processed_img)
        
        self.frame_count += 1
        return processed_img

def create_searchable_pdf(images):
    """Create PDF with OCR text layer"""
    try:
        pdf_bytes = img2pdf.convert([img.convert("RGB") for img in images])
        return pdf_bytes
    except Exception as e:
        st.error(f"PDF creation error: {str(e)}")
        return None

def main():
    st.title("📖 DocScan Pro - Camera Scanner")
    
    # Initialize session state
    if 'scanned_pages' not in st.session_state:
        st.session_state.scanned_pages = []
    
    # WebRTC Camera Scanner
    ctx = webrtc_streamer(
        key="doc-scanner",
        video_processor_factory=DocumentScanner,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    # Capture scanned pages
    if ctx.video_processor:
        if st.button("📸 Capture Current Frame"):
            current_frame = ctx.video_processor.processed_frame
            if current_frame:
                st.session_state.scanned_pages.append(current_frame)
                st.rerun()

    # Display scanned pages
    if st.session_state.scanned_pages:
        st.subheader("Scanned Pages Preview")
        cols = st.columns(3)
        for idx, page in enumerate(st.session_state.scanned_pages):
            with cols[idx % 3]:
                st.image(page, use_column_width=True)
                if st.button(f"❌ Remove Page {idx+1}", key=f"remove_{idx}"):
                    st.session_state.scanned_pages.pop(idx)
                    st.rerun()

        # PDF Generation
        if st.button("📑 Generate Searchable PDF"):
            with st.spinner("Creating PDF..."):
                pdf_bytes = create_searchable_pdf(st.session_state.scanned_pages)
                if pdf_bytes:
                    st.session_state.pdf_bytes = pdf_bytes
                    st.success("PDF generated successfully!")
                    st.download_button(
                        "💾 Download PDF",
                        data=pdf_bytes,
                        file_name="scanned_document.pdf",
                        mime="application/pdf"
                    )

    # Existing PDF processing
    pdf_file = st.file_uploader("Or upload existing PDF", type=["pdf"])
    if pdf_file:
        # ... (rest of your existing PDF processing code)

if __name__ == "__main__":
    main()
