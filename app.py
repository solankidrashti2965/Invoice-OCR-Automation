import streamlit as st
from PIL import Image
import pytesseract
import re
import pdf2image
import io

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")
st.title("📄 Universal Invoice OCR Automation")
st.write("Upload invoice (Image or PDF)")

uploaded = st.file_uploader(
    "Upload Invoice",
    type=["jpg", "jpeg", "png", "pdf"]
)

# ----------------------------
# Clean OCR Text
# ----------------------------
def clean_text(text):
    text = text.replace("\n\n", "\n")
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    return text.strip()

# ----------------------------
# Extract Amount (Flexible)
# ----------------------------
def extract_amount(keywords, text):
    pattern = rf"({keywords}).{{0,40}}?(₹|Rs\.?|INR|\$|€)?\s?([\d,]+\.?\d*)"
    match = re.search(pattern, text, re.I | re.S)
    if match:
        symbol = match.group(2) or ""
        return f"{symbol} {match.group(3)}".strip()
    return "Not found"

# ----------------------------
# Extract Dates (Multiple formats)
# ----------------------------
def extract_date(text):
    date_patterns = [
        r"\d{4}[-/]\d{2}[-/]\d{2}",
        r"\d{2}[-/]\d{2}[-/]\d{4}",
        r"\d{2}\s+[A-Za-z]+\s+\d{4}",
        r"[A-Za-z]+\s+\d{2},?\s+\d{4}"
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return "Not found"

# ----------------------------
# Extract Invoice Number
# ----------------------------
def extract_invoice_number(text):
    patterns = [
        r"invoice\s*(no|number|#)\s*[:\-]?\s*([\w\-\/]+)",
        r"\bINV[-\w]+\b",
        r"\b\d{4,}[-/]\d+\b"
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(2) if len(m.groups()) > 1 else m.group()
    return "Not found"

# ----------------------------
# Extract Phone
# ----------------------------
def extract_phone(text):
    phone_match = re.search(r"\+?\d[\d\s\-]{8,15}\d", text)
    return phone_match.group() if phone_match else "Not found"

# ----------------------------
# Extract Vendor
# ----------------------------
def extract_vendor(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:10]:
        if not any(k in line.lower() for k in 
                   ["invoice", "date", "gst", "total", "bill", "amount"]):
            if len(line) > 4:
                return line
    return "Not found"

# ==================================================
# MAIN PROCESS
# ==================================================

if uploaded:
    try:
        # ----------------------------
        # Handle PDF (All Pages)
        # ----------------------------
        if uploaded.type == "application/pdf":
            images = pdf2image.convert_from_bytes(uploaded.read())
            raw_text = ""
            for img in images:
                raw_text += pytesseract.image_to_string(
                    img, config="--oem 3 --psm 6"
                ) + "\n"
            image = images[0]
        else:
            image = Image.open(uploaded).convert("RGB")
            raw_text = pytesseract.image_to_string(
                image, config="--oem 3 --psm 6"
            )

        st.image(image, width=450)

        raw_text = clean_text(raw_text)

        if not raw_text.strip():
            st.error("No readable text found.")
            st.stop()

        # ----------------------------
        # Extract Data
        # ----------------------------
        vendor = extract_vendor(raw_text)
        invoice_no = extract_invoice_number(raw_text)
        invoice_date = extract_date(raw_text)
        subtotal = extract_amount("subtotal|taxable amount", raw_text)
        tax = extract_amount("tax|gst|vat|cgst|sgst|igst", raw_text)
        total = extract_amount("grand total|total amount|amount due|balance|total", raw_text)
        phone = extract_phone(raw_text)

        # ----------------------------
        # Display
        # ----------------------------
        st.success("✅ Invoice processed successfully")

        with st.expander("📄 Extracted Details"):
            st.write(f"**Vendor / Company:** {vendor}")
            st.write(f"**Invoice Number:** {invoice_no}")
            st.write(f"**Invoice Date:** {invoice_date}")
            st.write(f"**Subtotal:** {subtotal}")
            st.write(f"**Tax:** {tax}")
            st.write(f"**Total Amount:** {total}")
            st.write(f"**Phone:** {phone}")

            st.markdown("---")
            st.markdown("### 🔍 Raw OCR Text")
            st.text(raw_text)

    except Exception as e:
        st.error("OCR processing failed safely")
        st.code(str(e))
