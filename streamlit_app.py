import streamlit as st
from PyPDF2 import PdfReader
from langdetect import detect
from gtts import gTTS
import tempfile
import os
import base64
import requests
from io import BytesIO

st.set_page_config(layout="wide")
st.title("📖 Mogontia Audiobook Generator - Generate Your Own Audiobook Reference")

# PDF URL or file upload
pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])
pdf_url = st.text_input("Or, provide a URL for an online PDF")

# Function to fetch PDF from URL
def fetch_pdf_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            st.error("❌ Failed to download PDF from URL.")
            return None
    except Exception as e:
        st.error(f"❌ Error fetching PDF from URL: {e}")
        return None

if pdf_file:
    # Save uploaded file to a temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_file.read())
        pdf_path = tmp_file.name
elif pdf_url:
    pdf_bytes = fetch_pdf_from_url(pdf_url)
    if pdf_bytes:
        # Save PDF to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_bytes)
            pdf_path = tmp_file.name
else:
    pdf_path = None

if pdf_path:
    # Left and Right columns
    col1, col2 = st.columns([2, 3])

    with col1:
        pdf_reader = PdfReader(pdf_path)
        total_pages = len(pdf_reader.pages)

        st.sidebar.header("📄 Page Selection")
        page_numbers = st.sidebar.multiselect(
            "Select pages to read aloud",
            options=list(range(1, total_pages + 1)),
            default=[1],
        )

        if page_numbers:
            full_text = ""
            for i in page_numbers:
                page = pdf_reader.pages[i - 1]
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            st.subheader("📝 P2lemy - Extracted Text")
            st.markdown(
                f"""
                <div style="height: 800px; overflow-y: auto; padding: 1rem; background-color: black; border: 1px solid #ddd; border-radius: 5px;">
                    <pre style="white-space: pre-wrap; color: white;">{full_text}</pre>
                </div>
                """,
                unsafe_allow_html=True
            )

            try:
                detected_lang = detect(full_text)
                st.success(f"🌍 Detected Language: `{detected_lang}`")
            except Exception as e:
                st.warning(f"Language detection failed: {e}")
                detected_lang = "en"

            st.sidebar.header("🔈 TTS Options")
            slow = st.sidebar.checkbox("Slow Speed", value=False)

            lang_override = st.sidebar.text_input(
                "Override Language Code (optional)", value=detected_lang
            )
            selected_lang = lang_override.strip() if lang_override else detected_lang

            if st.button("🔊 Read Selected Pages Aloud"):
                try:
                    tts = gTTS(text=full_text, lang=selected_lang, slow=slow)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, format="audio/mp3")
                        with open(fp.name, "rb") as audio_file:
                            st.download_button(
                                label="💾 Download Audio",
                                data=audio_file,
                                file_name="tts_output.mp3",
                                mime="audio/mp3",
                            )
                except Exception as e:
                    st.error(f"❌ TTS failed: {e}")
        else:
            st.info("Please select at least one page.")

    with col2:
        st.subheader("👁️ Scrollable PDF Preview")

        # Encode PDF as base64
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")

        pdf_display = f"""
        <iframe 
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%" 
            height="800px" 
            type="application/pdf"
            style="border:1px solid #ccc; border-radius: 4px;">
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
else:
    st.info("📂 Please upload a PDF file or provide a URL to begin.")
