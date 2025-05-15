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
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
    menu_items={
        'Get Help': 'https://github.com/mogontia/audiobook-gen',
        'Report a bug': "https://github.com/mogontia/audiobook-gen/issues",
        'About': """
        ## 🎧 PeePit Audiobook Generator 
        **Version 2.1**  
        Transform documents into immersive audio experiences  
        """
    }
)

# Modern UI Styles with Mobile Fixes
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
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0;
    }
    
    .header-gradient {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 2rem 2rem 4rem;
        margin: -1rem -2rem 2rem;
        border-radius: 0 0 20px 20px;
    }
    
    .upload-card {
        background: rgba(43, 45, 66, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 2rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-weight: 600;
        transition: transform 0.2s ease;
    }
    
    .preview-card {
        background: #1A1B2F;
        border-radius: 15px;
        padding: 1.5rem;
        position: relative;
        height: 70vh;
        display: flex;
        flex-direction: column;
    }
    
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #1A1B2F; }
    ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }
    
    .preview-content {
        flex: 1;
        overflow-y: auto;
        padding: 0.5rem;
    }
    
    @media (max-width: 768px) {
        .header-gradient {
            padding: 1rem 1rem 3rem;
            margin: -1rem -1rem 1rem;
        }
        
        .upload-card {
            padding: 1rem;
        }
        
        .preview-card {
            height: 50vh !important;
            margin-bottom: 4rem;
        }
        
        .stButton>button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        
        [data-testid="column"] {
            width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

def pil_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def main():
    # Hero Section
    st.markdown("""
        <div class="header-gradient">
            <h1 style="color: white; margin: 0;">PeePit Audiobook</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem;">
                Peep your doc after transforming it into immersive audio experiences
            </p>
        </div>
    """, unsafe_allow_html=True)

    # File Upload Section
    col1, col2 = st.columns(2, gap="large")
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

    # PDF Processing
    pdf_path = None
    if pdf_file or pdf_url:
        if pdf_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_file.read())
                pdf_path = tmp_file.name
        elif pdf_url:
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
            
            # Page Selection
            st.sidebar.markdown("## 📄 Page Selection")
            selected_pages = st.sidebar.multiselect(
                "Select pages to convert:",
                options=list(range(1, total_pages + 1)),
                default=[1],
                key="page_selector",
                help="Select multiple pages for continuous narration"
            )

            # Main Content
            col_left, col_right = st.columns([1, 1], gap="large")
            
            # Text Preview
            with col_left:
                with st.expander("📜 Document Text", expanded=True):
                    full_text = ""
                    for page_num in selected_pages:
                        page = pdf_reader.pages[page_num - 1]
                        text = page.extract_text()
                        full_text += f"{text}\n\n" if text else ""
                    
                    st.markdown(f"""
                        <div class="preview-card">
                            <div class="preview-content">
                                <pre style="color: #e0e0e0; white-space: pre-wrap; font-family: 'Inter'; margin: 0;">{full_text}</pre>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            # Audio Generation (Outside Scrollable Area)
            if full_text:
                try:
                    detected_lang = detect(full_text[:500])
                    lang = detected_lang
                    st.success(f"🌍 Detected language: {detected_lang.upper()}")
                    
                    # Mobile-optimized button container
                    button_col1, button_col2 = st.columns([1,1])
                    with button_col1:
                        if st.button("🎧 Generate Audiobook", type="primary"):
                            with st.spinner("🔊 Generating audio..."):
                                tts = gTTS(text=full_text, lang=lang)
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                                    tts.save(fp.name)
                                    st.audio(fp.name, format="audio/mp3")
                                    st.download_button(
                                        "💾 Download Audiobook",
                                        data=open(fp.name, "rb"),
                                        file_name="audiobook.mp3",
                                        mime="audio/mp3"
                                    )
                    with button_col2:
                        st.caption("Quality may vary based on document complexity")
                except Exception as e:
                    st.error(f"Error generating audio: {str(e)}")

            # PDF Preview
            with col_right:
                with st.expander("🖼️ Visual Preview", expanded=True):
                    st.markdown("""
                        <div class="preview-card">
                            <div class="preview-content" style="padding: 1rem;">
                    """, unsafe_allow_html=True)
                    
                    with pdfplumber.open(pdf_path) as pdf:
                        for i, page in enumerate(pdf.pages):
                            if (i + 1) in selected_pages:
                                image = page.to_image(resolution=150).original
                                img_base64 = pil_to_base64(image)
                                st.markdown(f"""
                                    <div style="margin-bottom: 2rem;">
                                        <img src="data:image/png;base64,{img_base64}" 
                                            style="width:100%; 
                                            border-radius: 8px;
                                            box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                                        <p style="text-align: center; color: #888; margin-top: 0.5rem;">
                                            Page {i + 1}
                                        </p>
                                    </div>
                                """, unsafe_allow_html=True)
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)

        # Cleanup
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

    else:
        # Empty State
        st.markdown("""
            <div style="text-align: center; padding: 4rem 0; opacity: 0.8;">
                <div style="font-size: 4rem;">📚</div>
                <h3>Upload a document to begin</h3>
                <p style="opacity: 0.7;">Supported formats: PDF</p>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
