import streamlit as st
from PyPDF2 import PdfReader
from langdetect import detect
from gtts import gTTS
import tempfile
import os
import base64

st.set_page_config(layout="wide")
st.title("📖 Mogontia - Create Your Audio Reference")

# Upload PDF
pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if pdf_file:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        tmp_path = tmp.name

    # Left column: TTS features
    col1, col2 = st.columns([2, 3])

    with col1:
        pdf_reader = PdfReader(tmp_path)
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

            st.markdown(
                f"""
                <div style="height: 800px; overflow-y: auto; padding: 1rem; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;">
                    <pre style="white-space: pre-wrap; color: black;">{full_text}</pre>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Detect language
            try:
                detected_lang = detect(full_text)
                st.success(f"🌍 Detected Language: `{detected_lang}`")
            except Exception as e:
                st.warning(f"Language detection failed: {e}")
                detected_lang = "en"

            # TTS Options
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

    # Right column: Scrollable PDF viewer
    with col2:
        st.subheader("👁️ Scrollable PDF Preview")

        with open(tmp_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')

        pdf_viewer_html = f"""
            <iframe
                src="data:application/pdf;base64,{base64_pdf}"
                width="100%"
                height="800px"
                style="border:1px solid #ccc;"
            ></iframe>
        """

        st.markdown(
            f"""
            <div style="overflow-y: auto; height: 820px;">
                {pdf_viewer_html}
            </div>
            """,
            unsafe_allow_html=True
        )
