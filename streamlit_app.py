import streamlit as st
import re
import tempfile
import base64
from pypdf import PdfReader
from pdf2image import convert_from_path
from fpdf import FPDF
import io
from gtts import gTTS
import os

st.set_page_config(
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
)

# Your existing CSS styling
st.markdown("""
<style>
/* Styling for the Streamlit page */
[data-testid="stColumns"] {
    display: flex;
    align-items: stretch;
    gap: 2rem;
    justify-content: center;
}

body, pre {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #ddd;
    background-color: #0f1123;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
}

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

.st-expanderHeader {
    background-color: #2ecc71 !important;
}

.preview-card {
    background: #1A1B2F;
    border-radius: 15px;
    padding: 1.5rem;
    height: 100%;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 15px rgba(10, 10, 30, 0.5);
}

.scroll-container {
    flex: 1;
    overflow-y: auto;
    padding-right: 0.5rem;
    scrollbar-width: thin;
    scrollbar-color: #4e5aee #1A1B2F;
}

.preview-image-container {
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
}

.preview-image {
    background: #2B2D42;
    border-radius: 8px;
    padding: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    user-select: none;
}

.preview-image img {
    border-radius: 6px;
    margin-bottom: 0.5rem;
    width: 100%;
    height: auto;
    object-fit: contain;
}
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

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

    return extracted_text.strip(), pages_without_text


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

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_img_file:
            temp_img_file.write(bio.read())
            temp_img_file_path = temp_img_file.name
        
        pdf.add_page()
        pdf.image(temp_img_file_path, x=10, y=10, w=pdf.w - 20)

    pdf_path = tempfile.mktemp(suffix=".pdf")
    pdf.output(pdf_path)
    
    return pdf_path


# --- Main App ---

def main():
    st.markdown("""
<h1 style='
    color: white;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    text-align: center;
    font-weight: 600;
    margin-top: 2rem;
    margin-bottom: 2rem;
'>
🎧 PeePit
</h1>
""", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload PDF file (drag-and-drop supported)", 
        type=["pdf"], 
        label_visibility="visible"
    )

    if uploaded_file:
        # Save uploaded PDF to temp file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = tmp.name

        # Read total pages
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        # Generate thumbnails for all pages
        with st.spinner("Generating page thumbnails..."):
            images = convert_from_path(pdf_path, dpi=100, first_page=1, last_page=total_pages)

        # Show thumbnails with page numbers
        st.markdown("### 📄 Page Previews")
        cols = st.columns(min(total_pages, 6))
        for i, img in enumerate(images):
            with cols[i % 6]:
                st.image(img, caption=f"Page {i+1}", use_column_width=True)

        # Page selection
        selected_pages = st.multiselect(
            "Select pages to process", 
            options=list(range(1, total_pages + 1)),
            default=[1]
        )

        if selected_pages:
            with st.spinner("Extracting text..."):
                full_text, pages_without_text = extract_text_from_pdf(pdf_path, selected_pages)

            if not full_text:
                st.error("No extractable text found in selected pages.")
                return

            # Display extracted text
            with st.expander("📜 Extracted Text", expanded=True):
                search_term = st.text_input("🔎 Search within text", "")
                display_text = full_text

                if search_term:
                    display_text = re.sub(
                        f"(?i)({re.escape(search_term)})",
                        r"<mark style='background-color:yellow'>\1</mark>",
                        display_text,
                        flags=re.DOTALL,
                    )
                st.markdown(display_text.replace("\n", "<br>"), unsafe_allow_html=True)

            # Audio generation and playback
            with st.expander("🔊 Audio Playback", expanded=True):
                lang = st.radio("Select language", ("en", "es", "fr", "de"))
                rate = st.slider("Speed", 0.5, 2.0, 1.0, 0.1)
                gender = st.radio("Select voice type", ("male", "female"))

                audio_path = generate_audio(full_text, lang=lang, rate=rate, gender=gender)
                with open(audio_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3")

            # Export thumbnails as PDF for download
            export_images = [images[i-1] for i in selected_pages]  # zero-based index

            pdf_export_path = save_images_as_pdf(export_images)

            with open(pdf_export_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                "📥 Export Selected Pages as PDF (Thumbnails)", 
                data=pdf_bytes,
                file_name="exported_pages_preview.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()
