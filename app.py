import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os
from datetime import datetime

st.set_page_config(page_title="Invoice OCR", layout="centered")
st.title("📄 Universal Invoice OCR")
st.caption("Works for invoices of ANY layout")

uploaded = st.file_uploader("Upload invoice image", type=["jpg", "png", "jpeg"])

def clean(text):
    return text.replace("\n", " ").strip()

def find_first(patterns, text):
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1)
    return "Not Found"

def extract_invoice(text):
    result = {}

    # Invoice Number
    result["Invoice Number"] = find_first([
        r'(?:invoice|bill|inv)\s*(?:no|number|#)\s*[:\-]?\s*([A-Z0-9\-]+)'
    ], text)

    # Dates
    dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
    result["Invoice Date"] = dates[0] if len(dates) > 0 else "Not Found"
    result["Due Date"] = dates[1] if len(dates) > 1 else "Not Found"

    # Vendor (first clean line)
    lines = [l for l in text.splitlines() if len(l.strip()) > 4]
    vendor = "Not Found"
    for l in lines[:5]:
        if not re.search(r'@|www|gst|phone|\d{3}', l, re.I):
            vendor = l.strip()
            break
    result["Vendor"] = vendor

    # Amounts
    amounts = re.findall(r'(₹|\$|INR|USD)?\s?([\d,]+\.\d{2})', text)
    if amounts:
        amounts_clean = [float(a[1].replace(",", "")) for a in amounts]
        result["Total Amount"] = max(amounts_clean)
    else:
        result["Total Amount"] = "Not Found"

    return result

if uploaded:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(uploaded.read())
        path = f.name

    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)

        data = extract_invoice(text)

        found_fields = sum(1 for v in data.values() if v != "Not Found")

        if found_fields < 2:
            st.error("❌ This does not appear to be a valid invoice.")
        else:
            st.success("✅ Invoice extracted successfully")
            st.subheader("📌 Extracted Details")
            for k, v in data.items():
                st.write(f"**{k}:** {v}")

    except Exception as e:
        st.error(str(e))
    finally:
        os.remove(path)
