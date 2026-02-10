import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os
from pdf2image import convert_from_path
import cairosvg

st.set_page_config(page_title="Invoice OCR", layout="centered")
st.title("📄 Universal Invoice OCR")
st.caption("Supports Image • PDF • SVG invoices")

uploaded = st.file_uploader(
    "Upload invoice (JPG / PNG / PDF / SVG)",
    type=["jpg", "png", "jpeg", "pdf", "svg"]
)

# ---------- Utility functions ----------

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

    # Vendor
    lines = [l for l in text.splitlines() if len(l.strip()) > 4]
    vendor = "Not Found"
    for l in lines[:6]:
        if not re.search(r'@|www|gst|phone|\d{3}', l, re.I):
            vendor = l.strip()
            break
    result["Vendor"] = vendor

    # Total Amount
    amounts = re.findall(r'(₹|\$|INR|USD|EUR)?\s?([\d,]+\.\d{2})', text)
    if amounts:
        result["Total Amount"] = max(
            float(a[1].replace(",", "")) for a in amounts
        )
    else:
        result["Total Amount"] = "Not Found"

    return result

# ---------- Main logic ----------

if uploaded:
    suffix = uploaded.name.split(".")[-1].lower()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, uploaded.name)

        with open(file_path, "wb") as f:
            f.write(uploaded.read())

        images = []

        try:
            # IMAGE
            if suffix in ["jpg", "jpeg", "png"]:
                images = [
