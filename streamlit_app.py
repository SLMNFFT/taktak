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

st.set_page_config(
    page_title="Mogontia Audiobook",
    layout="wide",
    page_icon="🎧",
    menu_items={
        'Get Help': 'https://github.com/mogontia/audiobook-gen',
        'Report a bug': "https://github.com/mogontia/audiobook-gen/issues",
        'About': """
        ## 🎧 Mogontia Audiobook Generator 
        **Version 2.0**  
        Transform documents into immersive audio experiences  
        """
    }
)

# Modern UI Styles
st.markdown("""
    <style>
    :root {
        --primary: #25C9A5;
        --secondary: #2B2D42;
        --accent: #FF6B6B;
        --background: #0F0F1C;
    }
    
    html, body, [class*="css"] {
        background-color: var(--background);
        color: #F8F9FA;
        font-family: 'Inter', sans-serif;
        height: 100vh;
        overflow: hidden;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0;
        height: calc(100vh - 100px);
    }
    
    .header-gradient {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 1rem 2rem 2rem;
        margin: -1rem -2rem 1rem;
        border-radius: 0 0 20px 20px;
    }
    
    .upload-card {
        background: rgba(43, 45, 66, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .preview-card {
        background: #1A1B2F;
        border-radius: 15px;
        padding: 1rem;
        height: calc(100vh - 300px);
        display: flex;
        flex-direction: column;
    }
    
    .preview-content {
        flex: 1;
        overflow-y: auto;
        padding: 0.5rem;
    }
    
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 300px !important;
    }
    
    [data-testid="column"] {
        flex: 1 1 0%;
        min-width: 0;
        padding: 0 0.5rem;
    }
    
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

def pil_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def main():
    # Compact Hero Section
    st.markdown("""
        <div class="header-gradient">
            <h1 style="color: white; margin: 0; font-size: 1.8rem;">Mogontia Audiobook</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">
                Transform documents into immersive audio experiences
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Upload Section
    col1, col2 = st.columns(2, gap="medium")
    pdf_file = None
    pdf_url = None
    
    with col1:
        with st.container():
            st.markdown('<div class="upload-card">', unsafe_allow_html=True)
            pdf_file = st.file_uploader(
                "📤 Upload PDF", 
                type=["pdf"],
                help="Supports PDF documents up to 200MB",
                key="file_upload"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="upload-card">', unsafe_allow_html=True)
            pdf_url = st.text_input(
                "🌐 PDF URL",
                placeholder="Enter document URL...",
                help="Direct link to PDF file",
                key="url_input"
            )
            st.markdown('</div>', unsafe_allow_html=True)

    # Main Content Area
    if pdf_file or pdf_url:
        pdf_path = None
        try:
            if pdf_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(pdf_file.read())
                    pdf_path = tmp_file.name
            else:
                try:
                    response = requests.get(pdf_url, timeout=10)
                    response.raise_for_status()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(response.content)
                        pdf_path = tmp_file.name
                except Exception as e:
                    st.error(f"❌ Error fetching PDF: {str(e)}")
                    return

            with st.spinner("🔍 Analyzing document..."):
                pdf_reader = PdfReader(pdf_path)
                total_pages = len(pdf_reader.pages)
                
                # Sidebar Controls
                with st.sidebar:
                    st.markdown("## ⚙️ Controls")
                    selected_pages = st.multiselect(
                        "Select pages:",
                        options=list(range(1, total_pages + 1)),
                        default=[1],
                        key="page_selector"
                    )
                    
                    st.markdown("---")
                    detected_lang = "en"
                    if selected_pages:
                        full_text = "".join(pdf_reader.pages[page-1].extract_text() for page in selected_pages)
                        try:
                            detected_lang = detect(full_text[:500])
                        except: 
                            pass
                    
                    lang = st.text_input("Language Code", value=detected_lang)
                    slow = st.checkbox("Slow Narration")
                    
                    if st.button("🎧 Generate Audiobook"):
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
                                        mime="audio/mp3"
                                    )
                            except Exception as e:
                                st.error(f"Audio generation failed: {str(e)}")

                # Main Preview Panels
                col_left, col_right = st.columns(2, gap="medium")
                
                with col_left:
                    with st.container():
                        st.markdown("### Text Preview")
                        full_text = "".join(pdf_reader.pages[page-1].extract_text() for page in selected_pages)
                        st.markdown(f"""
                            <div class="preview-card">
                                <div class="preview-content">
                                    <pre style="color: #e0e0e0; white-space: pre-wrap;">{full_text}</pre>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                with col_right:
                    with st.container():
                        st.markdown("### Visual Preview")
                        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
                        with pdfplumber.open(pdf_path) as pdf:
                            for i, page in enumerate(pdf.pages):
                                if (i + 1) in selected_pages:
                                    image = page.to_image(resolution=130).original
                                    img_base64 = pil_to_base64(image)
                                    st.markdown(f"""
                                        <div style="margin-bottom: 1rem;">
                                            <img src="data:image/png;base64,{img_base64}" 
                                                style="width:100%; border-radius: 8px;">
                                            <p style="text-align: center; color: #888; margin: 0.3rem 0; font-size: 0.8rem;">
                                                Page {i + 1}
                                            </p>
                                        </div>
                                    """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

        finally:
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)

    else:
        # Compact Empty State
        st.markdown("""
            <div style="text-align: center; padding: 2rem 0; opacity: 0.8;">
                <div style="font-size: 2rem;">📚</div>
                <p>Upload a PDF or enter URL to begin</p>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
