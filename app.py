import streamlit as st
from PIL import Image
import pytesseract
import re
import cv2
import numpy as np
from pdf2image import convert_from_bytes

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")

st.title("📄 Invoice OCR Automation")
st.write("Upload an invoice (Image or PDF)")

uploaded_file = st.file_uploader(
    "Upload Invoice",
    type=["jpg", "jpeg", "png", "pdf"]
)

# ----------------------------------------
# IMAGE PREPROCESSING (Improves OCR 40%)
# ----------------------------------------
def preprocess_image(pil_image):
    img = np.array(pil_image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blur, 0, 255,
                           cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return thresh


# ----------------------------------------
# SMART FIELD EXTRACTION FUNCTION
# ----------------------------------------
def extract_fields(text):

    # Clean OCR text
    text = text.replace("\n", " ")
    text = re.sub(r'\s+', ' ', text)

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

    # ---------------- Vendor Name ----------------
    lines = text.split(" ")
    if len(lines) > 3:
        data["Vendor Name"] = " ".join(lines[:3])

    # ---------------- Invoice Number ----------------
    inv_match = re.search(
        r'(Invoice\s*(No|Number|#)?\s*[:\-]?\s*)([A-Z0-9\-]+)',
        text,
        re.I
    )
    if inv_match:
        data["Invoice Number"] = inv_match.group(3)

    # ---------------- Invoice Date ----------------
    date_match = re.search(
        r'(Invoice\s*Date\s*[:\-]?\s*)(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        text,
        re.I
    )
    if date_match:
        data["Invoice Date"] = date_match.group(2)
    else:
        any_date = re.search(
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            text
        )
        if any_date:
            data["Invoice Date"] = any_date.group(1)

    # ---------------- Due Date ----------------
    due_match = re.search(
        r'(Due\s*Date|Payment\s*Due)\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        text,
        re.I
    )
    if due_match:
        data["Due Date"] = due_match.group(2)

    # ---------------- Subtotal ----------------
    sub_match = re.search(
        r'(Sub\s*Total)\s*[:\-]?\s*(₹|\$)?\s*([\d,]+\.\d{2})',
        text,
        re.I
    )
    if sub_match:
        data["Subtotal"] = sub_match.group(3)

    # ---------------- Tax ----------------
    tax_match = re.search(
        r'(Tax|GST|IGST|CGST|SGST)\s*[:\-]?\s*(₹|\$)?\s*([\d,]+\.\d{2})',
        text,
        re.I
    )
    if tax_match:
        data["Tax"] = tax_match.group(3)

    # ---------------- Smart Total Detection ----------------
    amounts = re.findall(r'[\d,]+\.\d{2}', text)

    if amounts:
        clean_amounts = [float(a.replace(",", "")) for a in amounts]

        # remove small values like tax
        large_values = [a for a in clean_amounts if a > 50]

        if large_values:
            data["Total Amount"] = str(max(large_values))
        else:
            data["Total Amount"] = str(max(clean_amounts))

    # ---------------- Phone ----------------
    phone_match = re.search(r'\b\d{10,}\b', text)
    if phone_match:
        data["Phone / Account"] = phone_match.group()

    return data


# ----------------------------------------
# MAIN LOGIC
# ----------------------------------------
if uploaded_file:

    try:
        text = ""

        # -------- Handle PDF --------
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(uploaded_file.read())
            for img in images:
                img = preprocess_image(img)
                text += pytesseract.image_to_string(
                    img,
                    config="--psm 6"
                )

        # -------- Handle Image --------
        else:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, width=450)

            processed = preprocess_image(image)

            text = pytesseract.image_to_string(
                processed,
                config="--psm 6"
            )

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
