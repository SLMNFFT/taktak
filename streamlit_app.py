import streamlit as st
import re
import tempfile
import base64
import pdfplumber
from pypdf import PdfReader
from PIL import Image
from fpdf import FPDF
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

/* ===== Center content vertically and horizontally when empty ===== */
.centered-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 80vh;
    gap: 1rem;
}

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
    # gTTS does not support rate or gender control, ignoring those params for now
    tts = gTTS(text=text, lang=lang, slow=(rate<1.0))
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
    pdf_file = st.file_uploader("Turn your PDF to a MP3 file. (PDF images and image PDFs are not supported)", type=["pdf"])
    pdf_url = st.text_input("Or enter a PDF URL")

    if not pdf_file and not pdf_url:

        # Show uploader + URL input centered using columns hack
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.file_uploader("Turn your PDF to a MP3 file. (PDF images and image PDFs are not supported)", type=["pdf"], key="centered_uploader")
            st.text_input("Or enter a PDF URL", key="centered_url")
        return

    # If file uploaded or URL provided, process file as before
    pdf_path = None
    if pdf_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            pdf_path = tmp.name
    # (For URL: you can add downloading logic here if you want, currently ignored)

    if pdf_path:
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
        '>🎧 PeePit</h1>
        """, unsafe_allow_html=True)

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
                    show_ocr = st.checkbox("👁️ Show OCR text", value=True)

                    if not show_ocr and ocr_pages:
                        # Remove OCR pages text from display
                        pattern = r"(--- Page (\d+).*?)(?=--- Page \d+|$)"
                        matches = re.findall(pattern, full_text, re.DOTALL)
                        filtered_text = ""
                        for full_match, page_num_str in matches:
                            page_num = int(page_num_str)
                            if page_num not in ocr_pages:
                                filtered_text += full_match
                        display_text = filtered_text
                    else:
                        display_text = full_text

                    if search_term:
                        display_text = re.sub(
                            f"(?i)({re.escape(search_term)})",
                            r"<mark style='background-color:yellow'>\1</mark>",
                            display_text
                        )

                    st.markdown(f"""
                        <div class="preview-card">
                            <div class="scroll-container">
                                <pre>{display_text}</pre>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    st.download_button("📥 Download Extracted Text", full_text, file_name="extracted_text.txt")

                # Audio Settings
                st.subheader("🔊 Audio Settings")
                col1, col2, col3 = st.columns(3)
                with col1:
                    language = st.selectbox("Language", ["en", "fr", "de", "es"])
                with col2:
                    speed = st.select_slider("Speed", ["slow", "normal", "fast"], value="normal")
                with col3:
                    voice = st.selectbox("Voice", ["male", "female"])

                rate_map = {"slow": 0.75, "normal": 1.0, "fast": 1.25}
                audio_path = generate_audio(full_text, lang=language, rate=rate_map[speed], gender=voice)
                with open(audio_path, "rb") as f_audio:
                    audio_bytes = f_audio.read()

                st.audio(audio_bytes, format="audio/mp3")

                st.download_button(
                    label="📥 Download MP3 Audio",
                    data=audio_bytes,
                    file_name="audiobook.mp3",
                    mime="audio/mp3",
                )

            # --- RIGHT COLUMN: PREVIEW & IMAGES ---
            with col_right:
                with st.expander("🖼️ Preview Images", expanded=True):
                    images = []
                    for i in selected_pages:
                        try:
                            page = reader.pages[i - 1]
                            if "/XObject" in page["/Resources"]:
                                xObject = page["/Resources"]["/XObject"].get_object()
                                for obj in xObject:
                                    if xObject[obj]["/Subtype"] == "/Image":
                                        size = (xObject[obj]["/Width"], xObject[obj]["/Height"])
                                        data = xObject[obj].get_data()
                                        mode = "RGB"
                                        if xObject[obj]["/ColorSpace"] == "/DeviceCMYK":
                                            mode = "CMYK"
                                        img = Image.frombytes(mode, size, data)
                                        images.append(img)
                        except Exception as e:
                            st.warning(f"Could not extract images from page {i}: {e}")

                    if images:
                        st.markdown('<div class="preview-image-container">', unsafe_allow_html=True)
                        for idx, img in enumerate(images[:10]):  # Show max 10 images
                            img = img.resize((200, int(200 * img.height / img.width)))
                            img_b64 = pil_to_base64(img)
                            st.markdown(f"""
                            <div class="preview-image">
                                <img src="data:image/png;base64,{img_b64}" alt="Page Image {idx + 1}">
                                <p>Page Image {idx + 1}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        pdf_preview_path = save_images_as_pdf(images)
                        with open(pdf_preview_path, "rb") as f_pdf:
                            pdf_bytes = f_pdf.read()

                        st.download_button(
                            "📥 Download Preview Images PDF",
                            pdf_bytes,
                            file_name="preview_images.pdf",
                            mime="application/pdf",
                        )
                    else:
                        st.info("No images found in the selected pages.")

        # Cleanup temp files
        if os.path.exists(audio_path):
            os.remove(audio_path)

if __name__ == "__main__":
    main()
