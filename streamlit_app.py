import streamlit as st
from PyPDF2 import PdfReader
import pdfplumber
from gtts import gTTS
import tempfile
import pytesseract
from PIL import Image
import io
import re
from bidi.algorithm import get_display
import arabic_reshaper
from pdf2image import convert_from_bytes

def extract_text_from_pdf(pdf_file, content_lang):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except Exception:
        text = ""
        images = convert_from_bytes(pdf_file.read())
        for image in images:
            text += pytesseract.image_to_string(image, lang=content_lang)
    return text

def clean_ocr_text(text):
    return re.sub(r'[\x00-\x1F]+', '', text).strip()

def extract_and_highlight_text(text, keywords, lang):
    pattern = '|'.join(re.escape(word) for word in keywords if word.strip())
    if not pattern:
        return text, []
    matches = re.findall(pattern, text, re.IGNORECASE)
    highlighted_text = re.sub(f"({pattern})", r'**\1**', text, flags=re.IGNORECASE)
    return highlighted_text, matches

def main():
    st.title("Peepit Audiobook")

    pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    col1, col2 = st.columns(2)
    with col1:
        content_lang = st.selectbox("PDF Content Language", options=["en", "fr", "ar", "de", "it", "es", "zh-cn"])
    with col2:
        audio_lang = st.selectbox("Audio Output Language", options=["en", "fr", "ar", "de", "it", "es", "zh-cn"])

    keywords = st.text_input("Enter keywords to highlight (comma-separated):", value="")
    keyword_list = [word.strip() for word in keywords.split(",") if word.strip()]

    if pdf_file:
        pdf_bytes = pdf_file.read()
        extracted_text = extract_text_from_pdf(io.BytesIO(pdf_bytes), content_lang)

        if content_lang == 'ar':
            extracted_text = clean_ocr_text(extracted_text)
            try:
                reshaped = arabic_reshaper.reshape(extracted_text)
                display_text = get_display(reshaped)
            except Exception:
                display_text = get_display(extracted_text)
        else:
            display_text = extracted_text

        highlighted_text, matched_keywords = extract_and_highlight_text(display_text, keyword_list, content_lang)

        st.markdown("### Extracted Text with Highlighted Keywords")
        st.markdown(highlighted_text)

        if extracted_text:
            tts = gTTS(text=extracted_text, lang=audio_lang)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
                tts.save(tmpfile.name)
                st.audio(tmpfile.name, format="audio/mp3")
        else:
            st.warning("No text found in the PDF.")

if __name__ == "__main__":
    main()