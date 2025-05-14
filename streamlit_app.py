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
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0;
    }
    
    /* Gradient Header */
    .header-gradient {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 2rem 2rem 4rem;
        margin: -1rem -2rem 2rem;
        border-radius: 0 0 20px 20px;
    }
    
    /* Upload Cards */
    .upload-card {
        background: rgba(43, 45, 66, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 2rem;
        transition: all 0.3s ease;
    }
    .upload-card:hover {
        border-color: var(--primary);
        box-shadow: 0 8px 32px rgba(37, 201, 165, 0.15);
    }
    
    /* Modern Button */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-weight: 600;
        transition: transform 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(37, 201, 165, 0.3);
    }
    
    /* Preview Cards */
    .preview-card {
        background: #1A1B2F;
        border-radius: 15px;
        padding: 1.5rem;
        position: relative;
        transition: all 0.3s ease;
    }
    .preview-card::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 15px;
        padding: 2px;
        background: linear-gradient(45deg, var(--primary), transparent);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #1A1B2F; }
    ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

def main():
    # Hero Section
    st.markdown("""
        <div class="header-gradient">
            <h1 style="color: white; margin: 0;">Mogontia Audiobook</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem;">
                Transform documents into immersive audio experiences
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Upload Section
    col1, col2 = st.columns(2, gap="large")
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

    # Processing
    pdf_path = None
    if pdf_file or pdf_url:
        # [Keep previous PDF processing logic]
        # Add modern preview sections:
        
        with st.container():
            col_left, col_right = st.columns([1.2, 1], gap="large")
            
            with col_left:
                with st.expander("📜 Document Text", expanded=True):
                    st.markdown("""
                        <div class="preview-card">
                            <div style="max-height: 60vh; overflow-y: auto;">
                                <!-- Text content here -->
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
            with col_right:
                with st.expander("🖼️ Visual Preview", expanded=True):
                    st.markdown("""
                        <div class="preview-card">
                            <div style="max-height: 70vh; overflow-y: auto;">
                                <!-- PDF preview images here -->
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        
        # Modern Controls
        with st.sidebar:
            st.markdown("## ⚙️ Control Panel")
            with st.expander("🔊 Audio Settings", expanded=True):
                # Add audio customization options
                st.slider("Playback Speed", 0.5, 2.0, 1.0)
                st.selectbox("Voice Style", ["Standard", "Professional", "Storyteller"])
            
            with st.expander("🎨 Display Options"):
                st.checkbox("Show Page Numbers", True)
                st.checkbox("Dark Mode", True)
                st.color_picker("Accent Color", "#25C9A5")

    else:
        # Empty State Design
        st.markdown("""
            <div style="text-align: center; padding: 4rem 0; opacity: 0.8;">
                <div style="font-size: 4rem;">📚</div>
                <h3>Upload a document to begin</h3>
                <p style="opacity: 0.7;">Supported formats: PDF</p>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
