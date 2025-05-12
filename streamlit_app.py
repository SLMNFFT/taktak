import streamlit as st
from PyPDF2 import PdfReader
from langdetect import detect
from streamlit_pdf_viewer import pdf_viewer
from io import BytesIO
from gtts import gTTS
import tempfile
import os
import requests
from langchain_community.llms import Ollama
from langchain.chains.question_answering import load_qa_chain
from langchain.docstore.document import Document

# App layout
st.set_page_config(page_title="TakTak", layout="wide")
st.title("📄 TakTaK PDF Reader with Multilingual Audio Assistance")

# Sidebar controls
st.sidebar.header("🎙️ Speech Settings")
language_code = st.sidebar.text_input("Speech language (e.g., en, fr, de, es)", value="en")
speech_speed = st.sidebar.radio("Speech speed", options=["Normal", "Slow"], index=0)
slow = speech_speed == "Slow"

# Upload or URL
pdf_file = st.file_uploader("📂 Upload a PDF file", type=["pdf"])
pdf_url = st.text_input("🌐 Or enter a PDF URL")

# Fetch PDF from URL
def fetch_pdf_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            st.error("❌ Failed to download PDF.")
            return None
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None

# Load PDF
if pdf_file:
    pdf_bytes = pdf_file.read()
elif pdf_url:
    pdf_bytes = fetch_pdf_from_url(pdf_url)
else:
    pdf_bytes = None

if pdf_bytes:
    reader = PdfReader(BytesIO(pdf_bytes))
    total_pages = len(reader.pages)

    # Columns: Left for controls/text/audio, Right for preview
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("📑 PDF Preview")
        pdf_viewer(input=pdf_bytes, height=600)

    with col1:
        st.subheader("📖 Select Pages")
        page_numbers = st.multiselect("Select pages", list(range(1, total_pages + 1)), default=[1])

        combined_text = ""
        for page in page_numbers:
            text = reader.pages[page - 1].extract_text()
            if text:
                combined_text += text + "\n\n"

        if combined_text.strip():
            st.text_area("📝 Extracted Text", value=combined_text, height=300)

            # Detect language
            try:
                detected_lang = detect(combined_text)
                st.info(f"🌐 Detected Language: **{detected_lang.upper()}**")
            except Exception:
                detected_lang = "en"
                st.warning("⚠️ Language detection failed. Defaulting to English.")

            # Read aloud
            if st.button("🔊 Read Aloud"):
                try:
                    tts = gTTS(text=combined_text, lang=language_code, slow=slow)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        tts.save(tmp_file.name)
                        st.audio(tmp_file.name, format="audio/mp3")
                except Exception as e:
                    st.error(f"❌ TTS failed: {e}")

            # Ollama QA
            if st.checkbox("💬 Ask a question (via Ollama)"):
                question = st.text_input("Ask your question:")
                if question:
                    with st.spinner("🧠 Thinking..."):
                        try:
                            llm = Ollama(model="llama3")
                            chain = load_qa_chain(llm, chain_type="stuff")
                            docs = [Document(page_content=combined_text)]
                            answer = chain.run(input_documents=docs, question=question)
                            st.success(answer)
                        except Exception as e:
                            st.error(f"❌ Ollama Error: {e}")
        else:
            st.warning("📭 No text extracted from selected pages.")
else:
    st.info("📥 Upload a PDF or provide a URL to get started.")
