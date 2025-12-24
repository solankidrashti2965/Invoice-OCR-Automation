import streamlit as st
from PIL import Image
import json
import re
from pathlib import Path

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")
st.title("📄 Invoice OCR Automation")
st.write("Upload an invoice image to extract key details")

uploaded_file = st.file_uploader(
    "Upload Invoice Image",
    type=["jpg", "png", "jpeg"]
)

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Invoice", use_column_width=True)

    # DEMO OCR TEXT (simulating OCR output)
    demo_text = """
    Craigs Landscaping
    Invoice # 12345
    Invoice date 08/01/2024
    Phone 123-456-7890
    Total $634.73
    """

    invoice_no = ""
    date_value = ""
    vendor = ""
    total_amount = ""

    for ln in demo_text.split("\n"):
        if "Invoice #" in ln:
            invoice_no = re.search(r'\d+', ln).group()
        if "Invoice date" in ln:
            date_value = re.search(r'\d{2}/\d{2}/\d{4}', ln).group()
        if "Craigs" in ln:
            vendor = ln.strip()
        if "Total" in ln:
            total_amount = re.search(r'\$[\d.]+', ln).group()

    output = {
        "invoice_number": invoice_no,
        "date": date_value,
        "vendor": vendor,
        "total_amount": total_amount
    }

    st.subheader("✅ Extracted Invoice Data")
    st.json(output)
    