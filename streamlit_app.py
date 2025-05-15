import streamlit as st
import re
import tempfile
import base64
import pdfplumber
from pypdf import PdfReader
from PIL import Image
from fpdf import FPDF
import pyttsx3
import io
from gtts import gTTS
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
    justify-content: center; /* Center the columns horizontally */
}

/* ===== General Body Styling ===== */
body, pre {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #ddd;
    background-color: #0f1123;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh; /* Full viewport height */
    margin: 0;
}

/* Main Content Container */
.main-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 20px;
    height: 100%;
    width: 100%;
    text-align: center;
}

/* ===== Streamlit Expanders Style ===== */
.st-expanderHeader {
    background-color: #2ecc71 !important;
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

/* ===== Buttons, Inputs, Toggles (Streamlit default overrides can be added here) ===== */

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
    st.markdown("""
<h1 style='
    background: #2ecc71;
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    font-weight: 600;
    margin-top: 0;
'>
🎧 PeePit
</h1>
""", unsafe_allow_html=True)

    pdf_file = st.file_uploader("Turn your PDF to a MP3 file.  (PDF images and image PDFs are not supported)", type=["pdf"])
    pdf_url = st.text_input("Or enter a PDF URL")

    pdf_path = None
    if pdf_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            pdf_path = tmp.name

    if pdf_path:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        selected_pages = st.multiselect("Select pages to process", list(range(1, total_pages + 1)), default=[1])

        if not selected_pages:
            st.error("Please select at least one valid page")
            return

        with st.spinner("🔍 Analyzing document..."):
            full_text, ocr_pages = extract_text_from_pdf(pdf_path, selected_pages)
            if not full_text:
                st.error("No extractable text found in selected pages")
                return

            col_left, col_right = st.columns(2)

            # --- LEFT COLUMN: TEXT + AUDIO ---
            with col_left:
                with st.expander("📜 Extracted Text", expanded=True):
                    search_term = st.text_input("🔎 Search within text", "")
                    show_ocr = st.toggle("👁️ Show OCR text", value=True)

                    if not show_ocr and ocr_pages:
                        pattern = r"--- Page (\d+).*?(?=(--- Page |\Z))"
                        filtered = re.findall(pattern, full_text, re.DOTALL)
                        filtered_text = "\n\n".join(
                            section for section, _ in filtered if int(section) not in ocr_pages
                        )
                    else:
                        filtered_text = full_text

                    if search_term:
                        filtered_text = re.sub(
                            f"(?i)({re.escape(search_term)})",
                            r"<mark style='background-color:yellow'>\1</mark>",
                            filtered_text,
                            flags=re.DOTALL,
                        )

                    st.markdown(f"<div class='scroll-container'>{filtered_text}</div>", unsafe_allow_html=True)

                    audio_file = generate_audio(filtered_text)
                    st.audio(audio_file)

            # --- RIGHT COLUMN: PREVIEW CARD ---
            with col_right:
                with st.expander("📸 Preview Images"):
                    preview_images = []

                    for page_num in selected_pages:
                        page = reader.pages[page_num - 1]
                        images = page.extract_images()
                        for img in images:
                            image_data = img['image']
                            image = Image.open(io.BytesIO(image_data))
                            preview_images.append(image)

                    preview_pdf = save_images_as_pdf(preview_images)
                    with open(preview_pdf, "rb") as f:
                        st.download_button(
                            "📥 Download Preview PDF", f, file_name="preview_images.pdf"
                        )

                    if preview_images:
                        st.write("📷 Images found in the document:")
                        for i, img in enumerate(preview_images, 1):
                            st.image(img, width=150, caption=f"Page {i}")
                    else:
                        st.write("No images found in the selected pages")

if __name__ == "__main__":
    main()
