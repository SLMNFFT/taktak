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
from langdetect import detect, LangDetectException
from bidi.algorithm import get_display

st.set_page_config(
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
)

st.markdown("""
<style>
    /* RTL text styling */
    .rtl-text {
        direction: rtl;
        text-align: right;
        font-family: 'Noto Sans Arabic', Tahoma, sans-serif !important;
        line-height: 2;
        unicode-bidi: embed;
    }
    
    /* Base styling */
    [data-testid="stAppViewContainer"] {
        background: #0f1123;
        color: #ffffff;
    }
    
    .text-container {
        padding: 1rem;
        background: #1A1B2F;
        border-radius: 8px;
        margin: 1rem 0;
        white-space: pre-wrap;
    }
    
    mark {
        background-color: #ffeb3b !important;
        color: #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
TESSERACT_LANG_MAP = {
    'en': 'eng',
    'ar': 'ara'
}

def detect_content_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return 'en'

def extract_text_with_ocr(pdf_path, pages, lang='eng'):
    from pdf2image import convert_from_path
    import pytesseract
    text = ""
    images = convert_from_path(pdf_path, dpi=300, first_page=min(pages), last_page=max(pages))
    for i, img in zip(pages, images):
        text += f"--- Page {i} (OCR) ---\n"
        text += pytesseract.image_to_string(img, lang=lang)
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

    # Auto-detect OCR language
    detected_lang = 'eng'
    if extracted_text:
        try:
            detected_lang = detect_content_language(extracted_text)
        except:
            pass

    valid_ocr_pages = [p for p in pages_without_text if 1 <= p <= len(reader.pages)]
    if valid_ocr_pages:
        st.warning(f"🔍 Running OCR on pages: {valid_ocr_pages}")
        ocr_lang = TESSERACT_LANG_MAP.get(detected_lang, 'eng')
        ocr_text = extract_text_with_ocr(pdf_path, valid_ocr_pages, lang=ocr_lang)
        extracted_text += ocr_text

    return extracted_text.strip(), valid_ocr_pages

def generate_audio(text):
    try:
        lang = detect_content_language(text)
    except:
        lang = 'en'
        
    tts = gTTS(text=text, lang=lang, slow=False)
    temp_audio_path = tempfile.mktemp(suffix=".mp3")
    tts.save(temp_audio_path)
    return temp_audio_path

# --- MAIN APP ---
def main():
    st.markdown("""
    <h1 style="text-align: center; font-family: 'Segoe UI'; margin: 2rem 0;">
        <span style="transform: rotate(180deg); display: inline-block;">🎧</span> 
        PeePit
    </h1>
    <div style="text-align: center; margin-bottom: 2rem;">
        Turns your PDF to MP3 🎧
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📤 Upload PDF", type=["pdf"])
    pdf_path = None

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = tmp.name

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        selected_pages = st.multiselect(
            "Select pages to process",
            list(range(1, total_pages + 1)),
            default=[1]
        )

        if not selected_pages:
            st.error("Please select at least one valid page")
            return

        with st.spinner("🔍 Analyzing document..."):
            full_text, ocr_pages = extract_text_from_pdf(pdf_path, selected_pages)
            
            if not full_text:
                st.error("No extractable text found")
                return

            # Detect content language for display
            try:
                content_lang = detect_content_language(full_text)
            except:
                content_lang = 'en'

            col_left, col_right = st.columns(2)

            with col_left:
                with st.expander("📜 Extracted Text", expanded=True):
                    search_term = st.text_input("🔎 Search within text", "")
                    show_ocr = st.checkbox("👁️ Show OCR text", value=True)

                    if not show_ocr and ocr_pages:
                        pattern = r"--- Page (\d+).*?(?=(--- Page |\Z))"
                        filtered = re.findall(pattern, full_text, re.DOTALL)
                        filtered_text = "\n\n".join(section for section, _ in filtered if int(section) not in ocr_pages)
                    else:
                        filtered_text = full_text

                    if search_term:
                        filtered_text = re.sub(
                            f"(?i)({re.escape(search_term)})",
                            r"<mark>\1</mark>",
                            filtered_text,
                            flags=re.DOTALL,
                        )

                    # Apply RTL formatting for Arabic content
                    if content_lang == 'ar':
                        filtered_text = get_display(filtered_text)
                        text_class = "rtl-text"
                    else:
                        text_class = ""

                    st.markdown(f"""
                    <div class="text-container {text_class}">
                        {filtered_text.replace("\n", "<br>")}
                    </div>
                    """, unsafe_allow_html=True)

            with col_right:
                with st.expander("🔊 Audio Playback", expanded=True):
                    audio_path = generate_audio(filtered_text)
                    st.audio(audio_path, format="audio/mp3")

if __name__ == "__main__":
    main()