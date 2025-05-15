import streamlit as st
from pypdf import PdfReader  # Using the maintained pypdf package
from langdetect import detect
from gtts import gTTS
import tempfile
import requests
import pdfplumber
from PIL import Image
from io import BytesIO
import base64
import os

st.set_page_config(
    page_title="Mogontia Audiobook",
    layout="wide",
    page_icon="📖",
    menu_items={
        'Get Help': 'https://github.com/mogontia/audiobook-gen',
        'Report a bug': "https://github.com/mogontia/audiobook-gen/issues",
        'About': "# 🎧 Mogontia Audiobook Generator\nBeta Version 0.2"
    }
)

# Enhanced custom styles
st.markdown("""
    <style>
    :root {
        --primary: #1ed760;
        --secondary: #535353;
    }
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
        background-color: var(--secondary);
        border-radius: 20px;
        border: none;
        padding: 0.5rem 2rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: var(--primary);
        color: black;
    }
    .pdf-preview-scroll {
        max-height: 80vh;
        overflow-y: auto;
        border: 1px solid #333;
        padding: 1rem;
        border-radius: 10px;
        scrollbar-width: thin;
    }
    .pdf-preview img {
        border: 2px solid #333;
        border-radius: 10px;
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    .pdf-preview img:hover {
        transform: scale(1.02);
    }
    .stAlert {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("📖 Mogontia — V0.2 Beta Audiobook Generator")
    
    # Upload section
    st.header("📂 Choose Your Manuscript")
    col_upload1, col_upload2 = st.columns(2)
    
    with col_upload1:
        pdf_file = st.file_uploader(
            "Upload a PDF document",
            type=["pdf"],
            help="Maximum file size: 50MB"
        )
    
    with col_upload2:
        pdf_url = st.text_input(
            "Or enter PDF URL",
            placeholder="https://example.com/document.pdf",
            help="Supports direct PDF links"
        )

    # PDF processing functions
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

    # Handle file input
    pdf_path = None
    if pdf_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_file.read())
            pdf_path = tmp_file.name
    elif pdf_url:
        if pdf_url.strip():
            content = fetch_pdf_from_url(pdf_url)
            if content:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(content)
                    pdf_path = tmp_file.name

    # Main processing
    if pdf_path:
        try:
            with st.spinner("📖 Analyzing document..."):
                pdf_reader = PdfReader(pdf_path)
                total_pages = len(pdf_reader.pages)

            # Sidebar controls
            st.sidebar.header("⚙️ Conversion Settings")
            selected_pages = st.sidebar.multiselect(
                "Select pages to convert",
                options=list(range(1, total_pages + 1)),
                default=[1],
                help="Select multiple pages for continuous narration"
            )
            
            st.sidebar.markdown("---")
            show_all_pages = st.sidebar.checkbox(
                "Show all pages in preview",
                value=False,
                help="Display full document preview"
            )
            
            # Language settings
            with st.sidebar.expander("🌐 Language Settings"):
                slow = st.checkbox("Slow narration speed")
                lang_override = st.text_input(
                    "Override language code",
                    value="auto",
                    help="ISO 639-1 language code (e.g., 'en', 'es')"
                )

            # Main columns
            col_left, col_right = st.columns([1.5, 2])

            with col_left:
                with st.expander("📜 Extracted Text", expanded=True):
                    full_text = ""
                    for page_num in selected_pages:
                        page = pdf_reader.pages[page_num - 1]
                        text = page.extract_text()
                        full_text += text + "\n\n" if text else ""

                    if full_text:
                        st.markdown(f"""
                            <div style="
                                background: #1a1a1a;
                                padding: 1rem;
                                border-radius: 8px;
                                max-height: 60vh;
                                overflow-y: auto;
                            ">
                                <pre style='
                                    white-space: pre-wrap;
                                    font-family: Georgia, serif;
                                    color: #ddd;
                                    margin: 0;
                                '>{full_text}</pre>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        try:
                            detected_lang = detect(full_text[:500])  # Limit detection to first 500 chars
                            lang = lang_override if lang_override != "auto" else detected_lang
                            st.success(f"🌍 Detected language: {detected_lang.upper()} | Using: {lang.upper()}")
                        except Exception as e:
                            st.warning(f"⚠️ Language detection error: {e}")
                            lang = "en"

                        # Audio generation
                        if st.button("🎧 Generate Audiobook", type="primary"):
                            with st.spinner("🔊 Generating audio..."):
                                try:
                                    tts = gTTS(text=full_text, lang=lang, slow=slow)
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                                        tts.save(fp.name)
                                        st.audio(fp.name, format="audio/mp3")
                                        st.download_button(
                                            "💾 Download Audiobook",
                                            data=open(fp.name, "rb"),
                                            file_name="audiobook.mp3",
                                            mime="audio/mp3",
                                            use_container_width=True
                                        )
                                except Exception as e:
                                    st.error(f"🚨 Audio generation failed: {e}")
                    else:
                        st.info("🔍 No text found in selected pages")

            with col_right:
                with st.expander("🖼️ Document Preview", expanded=True):
                    st.markdown('<div class="pdf-preview-scroll">', unsafe_allow_html=True)
                    with pdfplumber.open(pdf_path) as pdf:
                        for i, page in enumerate(pdf.pages):
                            if show_all_pages or (i + 1) in selected_pages:
                                image = page.to_image(resolution=150).original
                                img_base64 = pil_to_base64(image)
                                st.markdown(f"""
                                    <div class="pdf-preview">
                                        <img src="data:image/png;base64,{img_base64}" 
                                            style="width:100%;
                                            cursor: pointer;"
                                            onclick="window.parent.document.querySelector('section.main').scrollTo(0, 0)">
                                        <p style="text-align:center; 
                                            font-size: 0.9rem; 
                                            color: #888;
                                            margin: 0.5rem 0 1.5rem 0">
                                            Page {i + 1}
                                        </p>
                                    </div>
                                """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    else:
        st.warning("📌 Please upload a PDF or enter a URL to get started")

if __name__ == "__main__":
    main()
