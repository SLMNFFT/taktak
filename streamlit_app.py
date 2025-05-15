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
import requests

st.set_page_config(
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
)

st.markdown("""
<style>
/* Your CSS styles here, unchanged... */
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
    transition: background 0.3s ease;
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
    border-radius: 10px;
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
    margin-top: 0;
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
.preview-image:first-child {
    margin-top: 0;
}
.preview-image img {
    border-radius: 6px;
    margin-bottom: 0.5rem;
    width: 100%;
    height: auto;
    object-fit: contain;
    user-select: none;
}
.preview-image p {
    text-align: center;
    color: #888;
    margin: 0;
    font-size: 0.9rem;
    font-style: italic;
    user-select: none;
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
.centered-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 80vh;
    gap: 1rem;
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
    # gTTS does not support rate or gender, ignoring those params for now
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
        image_path = tempfile.mktemp(suffix=".png")
        with open(image_path, "wb") as f:
            f.write(bio.read())
        pdf.add_page()
        pdf.image(image_path, x=10, y=10, w=pdf.w - 20)
        os.remove(image_path)
    pdf_path = tempfile.mktemp(suffix=".pdf")
    pdf.output(pdf_path)
    return pdf_path

def download_pdf(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_file.write(resp.content)
        tmp_file.close()
        return tmp_file.name
    except Exception as e:
        st.error(f"Failed to download PDF from URL: {e}")
        return None

def main():
    st.title("🎧 Peepit Audiobook")

    pdf_file = st.file_uploader("Upload a PDF file (text-based PDFs only)", type=["pdf"])
    pdf_url = st.text_input("Or enter a PDF URL")

    if not pdf_file and not pdf_url:
        # Centered layout before upload
        st.markdown("""
        <div class="centered-container">
            <h1 style='
                background: #2ecc71;
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                font-weight: 600;
                margin: 0;
                width: 100%;
                max-width: 480px;
            '>🎧 PeePit</h1>
            <div style="width: 100%; max-width: 480px;">
                <p style="color: #ddd; text-align:center;">Upload a PDF file or enter a URL to get started</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    pdf_path = None
    if pdf_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            pdf_path = tmp.name
    elif pdf_url:
        pdf_path = download_pdf(pdf_url)

    if not pdf_path:
        st.warning("Please upload a valid PDF file or enter a valid URL to continue.")
        return

    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
        return

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
                        filtered_text += full_match + "\n\n"
                text_to_show = filtered_text.strip()
            else:
                text_to_show = full_text

            if search_term:
                # Highlight matches case-insensitive
                safe_term = re.escape(search_term)
                highlight_html = re.sub(f"({safe_term})", r'<mark>\1</mark>', text_to_show, flags=re.I)
                st.markdown(f"<pre style='color:#ddd;background:#0f1123;padding:10px;border-radius:8px;white-space:pre-wrap;'>{highlight_html}</pre>", unsafe_allow_html=True)
            else:
                st.text_area("Extracted text", value=text_to_show, height=320)

        lang = st.selectbox("Select language", options=["en", "es", "fr", "de"], index=0)
        gender = st.selectbox("Select gender (note: gTTS ignores this)", options=["male", "female"])
        rate = st.slider("Select speed", 0.5, 2.0, 1.0, 0.1)

        audio_path = None
        if st.button("🎙️ Generate Audio"):
            with st.spinner("Converting text to speech..."):
                audio_path = generate_audio(full_text, lang=lang, rate=rate, gender=gender)
            st.success("Audio generated!")
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
            # Optionally clean up audio file
            # os.remove(audio_path)

    # --- RIGHT COLUMN: IMAGE PREVIEW ---
    with col_right:
        with st.expander("🖼️ Preview Images from PDF", expanded=True):
            images = []
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for p in selected_pages:
                        if 1 <= p <= len(pdf.pages):
                            page = pdf.pages[p - 1]
                            imgs = page.images
                            if imgs:
                                for img_dict in imgs:
                                    try:
                                        # pdfplumber coordinates: x0, top, x1, bottom
                                        # Crop in correct order: (x0, top, x1, bottom)
                                        cropped_img = page.crop((img_dict["x0"], img_dict["top"], img_dict["x1"], img_dict["bottom"])).to_image(resolution=150).original
                                        images.append(cropped_img)
                                    except Exception as e:
                                        st.warning(f"Failed to crop image on page {p}: {e}")
            except Exception as e:
                st.warning(f"Failed to extract images: {e}")

            if images:
                st.write(f"Found {len(images)} images in selected pages.")
                grid_cols = st.columns(3)
                for i, img in enumerate(images):
                    with grid_cols[i % 3]:
                        st.image(img, use_column_width=True)
            else:
                st.info("No images found in the selected pages.")

        if images:
            if st.button("🖼️ Export all images as PDF"):
                export_pdf_path = save_images_as_pdf(images)
                with open(export_pdf_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="exported_images.pdf">Download PDF with images</a>'
                st.markdown(href, unsafe_allow_html=True)
                # Optionally remove file after download
                # os.remove(export_pdf_path)

    # Cleanup temp file on exit or next run (optional)
    # if pdf_path and os.path.exists(pdf_path):
    #     os.remove(pdf_path)

if __name__ == "__main__":
    main()
