import streamlit as st
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
import pdf2image
from gtts import gTTS
import tempfile
import os
from langdetect import detect
import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF

# إعداد الصفحة
st.set_page_config(page_title="PeePit Audiobook", layout="centered")

st.title("🎧 PeePit Audiobook")
st.write("حوّل ملفات PDF الخاصة بك إلى نصوص أو ملفات صوتية")

uploaded_file = st.file_uploader("📤 ارفع ملف PDF", type=["pdf"])

if uploaded_file:
    # تحميل الملف في مجلد مؤقت
    st.success("✅ تم رفع الملف بنجاح!")
    pdf_reader = PdfReader(uploaded_file)
    total_pages = len(pdf_reader.pages)
    selected_pages = st.multiselect(
        "📄 اختر الصفحات التي تريد معالجتها:",
        options=list(range(1, total_pages + 1)),
        default=list(range(1, min(4, total_pages + 1)))
    )

    if st.button("📜 استخراج النص"):
        with st.spinner("جارٍ استخراج النص..."):
            with tempfile.TemporaryDirectory() as path:
                images = pdf2image.convert_from_bytes(uploaded_file.read(), output_folder=path)
                extracted_text = ""

                for i in selected_pages:
                    image = images[i - 1]
                    text = pytesseract.image_to_string(image, lang='ara+eng')
                    extracted_text += f"\n\n--- صفحة {i} ---\n{text}"

                try:
                    lang = detect(extracted_text)
                except:
                    lang = "unknown"

                st.subheader("📜 النص المستخرج:")
                if lang == "ar":
                    reshaped_text = arabic_reshaper.reshape(extracted_text)
                    bidi_text = get_display(reshaped_text)
                    st.markdown(
                        f"<div style='text-align: right; direction: rtl;'>{bidi_text}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.text_area("Extracted Text", extracted_text, height=300)

                # حفظ النص لاستخدامه لاحقًا
                st.session_state["extracted_text"] = extracted_text
                st.session_state["lang"] = lang

    if "extracted_text" in st.session_state:
        st.subheader("🔊 تحويل إلى صوت")
        if st.button("🎙️ إنشاء ملف صوتي"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
                tts = gTTS(text=st.session_state["extracted_text"], lang='ar' if st.session_state["lang"] == "ar" else 'en')
                tts.save(audio_file.name)
                audio_file.seek(0)
                st.audio(audio_file.read(), format="audio/mp3")

        st.subheader("📄 تصدير النص كـ PDF")
        if st.button("⬇️ تنزيل النص كـ PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # تقطيع النص للسطر
            lines = st.session_state["extracted_text"].split("\n")
            for line in lines:
                pdf.cell(200, 10, txt=line, ln=True, align='R' if st.session_state["lang"] == "ar" else 'L')

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
                pdf.output(pdf_file.name)
                st.download_button(
                    label="📥 تحميل ملف PDF",
                    data=open(pdf_file.name, "rb").read(),
                    file_name="peeptit_extracted_text.pdf",
                    mime="application/pdf"
                )