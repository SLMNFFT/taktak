import streamlit as st
import re
import tempfile
import base64
import pdfplumber
from pypdf import PdfReader
from PIL import Image
from fpdf import FPDF
from gtts import gTTS
import io
import os

st.set_page_config(
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
)

st.markdown("""
<style>
/* ===== Streamlit Columns Flex Fix ===== */
[data-testid="stColumns"] {
    display: flex;
    align-items: stretch; /* equal height columns */
    gap: 2rem; /* space between columns */
}

/* ===== Preview Card Styling ===== */
.preview-card {
    background: #1A1B2F;
    border-radius: 15px;
    padding: 1.5rem;
    height: 100% !important; /* full height of the column */
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 15px rgba(10, 10, 30, 0.5);
    transition: background 0.3s ease;
}

.preview-card:hover {
    background: #252742;
}

/* ===== Scroll Container (for scrollable content) ===== */
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

/* ===== Preview Image Container (Grid of images) ===== */
.preview-image-container {
    display: grid;
    gap: 1rem; /* Reduced gap for tighter grid */
    padding-bottom: 1rem;
    margin-top: 0; /* Remove any top margin */
}

/* ===== Individual Preview Image Card ===== */
.preview-image {
    background: #2B2D42;
    border-radius: 8px;
    padding: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Remove top margin from the first preview image to eliminate gap */
.preview-image:first-child {
    margin-top: 0;
}

/* ===== Image Styling ===== */
.preview-image img {
    border-radius: 6px;
    margin-bottom: 0.5rem;
    width: 100%;
    height: auto;
    object-fit: contain;
    user-select: none;
}

/* ===== Caption under each image ===== */
.preview-image p {
    text-align: center;
    color: #888;
    margin: 0;
    font-size: 0.9rem;
    font-style: italic;
    user-select: none;
}

/* ===== General Body & Text Styling ===== */
body, pre {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #ddd;
    background-color: #0f1123;
}

/* Preformatted text scroll area styling */
pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 0.95rem;
    line-height: 1.4;
}

/* ===== Buttons, Inputs, Toggles (Streamlit default overrides can be added here) ===== */
/* Add your custom button/input styles here if needed */

/* ===== Responsive tweaks ===== */
@media (max-width: 768px) {
    [data-testid="stColumns"] {
        flex-direction: column;
    }
    .preview-card {
        height: auto !important;
        margin-bottom: 1rem;
    }
}

/* ===== Center initial screen ===== */
.centered-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 80vh;
    gap: 1rem;
    max-width: 480px;
    margin: 0 auto;
    text-align: center;
}
h1.centered-header {
    background: #2ecc71;
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    margin: 0;
    width: 100%;
}
.limit-text {
    font-size: 0.9rem;
    color: #bbb;
    margin-top: -12px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# --- HELPER FUNCTIONS ---

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
    tts = gTTS(text=text, lang=lang, slow=False)
    temp_audio_path = tempfile.mktemp(suffix=".mp3")
    tts.save(temp_audio_path)
    return temp_audio_path


def save_images_as_pdf(images):
    pdf = FPDF()
    for img in images:
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        image_path = "/tmp/temp_img.png"
        with open(image_path, "wb") as f:
            f.write(bio.read())
        pdf.add_page()
        pdf.image(image_path, x=10, y=10, w=pdf.w - 20)
    pdf_path = "/tmp/preview_images.pdf"
    pdf.output(pdf_path)
    return pdf_path


# --- MAIN APP ---

def main():
    pdf_file = st.file_uploader(
        label="Drag and drop file here",
        type=["pdf"],
        help="Limit 200MB per file • - Field"
    )
    pdf_url = st.text_input("Or enter a PDF URL")

    if not pdf_file and not pdf_url:
        # Show centered initial UI
        st.markdown("""
        <div class="centered-container">
            <h1 class="centered-header">Turn your PDF to a MP3 file. (PDF images and image PDFs are not supported)</h1>
            <div style="width: 100%; margin-top: 16px;">
                <!-- File uploader below -->
            </div>
            <div class="limit-text">Limit 200MB per file • - Field</div>
            <div style="width: 100%; margin-bottom: 12px;">
                <!-- URL input below -->
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show the file uploader and URL input again, centered with limited width
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.file_uploader(
                label="Drag and drop file here",
                type=["pdf"],
                help="Limit 200MB per file • - Field",
                key="centered_uploader"
            )
            st.text_input("Or enter a PDF URL", key="centered_url")

        return  # stop here, wait for input

    # --- If file or URL provided, continue with your app as before ---

    # If file uploaded, save temporarily
    pdf_path = None
    if pdf_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            pdf_path = tmp.name

    # TODO: For PDF URL, you could download the file to temp location here
    # For now, just ignore URL handling for brevity

    if pdf_path:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        selected_pages = st.multiselect(
            label="Select pages to convert to audio",
            options=list(range(1, total_pages + 1)),
            default=list(range(1, total_pages + 1)),
        )

        if selected_pages:
            text, ocr_pages = extract_text_from_pdf(pdf_path, selected_pages)
            if not text:
                st.warning("No extractable text found in the selected pages.")
                return

            st.text_area("Extracted Text Preview", text, height=300)

            if st.button("Generate MP3 Audio"):
                with st.spinner("Generating audio..."):
                    audio_path = generate_audio(text)
                    audio_file = open(audio_path, "rb").read()
                    st.audio(audio_file, format="audio/mp3")
                    st.success("Audio generated successfully!")

    else:
        st.info("Please upload a PDF file or enter a valid URL.")

if __name__ == "__main__":
    main()
