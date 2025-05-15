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

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
[data-testid="stColumns"] {
    display: flex;
    align-items: stretch;
    gap: 2rem;
}
.preview-card {
    background: #1A1B2F;
    border-radius: 15px;
    padding: 1.5rem;
    height: 100% !important;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 15px rgba(10, 10, 30, 0.5);
}
.preview-card:hover {
    background: #252742;
}
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
}
.scroll-container::-webkit-scrollbar-thumb {
    background-color: #4e5aee;
    border-radius: 10px;
    border: 2px solid #1A1B2F;
}
.preview-image-container {
    display: grid;
    gap: 1rem;
    padding-bottom: 1rem;
}
.preview-image {
    background: #2B2D42;
    border-radius: 8px;
    padding: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    display: flex;
    flex-direction: column;
    align-items: center;
}
.preview-image img {
    border-radius: 6px;
    margin-bottom: 0.5rem;
    width: 100%;
    height: auto;
    object-fit: contain;
}
.preview-image p {
    text-align: center;
    color: #888;
    margin: 0;
    font-size: 0.9rem;
    font-style: italic;
}
body, pre {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #ddd;
    background-color: #0f1123;
}
pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 0.95rem;
    line-height: 1.4;
}
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
    tts = gTTS(text=text, lang=lang, slow=(rate < 1.0))
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
    text-align: center;
    font-weight: 600;
    margin-top: 0;
'>
🎧 PeePit Audiobook Generator
</h1>
""", unsafe_allow_html=True)

    pdf_file = st.file_uploader("📤 Upload your PDF to convert it into MP3", type=["pdf"])
    pdf_path = None

    if pdf_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            pdf_path = tmp.name

    if pdf_path:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        selected_pages = st.multiselect("📄 Select pages to include", list(range(1, total_pages + 1)), default=[1])

        if not selected_pages:
            st.error("Please select at least one valid page")
            return

        with st.spinner("🔍 Extracting text..."):
            full_text, ocr_pages = extract_text_from_pdf(pdf_path, selected_pages)
            if not full_text:
                st.error("No extractable text found.")
                return

        col_left, col_right = st.columns(2)

        # --- LEFT COLUMN ---
        with col_left:
            with st.expander("📜 Extracted Text", expanded=True):
                search_term = st.text_input("🔎 Search inside text", "")
                show_ocr = st.toggle("👁️ Include OCR pages", value=True)

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
                        filtered_text
                    )

                st.markdown(f"""
                    <div class="preview-card">
                        <div class="scroll-container">
                            <pre>{filtered_text}</pre>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                st.download_button("📥 Download Extracted Text", full_text, file_name="extracted_text.txt")

            # --- Audio Settings ---
            st.subheader("🔊 Audio Settings")
            lang = st.selectbox("Language", ["en", "fr", "de", "es"])
            speed = st.select_slider("Speed", ["slow", "normal", "fast"], value="normal")
            gender = st.selectbox("Voice", ["male", "female"])  # Currently unused with gTTS

            rate_map = {"slow": 0.8, "normal": 1.0, "fast": 1.3}
            rate = rate_map[speed]

            if st.button("🎧 Generate Audio"):
                with st.spinner("Generating audio..."):
                    audio_path = generate_audio(full_text, lang=lang, rate=rate, gender=gender)
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button("📥 Download Audio", audio_bytes, file_name="audiobook.mp3")

        # --- RIGHT COLUMN ---
        with col_right:
            with st.expander("🖼️ Visual Preview", expanded=True):
                st.markdown("""<div class="preview-card"><div class="scroll-container"><div class="preview-image-container">""", unsafe_allow_html=True)
                rendered_images = []
                with pdfplumber.open(pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_num = i + 1
                        if page_num in selected_pages:
                            img = page.to_image(resolution=150).original
                            rendered_images.append(img)
                            img_base64 = pil_to_base64(img)
                            st.markdown(f"""
                                <div class="preview-image">
                                    <img src="data:image/png;base64,{img_base64}" style="width:100%; height:auto;"/>
                                    <p>Page {page_num}</p>
                                </div>
                            """, unsafe_allow_html=True)
                st.markdown("</div></div></div>", unsafe_allow_html=True)

                if rendered_images:
                    preview_pdf = save_images_as_pdf(rendered_images)
                    with open(preview_pdf, "rb") as f:
                        st.download_button("📥 Download Previews as PDF", f.read(), file_name="previews.pdf", mime="application/pdf")

    else:
        st.info("📤 Upload a PDF file to begin.")

# --- RUN APP ---
if __name__ == "__main__":
    main()
