import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import os
import tempfile
from fpdf import FPDF
import img2pdf
import base64
import io

# OCR class to capture frames from webcam and process
class DocumentScanner(VideoProcessorBase):
    def __init__(self):
        self.result_image = None

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        self.result_image = image
        return av.VideoFrame.from_ndarray(image, format="bgr24")

# Convert image list to a searchable PDF
def create_searchable_pdf(images):
    pdf = FPDF()
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img)
        text = pytesseract.image_to_string(pil_img)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img_file:
            pil_img.save(temp_img_file.name)
            pdf.add_page()
            pdf.image(temp_img_file.name, x=10, y=10, w=190)
            os.unlink(temp_img_file.name)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf_file:
        pdf.output(temp_pdf_file.name)
        return temp_pdf_file.name

# Process uploaded PDF
def process_uploaded_pdf(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_file.read())
        images = convert_from_path(temp_pdf.name)
        text_output = ""
        for image in images:
            text_output += pytesseract.image_to_string(image) + "\n"
        os.unlink(temp_pdf.name)
        return text_output

# Main Streamlit app logic
def main():
    st.title("📄 Document Scanner & OCR Tool")
    st.markdown("Scan documents using webcam or upload PDFs for OCR.")

    mode = st.radio("Select Mode", ["Webcam Scan", "Upload PDF"])

    if mode == "Webcam Scan":
        st.write("📷 Capture document using webcam")
        ctx = webrtc_streamer(key="scanner", video_processor_factory=DocumentScanner)
        if ctx.video_processor and ctx.video_processor.result_image is not None:
            st.image(ctx.video_processor.result_image, caption="Captured Image")
            if st.button("Extract Text"):
                img = ctx.video_processor.result_image
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                text = pytesseract.image_to_string(pil_img)
                st.text_area("Extracted Text", text, height=300)

            if st.button("Download as Searchable PDF"):
                searchable_pdf = create_searchable_pdf([ctx.video_processor.result_image])
                with open(searchable_pdf, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="scanned_document.pdf">📥 Download PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                os.unlink(searchable_pdf)

    elif mode == "Upload PDF":
        pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if pdf_file is not None:
            with st.spinner("Processing..."):
                text = process_uploaded_pdf(pdf_file)
                st.text_area("Extracted Text", text, height=300)

# 🟩 This part must be correctly indented!
if __name__ == "__main__":
    main()
