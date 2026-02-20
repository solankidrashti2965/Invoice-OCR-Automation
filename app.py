import streamlit as st
from PIL import Image
import pytesseract
import re
import PyPDF2
import io

st.set_page_config(page_title="Invoice OCR Automation", layout="centered")

st.title("📄 Invoice OCR Automation")
st.write("Upload an invoice (Image or PDF)")

uploaded_file = st.file_uploader(
    "Upload Invoice",
    type=["jpg", "jpeg", "png", "pdf"]
)

# ----------------------------------------
# SMART FIELD EXTRACTION FUNCTION
# ----------------------------------------
def extract_fields(text):

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

    # ---------------- Invoice Number ----------------
    inv_match = re.search(
        r'(Invoice|Bill)\s*(No|Number|#)?\s*[:\-]?\s*([A-Z0-9\-\/]+)',
        text,
        re.I
    )
    if inv_match:
        data["Invoice Number"] = inv_match.group(3)

    # ---------------- Dates ----------------
    dates = re.findall(r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b', text)

    if len(dates) >= 1:
        data["Invoice Date"] = dates[0]

    if len(dates) >= 2:
        data["Due Date"] = dates[1]

    # ---------------- Tax ----------------
    tax_match = re.search(
        r'(GST|Tax|IGST|CGST|SGST)[^\d]*(\d+\.\d{2})',
        text,
        re.I
    )
    if tax_match:
        data["Tax"] = tax_match.group(2)

    # ---------------- SAFE Amount Detection ----------------
    amounts = re.findall(r'\b\d+\.\d{2}\b', text)

    clean_amounts = []

    for amt in amounts:
        try:
            value = float(amt)

            # Ignore small values (avoid dates like 04.12)
            if value > 10:
                clean_amounts.append(value)

        except:
            continue

    if clean_amounts:
        clean_amounts.sort()

        # Largest = Total
        data["Total Amount"] = str(clean_amounts[-1])

        # Second Largest = Subtotal (if exists)
        if len(clean_amounts) >= 2:
            data["Subtotal"] = str(clean_amounts[-2])

    # ---------------- Phone ----------------
    phone_match = re.search(r'\b\d{10}\b', text)
    if phone_match:
        data["Phone / Account"] = phone_match.group()

    # ---------------- Vendor Name ----------------
    words = text.split()
    if len(words) >= 3:
        data["Vendor Name"] = " ".join(words[:3])

    return data


# ----------------------------------------
# MAIN LOGIC
# ----------------------------------------
if uploaded_file:

    try:
        text = ""

        # -------- Handle PDF --------
        if uploaded_file.type == "application/pdf":

            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))

            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

        # -------- Handle Image --------
        else:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, width=450)
            text = pytesseract.image_to_string(image, config="--psm 6")

        if not text.strip():
            st.error("❌ No readable text found.")
            st.stop()

        extracted = extract_fields(text)

        st.success("✅ Invoice processed successfully")

        with st.expander("📄 Extracted Details", expanded=True):
            for k, v in extracted.items():
                st.write(f"**{k}:** {v}")

            st.markdown("---")
            st.markdown("🔍 Raw Extracted Text")
            st.text(text)

    except Exception as e:
        st.error("❌ Processing failed")
        st.code(str(e))
