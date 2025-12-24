import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")

st.title("📄 Invoice OCR Automation")
st.write("Upload a valid invoice image")

uploaded = st.file_uploader(
    "Upload Invoice Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded:
    image = Image.open(uploaded)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(uploaded.getvalue())
        temp_path = tmp.name

    try:
        text = pytesseract.image_to_string(image, config="--oem 3 --psm 6")
        text_lower = text.lower()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # ---------- VALIDATE INVOICE ----------
        keywords = [
            "invoice", "total", "amount", "bill",
            "invoice #", "subtotal", "tax", "due date"
        ]

        hits = sum(1 for k in keywords if k in text_lower)

        if hits < 2:
            st.error("❌ This image is NOT a valid invoice.")
            st.stop()

        # ---------- EXTRACTION ----------
        invoice_no = "Not found"
        total = "Not found"
        vendor = "Not found"

        for ln in lines:
            m = re.search(r'invoice\s*#\s*(\d+)', ln, re.I)
            if m:
                invoice_no = m.group(1)
                break

        for ln in lines:
            if ln.lower().startswith("total"):
                m = re.search(r'\$([\d,.]+)', ln)
                if m:
                    total = "$" + m.group(1)
                    break

        for ln in lines[:6]:
            if any(c.isalpha() for c in ln):
                vendor = ln
                break

        # ---------- OUTPUT ----------
        st.success("✅ Valid Invoice Detected")
        st.write("### 📌 Extracted Details")
        st.write(f"**Invoice Number:** {invoice_no}")
        st.write(f"**Vendor:** {vendor}")
        st.write(f"**Total Amount:** {total}")

    except Exception as e:
        st.error(f"OCR Error: {e}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
