import streamlit as st
import PyPDF2
from langdetect import detect
from streamlit_pdf_viewer import pdf_viewer
from io import BytesIO
from gtts import gTTS
from langchain_community.llms import Ollama
from langchain.chains.question_answering import load_qa_chain
from langchain.docstore.document import Document
import tempfile
import os
from pydub import AudioSegment
import requests

st.set_page_config(page_title="TakTak", layout="wide")
st.title("📄 TakTaK PDF Reader with Multilingual Audio Assistance")

# Sidebar settings
st.sidebar.header("🎙️ Speech Settings")
speech_speed = st.sidebar.slider("Speech Speed (%)", 50, 150, 100)

# --- Utility functions ---

# Fetch PDF from URL
def fetch_pdf_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            st.error("❌ Failed to download PDF from URL.")
            return None
    except Exception as e:
        st.error(f"❌ Error fetching PDF: {e}")
        return None

# Split long text into chunks
def split_text(text, max_chars=1000):
    sentences = text.split('. ')
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 < max_chars:
            current += sentence + ". "
        else:
            chunks.append(current.strip())
            current = sentence + ". "
    if current:
        chunks.append(current.strip())
    return chunks

# Generate audio from text using gTTS
def generate_tts_audio(full_text, lang='en'):
    chunks = split_text(full_text, 1000)
    final_audio = AudioSegment.empty()

    for i, chunk in enumerate(chunks):
        tts = gTTS(text=chunk, lang=lang, slow=(speech_speed < 100))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_chunk:
            tts.save(tmp_chunk.name)
            segment = AudioSegment.from_file(tmp_chunk.name, format="mp3")
            final_audio += segment

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_final:
        final_audio.export(tmp_final.name, format="mp3")
        return tmp_final.name

# --- Main logic ---

# PDF Upload or URL
pdf_file = st.file_uploader("Upload your PDF", type=["pdf"])
pdf_url = st.text_input("Or, enter a PDF URL")
pdf_bytes = pdf_file.read() if pdf_file else fetch_pdf_from_url(pdf_url) if pdf_url else None

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
            text = reader.pages[page_num - 1].extract_text()
            if text:
                page_texts += text + "\n\n"

        if page_texts.strip():
            st.subheader("📖 Combined Text from Selected Pages")
            st.text_area("Text", page_texts, height=300)

            try:
                detected_lang = detect(page_texts)
                st.info(f"🌐 Detected Language: **{detected_lang.upper()}**")
            except:
                detected_lang = "en"
                st.warning("⚠️ Language detection failed. Defaulting to English.")

            if st.button("🔊 Read Selected Pages Aloud"):
                try:
                    full_text = "\n".join([p.strip() for p in page_texts.split('\n') if p.strip()])
                    audio_path = generate_tts_audio(full_text, lang=detected_lang)

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
            st.warning("❌ No text to process.")
else:
    st.info("📂 Please upload a PDF or enter a URL to begin.")
