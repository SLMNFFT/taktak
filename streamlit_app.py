import streamlit as st
import PyPDF2
from langdetect import detect
from streamlit_pdf_viewer import pdf_viewer
from io import BytesIO
import pyttsx3
import tempfile
import os
import time
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

    # Create two columns for layout
    col1, col2 = st.columns([1, 2])  # First column for the PDF viewer, second for the rest of the content

    # Display PDF viewer in the left column (fixed height with scroll)
    with col1:
        pdf_viewer(input=pdf_bytes, height=600)  # Set the height to your preference

    # Display other content (text, language detection, etc.) in the right column
    with col2:
        # Select multiple pages
        page_numbers = st.multiselect("Select pages to read", list(range(1, total_pages + 1)), default=[1])
        
        # Combine text from the selected pages
        page_texts = ""
        for page_num in page_numbers:
            page_text = reader.pages[page_num - 1].extract_text()
            if page_text:
                page_texts += page_text + "\n\n"  # Add space between pages
        
        if page_texts.strip():
            st.subheader("📖 Combined Text from Selected Pages")
            st.text_area("Text", page_texts, height=300)

            # Language detection
            try:
                detected_lang = detect(page_texts)
                st.info(f"🌐 Detected Language: **{detected_lang.upper()}**")
            except Exception:
                detected_lang = "en"
                st.warning("⚠️ Language detection failed. Defaulting to English.")

            # Read aloud
            # ...existing code...
            if st.button("🔊 Read Selected Pages Aloud"):
                try:
                    combined_text = "\n\n".join([p.strip() for p in page_texts.split('\n') if p.strip()])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        audio_path = tmp_file.name

                    engine.save_to_file(combined_text, audio_path)
                    engine.runAndWait()

                    waited = 0
                    while (not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0) and waited < 5:
                        time.sleep(0.2)
                        waited += 0.2

                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                        with open(audio_path, 'rb') as f:
                            st.audio(f.read(), format="audio/wav")
                    else:
                       st.error("❌ Audio file was not created.")
                except Exception as e:
                    st.error(f"❌ Speech synthesis failed: {e}")

# ...existing code...

            # Ollama Q&A
            if st.checkbox("💬 Ask a question about the selected pages"):
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
