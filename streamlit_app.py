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
import re

# ... [Keep all previous imports and style definitions] ...

def main():
    # ... [Keep previous main() setup code] ...

    # Main processing
    if pdf_path:
        try:
            with st.spinner("📖 Analyzing document..."):
                pdf_reader = PdfReader(pdf_path)
                total_pages = len(pdf_reader.pages)
                
                # Pre-process text for search
                page_texts = {}
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_texts[page_num + 1] = page.extract_text() or ""

            # Sidebar controls
            st.sidebar.header("⚙️ Conversion Settings")
            
            # Search functionality
            st.sidebar.markdown("---")
            search_query = st.sidebar.text_input("🔍 Search document content")
            
            # Initialize session state for search results
            if 'search_results' not in st.session_state:
                st.session_state.search_results = {}

            # Search logic
            if search_query:
                matches = {}
                try:
                    pattern = re.compile(f'({re.escape(search_query)})', re.IGNORECASE)
                    for page_num, text in page_texts.items():
                        if re.search(pattern, text):
                            matches[page_num] = [m.start() for m in re.finditer(pattern, text)]
                    st.session_state.search_results = matches
                except re.error:
                    st.sidebar.error("Invalid search pattern")
            else:
                st.session_state.search_results = {}

            # Page selection with search integration
            default_pages = [1] if not st.session_state.search_results else list(st.session_state.search_results.keys())
            selected_pages = st.sidebar.multiselect(
                "Select pages to convert",
                options=list(range(1, total_pages + 1)),
                default=default_pages,
                help="Select multiple pages for continuous narration",
                key="page_selector"
            )

            # ... [Keep rest of sidebar controls] ...

            # Main columns
            col_left, col_right = st.columns([1.5, 2])

            with col_left:
                with st.expander("📜 Extracted Text", expanded=True):
                    full_text = ""
                    highlighted_text = ""
                    for page_num in selected_pages:
                        text = page_texts.get(page_num, "")
                        if text:
                            # Highlight search matches
                            if page_num in st.session_state.search_results:
                                text = re.sub(
                                    pattern, 
                                    r'<span style="background-color: #FFD70088; border-radius: 2px;">\1</span>', 
                                    text
                                )
                            full_text += f"Page {page_num}:\n{text}\n\n"

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
                                    line-height: 1.5;
                                '>{full_text}</pre>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # ... [Keep existing language detection and audio code] ...

            with col_right:
                with st.expander("🖼️ Document Preview", expanded=True):
                    st.markdown('<div class="pdf-preview-scroll">', unsafe_allow_html=True)
                    with pdfplumber.open(pdf_path) as pdf:
                        for i, page in enumerate(pdf.pages):
                            page_num = i + 1
                            show_it = show_all_pages or (page_num in selected_pages)
                            if show_it:
                                image = page.to_image(resolution=150).original
                                img_base64 = pil_to_base64(image)
                                
                                # Add search result indicator
                                border_style = ""
                                if page_num in st.session_state.search_results:
                                    border_style = "border: 2px solid #FFD700; box-shadow: 0 0 10px #FFD70088;"
                                    matches_count = len(st.session_state.search_results[page_num])
                                
                                st.markdown(f"""
                                    <div class="pdf-preview">
                                        <div style="
                                            position: relative;
                                            {border_style}
                                            border-radius: 10px;
                                            margin-bottom: 1.5rem;
                                        ">
                                            <img src="data:image/png;base64,{img_base64}" 
                                                style="width:100%;
                                                cursor: pointer;
                                                border-radius: 8px;"
                                                onclick="window.parent.document.querySelector('section.main').scrollTo(0, 0)">
                                            {"<div style='
                                                position: absolute;
                                                top: 5px;
                                                right: 5px;
                                                background: #FFD700DD;
                                                color: #000;
                                                padding: 2px 8px;
                                                border-radius: 12px;
                                                font-size: 0.8rem;
                                                font-weight: bold;
                                            '>🔍 {matches_count}</div>" 
                                            if page_num in st.session_state.search_results else ""}
                                            <p style="text-align:center; 
                                                font-size: 0.9rem; 
                                                color: #888;
                                                margin: 0.5rem 0 1.5rem 0">
                                                Page {page_num}
                                            </p>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    else:
        st.warning("📌 Please upload a PDF or enter a URL to get started")

# ... [Keep rest of the code] ...
