import streamlit as st
from PIL import Image
import pytesseract
import re
import pdf2image
import pdfplumber
import io

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")
st.title("📄 Smart Invoice OCR Automation")

uploaded = st.file_uploader(
    "Upload Invoice",
    type=["jpg", "jpeg", "png", "pdf"]
)

# -------------------------------------------------
# TEXT EXTRACTION (SMART METHOD)
# -------------------------------------------------
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_image(image):
    image = image.convert("L")  # grayscale
    return pytesseract.image_to_string(
        image,
        config="--oem 3 --psm 6"
    )

# -------------------------------------------------
# GENERIC FIELD EXTRACTION
# -------------------------------------------------
def find_first(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group().strip()
    return "Not found"

if uploaded:

    try:
        raw_text = ""

        # ---------------- PDF ----------------
        if uploaded.type == "application/pdf":
            raw_text = extract_text_from_pdf(uploaded)

            # If no text found → fallback to OCR
            if not raw_text.strip():
                images = pdf2image.convert_from_bytes(uploaded.read())
                for img in images:
                    raw_text += extract_text_from_image(img)

        # ---------------- IMAGE ----------------
        else:
            image = Image.open(uploaded)
            st.image(image, width=450)
            raw_text = extract_text_from_image(image)

        if not raw_text.strip():
            st.error("❌ No readable text found. Check Tesseract installation.")
            st.stop()

        st.success("✅ Text Extracted Successfully")

        # -------------------------------------------------
        # FIELD PATTERNS (VERY FLEXIBLE)
        # -------------------------------------------------
        vendor = raw_text.split("\n")[0]

        invoice_no = find_first([
            r"invoice\s*(no|number|#)\s*[:\-]?\s*\S+",
            r"\bINV[-\w]+\b"
        ], raw_text)

        date = find_first([
            r"\d{4}[-/]\d{2}[-/]\d{2}",
            r"\d{2}[-/]\d{2}[-/]\d{4}",
            r"\d{2}\s+[A-Za-z]+\s+\d{4}"
        ], raw_text)

        total = find_first([
            r"(grand\s*total|total\s*amount|amount\s*due)[^\d]{0,10}[\d,]+\.?\d*"
        ], raw_text)

        tax = find_first([
            r"(gst|vat|tax)[^\d]{0,10}[\d,]+\.?\d*"
        ], raw_text)

        phone = find_first([
            r"\+?\d[\d\s\-]{8,15}\d"
        ], raw_text)

        # -------------------------------------------------
        # DISPLAY
        # -------------------------------------------------
        with st.expander("📄 Extracted Details"):
            st.write("**Vendor:**", vendor)
            st.write("**Invoice Number:**", invoice_no)
            st.write("**Date:**", date)
            st.write("**Total:**", total)
            st.write("**Tax:**", tax)
            st.write("**Phone:**", phone)

            st.markdown("---")
            st.markdown("### 🔍 Raw Text")
            st.text(raw_text)

    except Exception as e:
        st.error("Processing Failed")
        st.code(str(e))
