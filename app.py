import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")

st.title("📄 Invoice OCR Automation")
st.write("Upload a valid invoice image to extract details")

uploaded_file = st.file_uploader(
    "Upload Invoice Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(uploaded_file.getvalue())
        temp_path = tmp.name

    try:
        text = pytesseract.image_to_string(image, config="--oem 3 --psm 6")
        text_lower = text.lower()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # ---------------- INVOICE VALIDATION ----------------
        invoice_keywords = [
            "invoice", "total", "amount", "bill",
            "invoice #", "subtotal", "tax", "due date"
        ]

        keyword_hits = sum(1 for k in invoice_keywords if k in text_lower)

        if keyword_hits < 2:
            st.error("❌ This image does not appear to be a valid invoice.")
            st.stop()

        # ---------------- EXTRACTION ----------------
        invoice_no = "Not found"
        total_amount = "Not found"
        vendor = "Not found"

        for line in lines:
            m = re.search(r'invoice\s*#\s*(\d+)', line, re.I)
            if m:
                invoice_no = m.group(1)
                break

        for line in lines:
            if re.match(r'^total\b', line, re.I):
                m = re.search(r'\$([\d,.]+)', line)
                if m:
                    total_amount = "$" + m.group(1)
                    break

        for line in lines[:6]:
            if any(c.isalpha() for c in line):
                vendor = re.sub(r'\d{3}-\d{3}-\d{4}', '', line).strip()
                break

        # ---------------- OUTPUT ----------------
        st.success("✅ Valid Invoice Detected")

        st.write("### 📌 Extracted Details")
        st.write(f"**Invoice Number:** {invoice_no}")
        st.write(f"**Vendor Name:** {vendor}")
        st.write(f"**Total Amount:** {total_amount}")

        with st.expander("🔍 OCR Debug Text"):
            st.text(text)

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
