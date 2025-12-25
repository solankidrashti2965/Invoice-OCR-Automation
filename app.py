import streamlit as st
from PIL import Image
import pytesseract
import re

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")

st.title("📄 Invoice OCR Automation")
st.write("Upload a valid invoice image to extract details")

uploaded_file = st.file_uploader(
    "Upload Invoice Image",
    type=["jpg", "png", "jpeg"]
)

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Invoice", use_column_width=True)

    try:
        # OCR
        text = pytesseract.image_to_string(image, config="--oem 3 --psm 6")
        text_lower = text.lower()

        # ❌ Reject random images
        if "invoice" not in text_lower:
            st.error("❌ This image does not appear to be a valid invoice.")
            st.stop()

        # ✅ Extract Invoice Number
        invoice_no = "Not found"
        match_inv = re.search(r'invoice\s*#?\s*(\d+)', text, re.I)
        if match_inv:
            invoice_no = match_inv.group(1)

        # ✅ Extract Total Amount
        total_amount = "Not found"
        match_total = re.search(r'total\s*\$?\s*([\d,.]+)', text, re.I)
        if match_total:
            total_amount = "$" + match_total.group(1)

        st.success("✅ Invoice processed successfully")
        st.write(f"**Invoice Number:** {invoice_no}")
        st.write(f"**Total Amount:** {total_amount}")

    except Exception as e:
        st.error("⚠️ OCR processing failed.")
        st.code(str(e))
