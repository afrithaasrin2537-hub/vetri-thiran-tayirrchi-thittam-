import os
import io
import requests
import streamlit as st
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF

st.set_page_config(page_title="LegalEase - AI Legal Document Generator", layout="centered", page_icon="⚖️")

LOGO_PATH = os.path.join("assets", "logo.png")

class BrandedPDF(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 33)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, 'LegalEase - Branded Document', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'LegalEase Inc. | contact@legalease.com | All Rights Reserved', 0, 0, 'C')

def sanitize_text(text: str) -> str:
    return text.encode('latin-1', 'replace').decode('latin-1')

def format_docx(text: str, doc_type: str) -> io.BytesIO:
    doc = Document()
    
    if os.path.exists(LOGO_PATH):
        doc.add_picture(LOGO_PATH, width=Inches(2))
        
    title = doc.add_heading(doc_type, level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    for paragraph in text.split('\n'):
        if paragraph.strip():
            p = doc.add_paragraph(paragraph)
            p.style.font.name = 'Times New Roman'
            p.style.font.size = Pt(11)
        
    section = doc.sections[0]
    footer = section.footer
    f_p = footer.paragraphs[0]
    f_p.text = "LegalEase Inc. | contact@legalease.com | All Rights Reserved"
    f_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def format_pdf(text: str, doc_type: str) -> io.BytesIO:
    pdf = BrandedPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    
    clean_text = sanitize_text(text)
    for line in clean_text.split('\n'):
        pdf.multi_cell(0, 6, txt=line)
        
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def format_html_preview(text: str) -> str:
    formatted = text.replace('\n', '<br>')
    return f"""
    <div style="background-color: #1e293b; color: #f8fafc; padding: 20px; border-radius: 8px; font-family: monospace; max-height: 400px; overflow-y: auto;">
        {formatted}
    </div>
    """

# Interface Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)

st.markdown("<h2 style='text-align: center;'>AI Legal Document Generator</h2>", unsafe_allow_html=True)

# Input Forms
document_type = st.text_input("Document Type (e.g. Agreement, Contract, NDA)", "Freelance Work Contract")
parties = st.text_area("Parties Involved", "Jane Doe (Service Provider), TechNova Inc. (Client)")
terms = st.text_area("Terms & Conditions (Use semicolons for bullet points)", "Work must be delivered by May 15, 2025; Payment will be made within 7 days of invoice; The client retains intellectual property rights.")
dates = st.text_input("Effective Date", "April 15, 2025")

if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "show_edit" not in st.session_state:
    st.session_state.show_edit = False

if st.button("Generate Document"):
    with st.spinner("Generating document..."):
        try:
            res = requests.post("http://localhost:8000/generate", json={
                "document_type": document_type,
                "parties": parties,
                "terms": terms,
                "dates": dates
            })
            if res.status_code == 200:
                st.session_state.generated_text = res.json().get("document", "")
                st.session_state.show_edit = False
                st.success("Document Generated Successfully!")
            else:
                st.error(f"Backend API Error: {res.text}")
        except Exception as e:
            st.error(f"Could not connect to FastAPI server at http://localhost:8000: {e}")

if st.session_state.generated_text:
    st.subheader("Document Preview")
    st.markdown(format_html_preview(st.session_state.generated_text), unsafe_allow_html=True)
    
    if st.button("✏️ Click to Edit Document"):
        st.session_state.show_edit = not st.session_state.show_edit

    if st.session_state.show_edit:
        st.session_state.generated_text = st.text_area(
            "Edit Document Below:", 
            value=st.session_state.generated_text, 
            height=300
        )

    st.markdown("### Export Options")
    col_a, col_b, col_c = st.columns(3)
    file_prefix = document_type.lower().replace(' ', '_')
    
    with col_a:
        st.download_button(
            "📄 Download as .TXT", 
            data=st.session_state.generated_text, 
            file_name=f"{file_prefix}.txt", 
            mime="text/plain"
        )
    with col_b:
        docx_data = format_docx(st.session_state.generated_text, document_type)
        st.download_button(
            "📝 Download as .DOCX", 
            data=docx_data, 
            file_name=f"{file_prefix}.docx", 
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    with col_c:
        pdf_data = format_pdf(st.session_state.generated_text, document_type)
        st.download_button(
            "📕 Download as .PDF", 
            data=pdf_data, 
            file_name=f"{file_prefix}.pdf", 
            mime="application/pdf"
        )