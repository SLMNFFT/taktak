import streamlit as st
import PyPDF2
from langdetect import detect
from streamlit_pdf_viewer import pdf_viewer
from io import BytesIO
import pyttsx3
import tempfile
import os
import time
import wave
import requests

from langchain_community.llms import Ollama
from langchain.chains.question_answering import load_qa_chain
from langchain.docstore.document import Document

st.set_page_config(page_title="TakTak", layout="wide")
st.title("📄 TakTaK PDF Reader with Multilingual Audio Assistance")

# Initialize pyttsx3
engine = pyttsx3.init()

# Get available voices
voices = engine.getProperty('voices')
voice_options = {
    f"{v.name} ({v.languages[0] if v.languages else 'unknown'})": v.id
    for v in voices
}

default_voice = list(voice_options.keys())[0]

# Sidebar controls
st.sidebar.header("🎙️ Speech Settings")
selected_voice = st.sidebar.selectbox("Choose Voice", options=list(voice_options.keys()), index=0)
rate = st.sidebar.slider("Speech Rate", 100, 300, 150)
volume = st.sidebar.slider("Volume", 0.0, 1.0, 1.0)

# Apply TTS settings
engine.setProperty('rate', rate)
engine.setProperty('volume', volume)
engine.setProperty('voice', voice_options[selected_voice])

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

# Split text into chunks
def split_text(text, max_length=500):
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) < max_length:
            current_chunk += para + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# Concatenate audio chunks
def concatenate_audio(files, output_path):
    with wave.open(output_path, 'wb') as output:
        with wave.open(files[0], 'rb') as first:
            output.setparams(first.getparams())
        for file in files:
            with wave.open(file, 'rb') as f:
                output.writeframes(f.readframes(f.getnframes()))

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
                    text_chunks = split_text(page_texts, max_length=500)
                    temp_files = []
                    for i, chunk in enumerate(text_chunks):
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                        temp_files.append(temp_file.name)
                        engine.save_to_file(chunk, temp_file.name)
                    
                    engine.runAndWait()

                    final_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
                    concatenate_audio(temp_files, final_audio)

                    with open(final_audio, 'rb') as f:
                        st.audio(f.read(), format="audio/wav")

                    for f_path in temp_files:
                        os.remove(f_path)
                    os.remove(final_audio)

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
