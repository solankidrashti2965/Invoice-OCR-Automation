import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")
st.title("📄 Invoice OCR Automation")
st.write("Upload an invoice image to extract details")

uploaded_file = st.file_uploader(
    "Upload Invoice Image", type=["png", "jpg", "jpeg"]
)

def extract(patterns, text):
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Not found"

if uploaded_file:
    st.image(uploaded_file, width=400)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(uploaded_file.read())
        img_path = tmp.name

    try:
        img = Image.open(img_path).convert("RGB")
        text = pytesseract.image_to_string(img)

        if not text.strip():
            st.error("⚠️ No readable text detected")
        else:
            st.success("✅ Invoice processed successfully")

            invoice_no = extract(
                [r"Invoice\s*#?\s*([A-Z0-9\-]+)"], text
            )

            invoice_date = extract(
                [r"Invoice\s*Date\s*[:\-]?\s*([0-9\/\-\.]+)",
                 r"Date\s*[:\-]?\s*([0-9\/\-\.]+)"],
                text
            )

            due_date = extract(
                [r"Due\s*Date\s*[:\-]?\s*([0-9\/\-\.]+)"],
                text
            )

            total = extract(
                [
                    r"Total\s*\$?\s*([0-9,]+\.\d{2})",
                    r"Grand\s*Total\s*\$?\s*([0-9,]+\.\d{2})",
                    r"Amount\s*Due\s*\$?\s*([0-9,]+\.\d{2})"
                ],
                text
            )

            phone = extract(
                [r"(\d{3}[-\s]\d{3}[-\s]\d{4})"], text
            )

            vendor = extract(
                [r"^(.*?)(?:Invoice|Bill|GST|Tax)"],
                text.split("\n")[0]
            )

            st.subheader("📌 Extracted Details")
            st.write(f"**Vendor Name:** {vendor}")
            st.write(f"**Invoice Number:** {invoice_no}")
            st.write(f"**Invoice Date:** {invoice_date}")
            st.write(f"**Due Date:** {due_date}")
            st.write(f"**Phone / Account No:** {phone}")
            st.write(f"**Total Amount:** {total}")

            with st.expander("🔍 Full OCR Text"):
                st.text(text)

    except Exception as e:
        st.error("❌ OCR processing failed safely")
        st.code(str(e))

    finally:
        os.remove(img_path)
