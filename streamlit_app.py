import streamlit as st
from pypdf import PdfReader
from langdetect import detect
from gtts import gTTS
import tempfile
import requests
import pdfplumber
from PIL import Image
from io import BytesIO
import base64
import os

# Page configuration
st.set_page_config(
    page_title="Mogontia Audiobook Generator",
    page_icon="📖",
    layout="wide",
    menu_items={
        'Get Help': 'https://github.com/mogontia/audiobook-gen',
        'Report a bug': "https://github.com/mogontia/audiobook-gen/issues",
        'About': "# 🎧 Mogontia Audiobook Generator\nBeta Version 0.2"
    }
)

# 🎨 Custom Styles
st.markdown("""
    <style>
    :root {
        --primary: #1ed760;
        --secondary: #535353;
        --dark: #0d0d0d;
        --light: #e0e0e0;
        --accent: #1db954;
    }
    html, body, [class*="css"] {
        background-color: var(--dark);
        color: var(--light);
        font-family: 'Georgia', serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        background-color: var(--secondary);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.6rem 1.5rem;
        transition: 0.3s ease;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: var(--primary);
        color: black;
        transform: scale(1.03);
    }
    .stDownloadButton>button {
        background-color: var(--accent);
        border-radius: 20px;
        color: black;
        font-weight: bold;
    }
    .pdf-preview-scroll {
        max-height: 75vh;
        overflow-y: auto;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 1rem;
        scrollbar-width: thin;
    }
    .pdf-preview img {
        width: 100%;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 2px solid #444;
        transition: transform 0.2s;
    }
    .pdf-preview img:hover {
        transform: scale(1.015);
    }
    .highlight-box {
        background-color: #1a1a1a;
        padding: 1rem;
        border-radius: 10px;
        color: #ccc;
        font-size: 0.95rem;
        max-height: 60vh;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)


def fetch_pdf_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"❌ Error fetching PDF: {str(e)}")
        return None

def pil_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def main():
    st.title("📖 Mogontia — Audiobook Generator (Beta V0.2)")

    # Upload Section
    st.header("📂 Upload or Link Your PDF")
    col1, col2 = st.columns(2)

    with col1:
        pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    with col2:
        pdf_url = st.text_input("Or paste a PDF URL", placeholder="https://example.com/sample.pdf")

    pdf_path = None
    if pdf_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_file.read())
            pdf_path = tmp_file.name
    elif pdf_url.strip():
        content = fetch_pdf_from_url(pdf_url)
        if content:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(content)
                pdf_path = tmp_file.name

    # Process PDF
    if pdf_path:
        try:
            with st.spinner("🔍 Reading the PDF..."):
                reader = PdfReader(pdf_path)
                total_pages = len(reader.pages)

            st.sidebar.header("⚙️ Conversion Settings")
            selected_pages = st.sidebar.multiselect(
                "Select pages to convert",
                options=list(range(1, total_pages + 1)),
                default=[1]
            )

            st.sidebar.markdown("---")
            show_all = st.sidebar.checkbox("📑 Show full document preview", value=False)

            with st.sidebar.expander("🌐 Language & Speed"):
                slow = st.checkbox("Slow narration")
                lang_override = st.text_input("Language override (e.g., en, de, fr)", value="auto")

            col_text, col_preview = st.columns([1.4, 1.6])

            # Text Extraction
            with col_text:
                st.subheader("📜 Extracted Text")
                full_text = ""
                for page_num in selected_pages:
                    text = reader.pages[page_num - 1].extract_text()
                    if text:
                        full_text += text + "\n\n"

                if full_text.strip():
                    st.markdown(f"<div class='highlight-box'><pre>{full_text}</pre></div>", unsafe_allow_html=True)
                    try:
                        detected = detect(full_text[:500])
                        lang = lang_override if lang_override != "auto" else detected
                        st.success(f"🌍 Detected: {detected.upper()} | Using: {lang.upper()}")
                    except Exception as e:
                        st.warning(f"⚠️ Language detection failed: {e}")
                        lang = "en"

                    if st.button("🎧 Generate Audiobook"):
                        with st.spinner("🔊 Generating MP3..."):
                            try:
                                tts = gTTS(text=full_text, lang=lang, slow=slow)
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_fp:
                                    tts.save(audio_fp.name)
                                    st.audio(audio_fp.name, format="audio/mp3")
                                    st.download_button(
                                        label="💾 Download Audiobook",
                                        data=open(audio_fp.name, "rb"),
                                        file_name="audiobook.mp3",
                                        mime="audio/mp3"
                                    )
                            except Exception as e:
                                st.error(f"❌ Failed to generate audio: {e}")
                else:
                    st.info("❗ No text found in selected pages.")

            # Preview Section
            with col_preview:
                st.subheader("🖼️ PDF Page Previews")
                st.markdown('<div class="pdf-preview-scroll">', unsafe_allow_html=True)
                with pdfplumber.open(pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        if show_all or (i + 1) in selected_pages:
                            img = page.to_image(resolution=150).original
                            img_b64 = pil_to_base64(img)
                            st.markdown(f"""
                                <div class="pdf-preview">
                                    <img src="data:image/png;base64,{img_b64}" />
                                    <p style="text-align:center; font-size:0.85rem; color:#999;">Page {i+1}</p>
                                </div>
                            """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    else:
        st.info("📎 Upload or enter a URL to start generating an audiobook.")

if __name__ == "__main__":
    main()
