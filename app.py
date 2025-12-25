import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os

st.set_page_config(page_title="Invoice OCR", layout="centered")
st.title("📄 Invoice OCR Automation")
st.write("Upload an invoice image to extract key details")

uploaded = st.file_uploader("Upload Invoice", type=["jpg", "png", "jpeg"])

def clean_text(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_invoice_number(text):
    patterns = [
        r"invoice\s*(number|no|#)\s*[:\-]?\s*([A-Z0-9\-]+)",
        r"inv\s*(no|#)\s*[:\-]?\s*([A-Z0-9\-]+)"
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(2)
    return "Not found"

def extract_dates(text):
    invoice_date = "Not found"
    due_date = "Not found"

    date_patterns = [
        r"(invoice date|date)\s*[:\-]?\s*([0-9\/\-\.]+)",
        r"(due date|payment due)\s*[:\-]?\s*([0-9\/\-\.]+)"
    ]

    for label, date in re.findall(r"(invoice date|date|due date|payment due)\s*[:\-]?\s*([0-9\/\-\.]+)", text, re.I):
        if "due" in label.lower():
            due_date = date
        else:
            invoice_date = date

    return invoice_date, due_date

def extract_total(text):
    patterns = [
        r"grand total\s*[:\-]?\s*([₹$]?\s?[0-9,]+\.\d{2})",
        r"total amount\s*[:\-]?\s*([₹$]?\s?[0-9,]+\.\d{2})",
        r"\btotal\b\s*[:\-]?\s*([₹$]?\s?[0-9,]+\.\d{2})"
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).replace(" ", "")
    return "Not found"

def extract_vendor(raw_text):
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    for line in lines[:6]:
        if not re.search(r"invoice|date|bill|total", line, re.I):
            if len(line.split()) >= 2:
                return line
    return "Not found"

if uploaded:
    st.image(uploaded, width=400)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(uploaded.getvalue())
        img_path = tmp.name

    try:
        image = Image.open(img_path)
        raw_text = pytesseract.image_to_string(image, config="--oem 3 --psm 6")
        text = clean_text(raw_text)

        invoice_no = extract_invoice_number(text)
        invoice_date, due_date = extract_dates(text)
        total_amount = extract_total(text)
        vendor = extract_vendor(raw_text)

        st.success("✅ Invoice processed successfully")

        st.subheader("Extracted Details")
        st.write(f"**Vendor / Company:** {vendor}")
        st.write(f"**Invoice Number:** {invoice_no}")
        st.write(f"**Invoice Date:** {invoice_date}")
        st.write(f"**Due Date:** {due_date}")
        st.write(f"**Total Amount:** {total_amount}")

        with st.expander("🔍 View OCR Text"):
            st.text(raw_text)

    except Exception as e:
        st.error("❌ OCR processing failed safely")
        st.code(str(e))

    finally:
        os.remove(img_path)
