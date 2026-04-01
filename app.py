import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os
from pdf2image import convert_from_bytes

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")

st.title("📄 Invoice OCR Automation")
st.write("Upload an invoice (Image or PDF)")

uploaded_file = st.file_uploader(
    "Upload Invoice",
    type=["jpg", "jpeg", "png", "pdf"]
)

def extract_fields(text):
    data = {
        "Invoice Number": "Not found",
        "Vendor Name": "Not found",
        "Invoice Date": "Not found",
        "Due Date": "Not found",
        "Total Amount": "Not found"
    }

    # Invoice Number
    m = re.search(r'(Invoice\s*(No|#)?\s*[:\-]?\s*)([A-Z0-9\-]+)', text, re.I)
    if m:
        data["Invoice Number"] = m.group(3)

    # Vendor (top lines)
    lines = text.splitlines()
    for ln in lines[:6]:
        if len(ln.strip()) > 4 and not re.search(r'invoice|date|bill|total', ln, re.I):
            data["Vendor Name"] = ln.strip()
            break

    # Invoice Date
    m = re.search(r'Invoice\s*Date\s*[:\-]?\s*([0-9\/\-]+)', text, re.I)
    if m:
        data["Invoice Date"] = m.group(1)

    # Due Date
    m = re.search(r'Due\s*Date\s*[:\-]?\s*([0-9\/\-]+)', text, re.I)
    if m:
        data["Due Date"] = m.group(1)

    # Total Amount (last total)
    totals = re.findall(r'Total\s*\$?\s*([0-9,.]+)', text, re.I)
    if totals:
        data["Total Amount"] = totals[-1]

    return data


if uploaded_file:
    st.success("File uploaded successfully ✅")

    text = ""

    try:
        # ---------- HANDLE PDF ----------
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(uploaded_file.read())
            for img in images:
                text += pytesseract.image_to_string(img)

        # ---------- HANDLE IMAGE ----------
        else:
            image = Image.open(uploaded_file)
            st.image(image, width=400)
            text = pytesseract.image_to_string(image)

        if len(text.strip()) < 30:
            st.error("❌ This does not look like an invoice")
        else:
            extracted = extract_fields(text)

            st.subheader("📑 Extracted Details")
            for k, v in extracted.items():
                st.write(f"**{k}:** {v}")

    except Exception as e:
        st.error("Something went wrong while processing the invoice")
