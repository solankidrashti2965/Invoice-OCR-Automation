import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os

# Streamlit Cloud Tesseract path
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")
st.title("📄 Invoice OCR Automation")
st.write("Upload an invoice image to extract details")

uploaded_file = st.file_uploader(
    "Upload Invoice Image", type=["png", "jpg", "jpeg"]
)

def extract_field(patterns, text):
    for p in patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Not found"

if uploaded_file:
    st.image(uploaded_file, width=400)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(uploaded_file.read())
        image_path = tmp.name

    try:
        image = Image.open(image_path).convert("RGB")
        text = pytesseract.image_to_string(image, config="--oem 3 --psm 6")

        if not text.strip():
            st.error("⚠️ No readable text found in image")
        else:
            st.success("✅ OCR completed successfully")

            # ---------- EXTRACTION LOGIC ----------
            invoice_number = extract_field(
                [
                    r"Invoice\s*#?\s*([A-Z0-9\-]+)",
                    r"Invoice\s*No\.?\s*([A-Z0-9\-]+)"
                ],
                text
            )

            invoice_date = extract_field(
                [
                    r"Invoice\s*Date\s*[:\-]?\s*([0-9\/\-\.]+)",
                    r"Date\s*[:\-]?\s*([0-9\/\-\.]+)"
                ],
                text
            )

            due_date = extract_field(
                [
                    r"Due\s*Date\s*[:\-]?\s*([0-9\/\-\.]+)"
                ],
                text
            )

            vendor_name = extract_field(
                [
                    r"^(.*?)(?:Invoice|Bill To)",
                ],
                text.split("\n")[0]
            )

            phone_number = extract_field(
                [
                    r"(\+?\d{1,3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4})",
                    r"(\d{3}[-\s]\d{3}[-\s]\d{4})"
                ],
                text
            )

            total_amount = extract_field(
                [
                    r"Total\s*[:\-]?\s*\$?\s*([0-9,]+\.\d{2})",
                    r"Grand\s*Total\s*[:\-]?\s*\$?\s*([0-9,]+\.\d{2})",
                    r"Amount\s*Due\s*[:\-]?\s*\$?\s*([0-9,]+\.\d{2})"
                ],
                text
            )

            tax_amount = extract_field(
                [
                    r"Tax\s*[:\-]?\s*\$?\s*([0-9,]+\.\d{2})",
                    r"CGST.*?([0-9,]+\.\d{2})",
                    r"SGST.*?([0-9,]+\.\d{2})"
                ],
                text
            )

            # ---------- OUTPUT ----------
            st.subheader("📌 Extracted Invoice Details")

            st.write(f"**Vendor Name:** {vendor_name}")
            st.write(f"**Invoice Number:** {invoice_number}")
            st.write(f"**Invoice Date:** {invoice_date}")
            st.write(f"**Due Date:** {due_date}")
            st.write(f"**Phone / Account No:** {phone_number}")
            st.write(f"**Tax Amount:** {tax_amount}")
            st.write(f"**Total Amount:** {total_amount}")

            with st.expander("🔍 View Full OCR Text"):
                st.text(text)

    except Exception as e:
        st.error("❌ OCR processing failed safely")
        st.code(str(e))

    finally:
        if os.path.exists(image_path):
            os.remove(image_path)
