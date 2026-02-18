import streamlit as st
from PIL import Image
import pytesseract
import re
from pdf2image import convert_from_bytes

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")

st.title("📄 Invoice OCR Automation")
st.write("Upload an invoice (Image or PDF)")

uploaded_file = st.file_uploader(
    "Upload Invoice",
    type=["jpg", "jpeg", "png", "pdf"]
)

# -------------------------------
# SMART FIELD EXTRACTION FUNCTION
# -------------------------------

def extract_fields(text):

    data = {
        "Vendor Name": "Not found",
        "Invoice Number": "Not found",
        "Invoice Date": "Not found",
        "Due Date": "Not found",
        "Subtotal": "Not found",
        "Tax": "Not found",
        "Total Amount": "Not found",
        "Phone / Account": "Not found"
    }

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # -------- Vendor (Top lines logic) --------
    for ln in lines[:10]:
        if (
            len(ln) > 5
            and not re.search(r'invoice|date|total|tax|gst|amount|bill', ln, re.I)
            and not re.search(r'\d{4,}', ln)
        ):
            cleaned = re.sub(r'[©®™]', '', ln)
            data["Vendor Name"] = cleaned.strip()
            break

    # -------- Invoice Number --------
    inv_match = re.search(
        r'(Invoice\s*(No|Number|#)?\s*[:\-]?\s*)([A-Z0-9\-]+)',
        text,
        re.I
    )
    if inv_match:
        data["Invoice Number"] = inv_match.group(3)

    # -------- Date (Flexible formats) --------
    date_match = re.search(
        r'(\d{4}-\d{2}-\d{2}|\d{2}[\/\-]\d{2}[\/\-]\d{2,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        text
    )
    if date_match:
        data["Invoice Date"] = date_match.group(1)

    # -------- Due Date --------
    due_match = re.search(
        r'(Due\s*Date|Payment\s*Due)\s*[:\-]?\s*([0-9A-Za-z\/\-, ]+)',
        text,
        re.I
    )
    if due_match:
        data["Due Date"] = due_match.group(2).strip()

    # -------- Subtotal --------
    sub_match = re.search(
        r'Sub\s*Total\s*[:\-]?\s*(₹|\$)?\s*([\d,]+\.\d{2})',
        text,
        re.I
    )
    if sub_match:
        data["Subtotal"] = (sub_match.group(1) or "") + sub_match.group(2)

    # -------- Tax --------
    tax_match = re.search(
        r'(Tax|GST|IGST|CGST|SGST)\s*[:\-]?\s*(₹|\$)?\s*([\d,]+\.\d{2})',
        text,
        re.I
    )
    if tax_match:
        data["Tax"] = (tax_match.group(2) or "") + tax_match.group(3)

    # -------- Total Amount --------
    total_match = re.search(
        r'(Total|Grand\s*Total|Amount\s*Due)\s*[:\-]?\s*(₹|\$)?\s*([\d,]+\.\d{2})',
        text,
        re.I
    )
    if total_match:
        data["Total Amount"] = (total_match.group(2) or "") + total_match.group(3)
    else:
        # fallback → pick largest decimal number
        numbers = re.findall(r'[\d,]+\.\d{2}', text)
        if numbers:
            numeric = sorted(
                [float(n.replace(",", "")) for n in numbers],
                reverse=True
            )
            data["Total Amount"] = str(numeric[0])

    # -------- Phone --------
    phone_match = re.search(r'\b\d{10,}\b', text)
    if phone_match:
        data["Phone / Account"] = phone_match.group()

    return data


# -------------------------------
# MAIN LOGIC
# -------------------------------

if uploaded_file:

    try:
        text = ""

        # -------- Handle PDF --------
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(uploaded_file.read())
            for img in images:
                text += pytesseract.image_to_string(img)

        # -------- Handle Image --------
        else:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, width=450)
            text = pytesseract.image_to_string(image)

        if not text.strip():
            st.error("❌ No readable text found.")
            st.stop()

        extracted = extract_fields(text)

        st.success("✅ Invoice processed successfully")

        with st.expander("📄 Extracted Details", expanded=True):
            for k, v in extracted.items():
                st.write(f"**{k}:** {v}")

            st.markdown("---")
            st.markdown("🔍 Raw OCR Text")
            st.text(text)

    except Exception as e:
        st.error("❌ OCR processing failed safely")
        st.code(str(e))
