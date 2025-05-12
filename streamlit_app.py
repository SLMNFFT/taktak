import streamlit as st
import PyPDF2
from langdetect import detect
from streamlit_pdf_viewer import pdf_viewer
from io import BytesIO
import tempfile
import os
import time
import requests
from gtts import gTTS

from langchain_community.llms import Ollama
from langchain.chains.question_answering import load_qa_chain
from langchain.docstore.document import Document

st.set_page_config(page_title="TakTak", layout="wide")
st.title("📄 TakTaK PDF Reader with Multilingual Audio Assistance")

# Sidebar info
st.sidebar.header("🎙️ Speech Settings (gTTS)")
st.sidebar.markdown("Using Google Text-to-Speech for high-quality, reliable multilingual audio.")

# File upload or URL input
pdf_file = st.file_uploader("Upload your PDF", type=["pdf"])
pdf_url = st.text_input("Or, enter a PDF URL")

# Function to fetch PDF from URL
def fetch_pdf_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            st.error("❌ Failed to download PDF from URL.")
            return None
    except Exception as e:
        st.error(f"❌ Error fetching PDF from URL: {e}")
        return None

# Determine PDF content based on input
if pdf_file:
    pdf_bytes = pdf_file.read()
elif pdf_url:
    pdf_bytes = fetch_pdf_from_url(pdf_url)
else:
    pdf_bytes = None

if pdf_bytes:
    reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
    total_pages = len(reader.pages)

    col1, col2 = st.columns([1, 2])

    with col1:
        pdf_viewer(input=pdf_bytes, height=600)

    with col2:
        page_numbers = st.multiselect("Select pages to read", list(range(1, total_pages + 1)), default=[1])
        
        page_texts = ""
        for page_num in page_numbers:
            page_text = reader.pages[page_num - 1].extract_text()
            if page_text:
                page_texts += page_text + "\n\n"
        
        if page_texts.strip():
            st.subheader("📖 Combined Text from Selected Pages")
            st.text_area("Text", page_texts, height=300)

            try:
                detected_lang = detect(page_texts)
                st.info(f"🌐 Detected Language: **{detected_lang.upper()}**")
            except Exception:
                detected_lang = "en"
                st.warning("⚠️ Language detection failed. Defaulting to English.")

            if st.button("🔊 Read Selected Pages Aloud"):
                try:
                    full_text = "\n".join([p.strip() for p in page_texts.split('\n') if p.strip()])
                    tts = gTTS(text=full_text, lang=detected_lang)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        audio_path = tmp_file.name
                        tts.save(audio_path)

                    with open(audio_path, 'rb') as f:
                        st.audio(f.read(), format="audio/mp3")
                except Exception as e:
                    st.error(f"❌ Speech synthesis failed: {e}")

            if st.checkbox("💬 Ask a question about the selected pages (Ollama)"):
                question = st.text_input("Ask your question:")
                if question:
                    with st.spinner("Thinking..."):
                        try:
                            llm = Ollama(model="llama3")
                            chain = load_qa_chain(llm, chain_type="stuff")
                            docs = [Document(page_content=page_texts)]
                            answer = chain.run(input_documents=docs, question=question)
                            st.success(answer)
                        except Exception as e:
                            st.error(f"❌ Ollama Error: {e}")
        else:
            st.warning("❌ No text to speak.")
else:
    st.info("📂 Please upload a PDF file or enter a URL to begin.")
