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
# SMART LINE-BASED EXTRACTION
# ----------------------------------------
def extract_fields(text):

    lines = [line.strip() for line in text.splitlines() if line.strip()]

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
    for line in lines[:10]:
        if (
            len(line) > 5
            and not re.search(r'invoice|tax|bill|original|date|gst|total', line, re.I)
            and not re.search(r'\d{4,}', line)
        ):
            data["Vendor Name"] = line
            break

    # ---------------- Invoice Number ----------------
    for line in lines:
        if re.search(r'invoice', line, re.I):
            match = re.search(r'([A-Z0-9\-\/]{5,})', line)
            if match and match.group(1).lower() not in ["original"]:
                data["Invoice Number"] = match.group(1)
                break

    # ---------------- Date ----------------
    for line in lines:
        date_match = re.search(r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}', line)
        if date_match:
            data["Invoice Date"] = date_match.group()
            break

        date_match2 = re.search(r'\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}', line)
        if date_match2:
            data["Invoice Date"] = date_match2.group()
            break

    # ---------------- Tax ----------------
    for line in lines:
        if re.search(r'gst|tax', line, re.I):
            match = re.search(r'\d+\.\d{2}', line)
            if match:
                data["Tax"] = match.group()
                break

    # ---------------- Total (VERY IMPORTANT) ----------------
    for line in lines:
        if re.search(r'grand total|total amount|amount payable|total$', line, re.I):
            match = re.search(r'\d+\.\d{2}', line)
            if match:
                data["Total Amount"] = match.group()
                break

    # Fallback → pick largest value
    if data["Total Amount"] == "Not found":
        amounts = re.findall(r'\d+\.\d{2}', text)
        if amounts:
            values = [float(a) for a in amounts]
            data["Total Amount"] = str(max(values))

    # ---------------- Phone ----------------
    for line in lines:
        phone_match = re.search(r'\b\d{10}\b', line)
        if phone_match:
            data["Phone / Account"] = phone_match.group()
            break

    return data


# ----------------------------------------
# MAIN LOGIC
# ----------------------------------------
if uploaded_file:

    try:
        text = ""

        # PDF
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

        # IMAGE
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
