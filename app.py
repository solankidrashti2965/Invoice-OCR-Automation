import streamlit as st
from PIL import Image
import easyocr
import re
import tempfile
import os

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")

st.title("📄 Invoice OCR Automation")
st.write("Upload a **valid invoice image** to extract details")

uploaded = st.file_uploader("Upload Invoice", type=["jpg", "png", "jpeg"])

if uploaded:
    st.image(uploaded, width=450)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(uploaded.getvalue())
        img_path = f.name

    try:
        reader = easyocr.Reader(['en'], gpu=False)
        result = reader.readtext(img_path, detail=0)
        text = " ".join(result)

        # ---------- VALIDATION ----------
        if not re.search(r'invoice', text, re.I):
            st.error("❌ This does not look like an invoice.")
            st.stop()

        # ---------- EXTRACTION ----------
        invoice_no = re.search(r'Invoice\s*#?\s*(\d+)', text, re.I)
        total_amt = re.search(r'Total\s*\$?\s*([\d,.]+)', text, re.I)

        st.success("✅ Invoice processed successfully")

        st.write("### Extracted Details")
        st.write("**Invoice Number:**", invoice_no.group(1) if invoice_no else "Not found")
        st.write("**Total Amount:**", "$" + total_amt.group(1) if total_amt else "Not found")

    except Exception as e:
        st.error(f"OCR Failed: {e}")

    finally:
        os.remove(img_path)
