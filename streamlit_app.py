import streamlit as st
from PyPDF2 import PdfReader
from langdetect import detect
from gtts import gTTS
import tempfile
import os

# Title
st.title("📖 Multilingual PDF Reader with Text-to-Speech")

# Upload PDF
pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if pdf_file:
    pdf_reader = PdfReader(pdf_file)
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

        st.subheader("📝 Extracted Text")
        st.write(full_text)

        # Detect language
        try:
            detected_lang = detect(full_text)
            st.success(f"🌍 Detected Language: `{detected_lang}`")
        except Exception as e:
            st.warning(f"Language detection failed: {e}")
            detected_lang = "en"

        # Voice and speed controls
        st.sidebar.header("🔈 TTS Options")
        slow = st.sidebar.checkbox("Slow Speed", value=False)

        # Language options override (optional)
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
