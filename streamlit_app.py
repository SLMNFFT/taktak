import streamlit as st
from PyPDF2 import PdfReader
from langdetect import detect
from gtts import gTTS
from io import BytesIO
import tempfile
import os
import requests
from streamlit_pdf_viewer import pdf_viewer
from langchain_community.llms import Ollama
from langchain.chains.question_answering import load_qa_chain
from langchain.docstore.document import Document

st.set_page_config(page_title="TakTak", layout="wide")
st.title("📄 TakTaK PDF Reader with Multilingual Audio Assistance")

# Sidebar
st.sidebar.header("🔈 Audio Settings")
speech_lang = st.sidebar.text_input("Language code (e.g. en, fr, de, ar)", value="en")
slow = st.sidebar.checkbox("Speak Slowly?", value=False)

# Upload or URL input
pdf_file = st.file_uploader("Upload a PDF", type=["pdf"])
pdf_url = st.text_input("Or enter a PDF URL")

# Load PDF
def load_pdf(pdf_bytes):
    return PdfReader(BytesIO(pdf_bytes))

def fetch_pdf_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"❌ Failed to fetch PDF: {e}")
        return None

# Determine PDF bytes
pdf_bytes = None
if pdf_file:
    pdf_bytes = pdf_file.read()
elif pdf_url:
    pdf_bytes = fetch_pdf_from_url(pdf_url)

if pdf_bytes:
    reader = load_pdf(pdf_bytes)
    total_pages = len(reader.pages)

    # Layout
    left, right = st.columns([1, 1.5])

    with right:
        st.subheader("📄 PDF Preview")
        pdf_viewer(input=pdf_bytes, height=700)

    with left:
        page_numbers = st.multiselect("Select pages to read", list(range(1, total_pages + 1)), default=[1])
        extracted_text = ""

        for num in page_numbers:
            text = reader.pages[num - 1].extract_text()
            if text:
                extracted_text += text + "\n\n"

        if extracted_text.strip():
            st.subheader("📖 Extracted Text")
            st.text_area("Text", extracted_text, height=300)

            # Language detection
            try:
                lang_detected = detect(extracted_text)
                st.info(f"🌍 Detected Language: **{lang_detected.upper()}**")
            except:
                lang_detected = "en"
                st.warning("⚠️ Language detection failed. Defaulted to English.")

            # Read aloud
            if st.button("🔊 Read Aloud"):
                try:
                    tts = gTTS(text=extracted_text, lang=speech_lang, slow=slow)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        audio_path = tmp_file.name
                        tts.save(audio_path)
                    with open(audio_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")
                    os.remove(audio_path)
                except Exception as e:
                    st.error(f"❌ TTS failed: {e}")

            # Q&A
            if st.checkbox("💬 Ask a question (Ollama)"):
                question = st.text_input("Enter your question:")
                if question:
                    with st.spinner("Thinking..."):
                        try:
                            llm = Ollama(model="llama3")
                            chain = load_qa_chain(llm, chain_type="stuff")
                            docs = [Document(page_content=extracted_text)]
                            answer = chain.run(input_documents=docs, question=question)
                            st.success(answer)
                        except Exception as e:
                            st.error(f"❌ Ollama error: {e}")
        else:
            st.warning("📭 No text extracted from selected pages.")
else:
    st.info("📂 Please upload a PDF or enter a valid URL to continue.")
