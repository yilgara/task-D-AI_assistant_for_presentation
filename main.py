
import streamlit as st
import tempfile
from docx import Document
import pdfplumber
import os
from utils.slide  import parse_gpt_response
from utils.slide import generate_pptx
from utils.prompt import get_presentation

def read_pdf(file_path):

    text = ''
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text.strip()

def read_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.docx':
        doc = Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])

    elif ext == '.pdf':
        return read_pdf(file_path)
    else:
        raise ValueError("Unsupported file format: Only .docx and .pdf are supported.")




def streamlit():
    st.title("Sənəddən Təqdimat Yaratma")

    # File upload
    uploaded_file = st.file_uploader("PDF və ya DOCX faylını yükləyin", type=["pdf", "docx"])

    slide_count = st.number_input("Slaydların sayı", min_value=5, step=1)

    include_visuals = st.radio(
        "Vizuaları ümumi slayd sayına daxil edək?",
        ("Bəli", "Xeyr"),
        index=1,
        help="Vizual elementləri slayd sayına daxil etmək üçün 'Bəli' seçin."
    )

    if uploaded_file:
        generate_btn = st.button("PPTX Yarat")
    else:
        generate_btn = False

    if "pptx_bytes" not in st.session_state:
        st.session_state.pptx_bytes = None
    if "generation_done" not in st.session_state:
        st.session_state.generation_done = False

    if uploaded_file and generate_btn:
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[-1]) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            # Step 1: Extract text
            with st.spinner("Fayl oxunur və təqdimat hazırlanır..."):
                doc_text = read_file(tmp_path)
                gpt_response = get_presentation(doc_text, slide_count, include_visuals=(include_visuals == "Bəli"))
                slides = parse_gpt_response(gpt_response)

                output_filename = "generated_presentation.pptx"
                generate_pptx(slides, output_filename)

                with open(output_filename, "rb") as f:
                    st.session_state.pptx_bytes = f.read()

            st.session_state.generation_done = True
            st.success("Təqdimat uğurla yaradıldı!")

        except Exception as e:
            st.error(f"Error: {e}")

    if st.session_state.generation_done and st.session_state.pptx_bytes:
        st.download_button(
            label="PPTX Faylını Yüklə",
            data=st.session_state.pptx_bytes,
            file_name="generated_presentation.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )


if __name__ == "__main__":
    streamlit()