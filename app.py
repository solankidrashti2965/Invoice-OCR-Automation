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
# SMART EXTRACTION FUNCTION
# ----------------------------------------
def extract_fields(text):

    raw_lines = text.splitlines()
    clean_text = re.sub(r'\s+', ' ', text)

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
    for line in raw_lines[:15]:
        line = line.strip()

        if (
            len(line) > 5
            and not re.search(r'invoice|tax|bill|original|date|gst|total', line, re.I)
            and not re.search(r'\d{4,}', line)
        ):
            data["Vendor Name"] = line
            break

    # ---------------- Invoice Number ----------------
    inv_match = re.search(
        r'Invoice\s*(No|Number|#)?\s*[:\-]?\s*([A-Z0-9\-\/]{5,})',
        clean_text,
        re.I
    )

    if inv_match:
        data["Invoice Number"] = inv_match.group(2)

    # ---------------- Date Detection ----------------
    # Format: 04/12/2023 or 04-12-2023 or 04.12.2023
    date_match1 = re.search(
        r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b',
        clean_text
    )

    # Format: 04 Dec 2023
    date_match2 = re.search(
        r'\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b',
        clean_text
    )

    if date_match1:
        data["Invoice Date"] = date_match1.group()
    elif date_match2:
        data["Invoice Date"] = date_match2.group()

    # ---------------- Total (Keyword Based) ----------------
    total_match = re.search(
        r'(Grand\s*Total|Total\s*Amount|Amount\s*Payable|Total)[^\d]*(\d+\.\d{2})',
        clean_text,
        re.I
    )

    if total_match:
        data["Total Amount"] = total_match.group(2)

    # ---------------- Tax ----------------
    tax_match = re.search(
        r'(GST|Tax)[^\d]*(\d+\.\d{2})',
        clean_text,
        re.I
    )

    if tax_match:
        data["Tax"] = tax_match.group(2)

    # ---------------- Phone ----------------
    phone_match = re.search(r'\b\d{10}\b', clean_text)
    if phone_match:
        data["Phone / Account"] = phone_match.group()

    return data


# ----------------------------------------
# MAIN LOGIC
# ----------------------------------------
if uploaded_file:

    try:
        text = ""

        # -------- PDF --------
        if uploaded_file.type == "application/pdf":

            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))

            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

        # -------- IMAGE --------
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
