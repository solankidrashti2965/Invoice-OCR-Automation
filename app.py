import streamlit as st
from PIL import Image
import pytesseract
import re

st.set_page_config(page_title="Invoice OCR", layout="centered")
st.title("📄 Invoice OCR System")
st.write("Upload a valid invoice image")

uploaded = st.file_uploader("Upload Invoice", type=["jpg", "png", "jpeg"])

if uploaded:
    image = Image.open(uploaded)
    st.image(image, caption="Uploaded Invoice", use_column_width=True)

    text = pytesseract.image_to_string(image, config="--oem 3 --psm 6")

    # Check if image looks like an invoice
    if "invoice" not in text.lower():
        st.error("❌ This does not look like a valid invoice")
    else:
        invoice_no = re.search(r'Invoice\s*#?\s*(\d+)', text, re.I)
        total_amt = re.search(r'Total\s*\$?\s*([\d,.]+)', text, re.I)

        st.success("✅ Invoice detected")

        st.write("### Extracted Details")
        st.write("**Invoice Number:**", invoice_no.group(1) if invoice_no else "Not found")
        st.write("**Total Amount:**", "$" + total_amt.group(1) if total_amt else "Not found")
