import streamlit as st
from PyPDF2 import PdfReader
from langdetect import detect
from gtts import gTTS
import tempfile
import os
import base64
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

st.set_page_config(layout="wide")
st.title("📖 Mogontia Audiobook Generator - Multilingual PDF to Audio + Summary")

# Upload PDF
pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

def extract_text_with_ocr(pdf_path, page_number):
    try:
        images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
        text = pytesseract.image_to_string(images[0])
        return text
    except Exception as e:
        return ""

def summarize_text(text):
    # You can plug in your LLM here
    return f"🔎 Summary (Placeholder): {text[:300]}..." if text else "No text to summarize."

if pdf_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_file.read())
        pdf_path = tmp_file.name

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

        full_text = ""
        image_based_pages = []

        for i in page_numbers:
            text = pdf_reader.pages[i - 1].extract_text()
            if not text or text.strip() == "":
                text = extract_text_with_ocr(pdf_path, i)
                image_based_pages.append(i)
            full_text += text + "\n"

        if full_text.strip():
            st.subheader("📝 Extracted Text")
            st.markdown(
                f"""
                <div style="height: 800px; overflow-y: auto; padding: 1rem; background-color: black; border: 1px solid #ddd; border-radius: 5px;">
                    <pre style="white-space: pre-wrap; color: white;">{full_text}</pre>
                </div>
                """,
                unsafe_allow_html=True
            )

            if image_based_pages:
                st.warning(f"📸 OCR used on image-only pages: {image_based_pages}")

            try:
                detected_lang = detect(full_text)
                st.success(f"🌍 Detected Language: `{detected_lang}`")
            except Exception as e:
                st.warning(f"Language detection failed: {e}")
                detected_lang = "en"

            st.sidebar.header("🔈 TTS Options")
            slow = st.sidebar.checkbox("Slow Speed", value=False)
            lang_override = st.sidebar.text_input("Override Language Code (optional)", value=detected_lang)
            selected_lang = lang_override.strip() if lang_override else detected_lang

            if st.button("📌 Show Summary First"):
                st.info(summarize_text(full_text))

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
            st.info("❗ No readable text found on selected pages.")

    with col2:
        st.subheader("👁️ Scrollable PDF Preview")
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
    st.info("📂 Please upload a PDF to begin.")
