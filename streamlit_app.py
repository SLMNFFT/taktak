import streamlit as st
from PyPDF2 import PdfReader
from langdetect import detect
from gtts import gTTS
import tempfile
import os
import requests
import pdfplumber
from PIL import Image
from io import BytesIO
import base64

st.set_page_config(page_title="Mogontia Audiobook", layout="wide", page_icon="📖")

# Custom styles
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #0d0d0d;
        color: #e0e0e0;
        font-family: 'Georgia', serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        color: white;
        background-color: #262626;
        border-radius: 8px;
        border: 1px solid #444;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #404040;
    }
    .pdf-preview img {
        border: 2px solid #333;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📖 Mogontia — The Fiction & Mystery Audiobook Forge")

# Upload area
st.header("📂 Choose Your Manuscript")
col_upload1, col_upload2 = st.columns(2)
pdf_file = col_upload1.file_uploader("Upload a mysterious PDF", type=["pdf"])
pdf_url = col_upload2.text_input("Or enter a URL to a digital grimoire (PDF)")

def fetch_pdf_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            st.error("❌ Failed to download PDF from URL.")
            return None
    except Exception as e:
        st.error(f"❌ Error fetching PDF: {e}")
        return None

def pil_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# Handle upload or download
pdf_path = None
if pdf_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_file.read())
        pdf_path = tmp_file.name
elif pdf_url:
    content = fetch_pdf_from_url(pdf_url)
    if content:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(content)
            pdf_path = tmp_file.name

# Main layout if PDF is loaded
if pdf_path:
    pdf_reader = PdfReader(pdf_path)
    total_pages = len(pdf_reader.pages)

    st.sidebar.header("📄 Page Selection")
    selected_pages = st.sidebar.multiselect(
        "Choose which pages to narrate",
        options=list(range(1, total_pages + 1)),
        default=[1]
    )

    col_left, col_right = st.columns([1.5, 2])

    with col_left:
        with st.expander("🔍 Extracted Story"):
            full_text = ""
            for page_num in selected_pages:
                page = pdf_reader.pages[page_num - 1]
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            if full_text:
                st.markdown(f"<pre style='white-space: pre-wrap; font-family: Georgia, serif; color: #ddd;'>{full_text}</pre>", unsafe_allow_html=True)

                try:
                    detected_lang = detect(full_text)
                    st.success(f"🌍 Language Detected: `{detected_lang}`")
                except Exception as e:
                    st.warning(f"Language detection failed: {e}")
                    detected_lang = "en"

                slow = st.sidebar.checkbox("🐢 Slow Reading")
                lang_override = st.sidebar.text_input("Language Override", value=detected_lang)
                chosen_lang = lang_override.strip()

                if st.button("🎧 Generate Audiobook"):
                    try:
                        tts = gTTS(text=full_text, lang=chosen_lang, slow=slow)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                            tts.save(fp.name)
                            st.audio(fp.name, format="audio/mp3")
                            with open(fp.name, "rb") as audio_file:
                                st.download_button(
                                    "💾 Save Audiobook",
                                    data=audio_file,
                                    file_name="narration.mp3",
                                    mime="audio/mp3"
                                )
                    except Exception as e:
                        st.error(f"TTS failed: {e}")
            else:
                st.info("No text found on selected pages.")

    with col_right:
        with st.expander("🖼️ Preview Pages"):
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    if i + 1 in selected_pages:
                        image = page.to_image(resolution=150).original
                        img_base64 = pil_to_base64(image)
                        st.markdown(f"""
                            <div class="pdf-preview">
                                <img src="data:image/png;base64,{img_base64}" style="width:100%;">
                                <p style="text-align:center; font-size: 14px; color: #999;">Page {i + 1}</p>
                            </div>
                        """, unsafe_allow_html=True)

else:
    st.warning("🕵️ Please upload a PDF or paste a URL to begin your audiobook journey.")
