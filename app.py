import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os

st.set_page_config(page_title="Invoice OCR", layout="centered")
st.title("📄 Invoice OCR Automation")

st.write("Upload a valid invoice image (JPG / PNG)")

uploaded = st.file_uploader("Upload Invoice", type=["jpg", "jpeg", "png"])

def clean(text):
    return text.replace("\n", " ").strip()

def extract(patterns, text):
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return clean(m.group(1))
    return "Not found"

if uploaded:
    st.image(uploaded, width=450)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
        f.write(uploaded.getvalue())
        img_path = f.name

    try:
        img = Image.open(img_path)
        text = pytesseract.image_to_string(img, config="--oem 3 --psm 6")

        if len(text.strip()) < 30:
            st.error("❌ Not a valid invoice image")
            st.stop()

        text_lower = text.lower()

        
        invoice_keywords = ["invoice", "total", "amount", "subtotal"]
        if not any(k in text_lower for k in invoice_keywords):
            st.error("❌ This does not look like an invoice")
            st.stop()

        
        invoice_no = extract([
            r"invoice\s*#?\s*[:\-]?\s*([A-Z0-9\-]+)"
        ], text)

        invoice_date = extract([
            r"invoice\s*date\s*[:\-]?\s*([0-9\/\-\.]+)",
            r"date\s*[:\-]?\s*([0-9\/\-\.]+)"
        ], text)

        due_date = extract([
            r"due\s*date\s*[:\-]?\s*([0-9\/\-\.]+)"
        ], text)

        vendor = extract([
            r"bill\s*from\s*[:\-]?\s*([A-Za-z &]+)",
            r"from\s*[:\-]?\s*([A-Za-z &]+)",
        ], text)

        subtotal = extract([
            r"subtotal\s*[:\-]?\s*[₹$]?\s*([\d,]+\.\d{2})"
        ], text)

        tax = extract([
            r"(cgst|sgst|tax)\s*[:\-]?\s*[₹$]?\s*([\d,]+\.\d{2})"
        ], text)

        total = extract([
            r"total\s*[:\-]?\s*[₹$]?\s*([\d,]+\.\d{2})",
            r"amount\s*due\s*[:\-]?\s*[₹$]?\s*([\d,]+\.\d{2})"
        ], text)

        
        st.success("✅ Invoice processed successfully")

        st.subheader("Extracted Details")
        st.write("**Invoice Number:**", invoice_no)
        st.write("**Vendor / Company:**", vendor)
        st.write("**Invoice Date:**", invoice_date)
        st.write("**Due Date:**", due_date)
        st.write("**Subtotal:**", subtotal)
        st.write("**Tax:**", tax)
        st.write("**Total Amount:**", total)

        with st.expander("🔍 OCR Text (Debug)"):
            st.text(text)

    except Exception as e:
        st.error("❌ OCR processing failed safely")
        st.code(str(e))

    finally:
        os.remove(img_path)
