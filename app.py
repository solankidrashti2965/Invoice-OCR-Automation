import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os
import pdf2image

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")
st.title("📄 Invoice OCR Automation")
st.write("Upload invoice (Image or PDF)")

uploaded = st.file_uploader(
    "Upload Invoice",
    type=["jpg", "jpeg", "png", "pdf"]
)

def extract_amount(keyword, text):
    pattern = rf"{keyword}.*?(₹|Rs\.?|INR|\$)?\s*([\d,]+\.\d+)"
    match = re.search(pattern, text, re.I | re.S)
    if match:
        symbol = match.group(1) or ""
        amount = match.group(2)
        return f"{symbol} {amount}".strip()
    return "Not found"

def extract_date(text, keyword):
    pattern = rf"{keyword}.*?(\d{{4}}[-/]\d{{2}}[-/]\d{{2}}|\d{{2}}[-/]\d{{2}}[-/]\d{{4}})"
    match = re.search(pattern, text, re.I)
    return match.group(1) if match else "Not found"

if uploaded:

    try:
        # --------------------
        # Handle PDF
        # --------------------
        if uploaded.type == "application/pdf":
            images = pdf2image.convert_from_bytes(uploaded.read())
            image = images[0]
        else:
            image = Image.open(uploaded).convert("RGB")

        st.image(image, width=450)

        # OCR
        raw_text = pytesseract.image_to_string(image, config="--oem 3 --psm 6")

        if not raw_text.strip():
            st.error("No readable text found.")
            st.stop()

        # --------------------
        # Vendor (top section)
        # --------------------
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        vendor = "Not found"
        for line in lines[:8]:
            if not any(k in line.lower() for k in ["invoice", "date", "gst", "total", "tax"]):
                if len(line) > 4:
                    vendor = line
                    break

        # --------------------
        # Invoice Number
        # --------------------
        inv_patterns = [
            r"invoice\s*(no|number|#)\s*[:\-]?\s*([\w\-]+)",
            r"\bINV[-\w]+\b"
        ]

        invoice_no = "Not found"
        for p in inv_patterns:
            m = re.search(p, raw_text, re.I)
            if m:
                invoice_no = m.group(2) if len(m.groups()) > 1 else m.group(0)
                break

        # --------------------
        # Dates
        # --------------------
        invoice_date = extract_date(raw_text, "invoice date")
        due_date = extract_date(raw_text, "due date")

        # --------------------
        # Subtotal / Tax / Total
        # --------------------
        subtotal = extract_amount("subtotal|taxable amount", raw_text)
        tax = extract_amount("tax|gst|igst|cgst|sgst", raw_text)
        total = extract_amount("grand total|total amount|amount due|total", raw_text)

        # --------------------
        # Phone
        # --------------------
        phone_match = re.search(r"\b\d{10}\b", raw_text)
        phone = phone_match.group() if phone_match else "Not found"

        # --------------------
        # Display
        # --------------------
        st.success("✅ Invoice processed successfully")

        with st.expander("📄 Extracted Details"):
            st.write(f"**Vendor / Company:** {vendor}")
            st.write(f"**Invoice Number:** {invoice_no}")
            st.write(f"**Invoice Date:** {invoice_date}")
            st.write(f"**Due Date:** {due_date}")
            st.write(f"**Subtotal:** {subtotal}")
            st.write(f"**Tax:** {tax}")
            st.write(f"**Total Amount:** {total}")
            st.write(f"**Phone / Account:** {phone}")

            st.markdown("---")
            st.markdown("### 🔍 Raw OCR Text")
            st.text(raw_text)

    except Exception as e:
        st.error("OCR processing failed safely")
        st.code(str(e))
