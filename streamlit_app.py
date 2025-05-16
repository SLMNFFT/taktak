import streamlit as st
import re
import tempfile
import base64
from pypdf import PdfReader
from PIL import Image
from fpdf import FPDF
from gtts import gTTS
import io

st.set_page_config(
    page_title="Peepit Audiobook",
    layout="wide",
    page_icon="🎧",
)

st.markdown("""
<style>
/* Styling for the Streamlit page */
[data-testid="stColumns"] {
    display: flex;
    align-items: stretch;
    gap: 2rem;
    justify-content: center;
}

body, pre {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #ddd;
    background-color: #0f1123;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
}

.main-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 20px;
    height: 100%;
    width: 100%;
    text-align: center;
}

.st-expanderHeader {
    background-color: #2ecc71 !important;
}

.preview-card {
    background: #1A1B2F;
    border-radius: 15px;
    padding: 1.5rem;
    height: 100%;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 15px rgba(10, 10, 30, 0.5);
}

.scroll-container {
    flex: 1;
    overflow-y: auto;
    padding-right: 0.5rem;
    scrollbar-width: thin;
    scrollbar-color: #4e5aee #1A1B2F;
}

.preview-image-container {
    display: grid;
    gap: 1rem;
}

.preview-image {
    background: #2B2D42;
    border-radius: 8px;
    padding: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.preview-image img {
    border-radius: 6px;
    margin-bottom: 0.5rem;
    width: 100%;
    height: auto;
    object-fit: contain;
    user-select: none;
}

/* Custom upload button styling */
.upload-button {
    background: #2ecc71;
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 12px;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    font-weight: 600;
    font-size: 1.8rem;
    cursor: pointer;
    user-select: none;
    width: 100%;
    max-width: 400px;
    transition: background-color 0.3s ease;
    margin: 3rem auto 2rem auto;
    display: block;
}
.upload-button:hover {
    background: #27ae60;
}
</style>
""", unsafe_allow_html=True)


# --- HELPER FUNCTIONS ---

def extract_text_from_pdf(pdf_path, selected_pages):
    reader = PdfReader(pdf_path)
    extracted_text = ""
    pages_without_text = []

    if not selected_pages:
        return "", []

    for i in selected_pages:
        if i < 1 or i > len(reader.pages):
            continue
        page = reader.pages[i - 1]
        text = page.extract_text()
        if text and text.strip():
            extracted_text += f"--- Page {i} ---\n{text}\n\n"
        else:
            pages_without_text.append(i)

    # You can add OCR here if needed

    return extracted_text.strip(), pages_without_text

def generate_audio(text, lang="en", rate=1.0, gender="male"):
    tts = gTTS(text=text, lang=lang, slow=False)
    temp_audio_path = tempfile.mktemp(suffix=".mp3")
    tts.save(temp_audio_path)
    return temp_audio_path

def save_images_as_pdf(images):
    pdf = FPDF()
    
    for img in images:
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_img_file:
            temp_img_file.write(bio.read())
            temp_img_file_path = temp_img_file.name
        
        pdf.add_page()
        pdf.image(temp_img_file_path, x=10, y=10, w=pdf.w - 20)

    pdf_path = tempfile.mktemp(suffix=".pdf")
    pdf.output(pdf_path)
    
    return pdf_path


# --- MAIN APP ---

def main():
# Hidden uploader with no label (must be in the app so Streamlit gets file)
uploaded_file = st.file_uploader("", type=["pdf"], label_visibility="hidden", key="hidden_uploader")

# Big green upload button triggers the hidden input immediately on click
st.markdown("""
<style>
.center-bottom-upload {
    display: flex;
    justify-content: center;  /* center horizontally */
    align-items: center;      /* center vertically */
    height: 100vh;            /* full viewport height */
    margin: 0;                /* no margin */
}

#big-upload-label {
    background: #2ecc71;
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 12px;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    font-weight: 600;
    font-size: 1.8rem;
    cursor: pointer;
    user-select: none;
    width: 100%;
    max-width: 400px;
    transition: background-color 0.3s ease;
}

#big-upload-label:hover {
    background: #27ae60;
}

input[type="file"] {
    display: none;
}
</style>

<div class="center-bottom-upload">
    <button id="big-upload-label" type="button" role="button" tabindex="0">
        🎧 peep my file
    </button>
</div>

<script>
const btn = document.getElementById('big-upload-label');
const hiddenUploader = window.parent.document.querySelector('input[data-testid="stFileUploader"]');

btn.addEventListener('click', () => {
    if(hiddenUploader){
        hiddenUploader.click();
    }
});
</script>
""", unsafe_allow_html=True)

    pdf_url = st.text_input("Or enter a PDF URL")

    # Option 2: show file uploader only after clicking this button
    if "upload_clicked" not in st.session_state:
        st.session_state.upload_clicked = False

    def click_upload():
        st.session_state.upload_clicked = True

    st.button("🎧 Peep my file", on_click=click_upload, key="upload_button")

    uploaded_file = None
    if st.session_state.upload_clicked:
        uploaded_file = st.file_uploader("Upload your PDF file", type=["pdf"])

    pdf_path = None
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = tmp.name

    if pdf_path:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        selected_pages = st.multiselect("Select pages to process", list(range(1, total_pages + 1)), default=[1])

        if not selected_pages:
            st.error("Please select at least one valid page")
            return

        with st.spinner("🔍 Analyzing document..."):
            full_text, ocr_pages = extract_text_from_pdf(pdf_path, selected_pages)
            if not full_text:
                st.error("No extractable text found in selected pages")
                return

            col_left, col_right = st.columns(2)

            # --- LEFT COLUMN: TEXT + AUDIO ---
            with col_left:
                with st.expander("📜 Extracted Text", expanded=True):
                    search_term = st.text_input("🔎 Search within text", "")
                    filtered_text = full_text
                    if search_term:
                        filtered_text = re.sub(
                            f"(?i)({re.escape(search_term)})",
                            r"<mark style='background-color:yellow'>\1</mark>",
                            filtered_text,
                            flags=re.DOTALL,
                        )
                    st.markdown(filtered_text.replace("\n", "<br>").replace("  ", " "), unsafe_allow_html=True)

            # --- RIGHT COLUMN: AUDIO ---
            with col_right:
                with st.expander("🔊 Audio Playback", expanded=True):
                    lang = st.radio("Select language", ("en", "es", "fr", "de"))
                    rate = st.slider("Speed", 0.5, 2.0, 1.0, 0.1)
                    gender = st.radio("Select voice type", ("male", "female"))

                    audio_path = generate_audio(filtered_text, lang=lang, rate=rate, gender=gender)
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/mp3")

            # --- IMAGE EXPORT (Dummy Images) ---
            image1 = Image.new("RGB", (300, 300), color="blue")
            image2 = Image.new("RGB", (300, 300), color="green")
            
            st.download_button(
                "📥 Export PDF", 
                save_images_as_pdf([image1, image2]), 
                "exported_images.pdf", 
                "application/pdf", 
                key="export_pdf"
            )


if __name__ == "__main__":
    main()
