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

# ---------------------------
# SMART FIELD EXTRACTION
# ---------------------------

def extract_fields(text):

    data = {
        "Invoice Number": "Not found",
        "Vendor Name": "Not found",
        "Invoice Date": "Not found",
        "Due Date": "Not found",
        "Subtotal": "Not found",
        "Tax": "Not found",
        "Total Amount": "Not found",
        "Phone / Account": "Not found"
    }

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ------------------ INVOICE NUMBER ------------------
    inv_patterns = [
        r'invoice\s*(no|number|#)\s*[:\-]?\s*([A-Z0-9\-]+)',
        r'\bINV[\- ]?[0-9A-Z]+\b'
    ]

    for pattern in inv_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            data["Invoice Number"] = m.group(len(m.groups()))
            break

    # ------------------ VENDOR NAME ------------------
    for ln in lines[:8]:
        if (
            len(ln) > 5
            and not re.search(r'invoice|bill|date|total|tax', ln, re.I)
            and not re.search(r'\d{2,}', ln)
        ):
            data["Vendor Name"] = ln
            break

    # ------------------ DATES ------------------
    date_patterns = [
        r'(\d{2}[\/\-]\d{2}[\/\-]\d{2,4})',
        r'(\d{4}[\/\-]\d{2}[\/\-]\d{2})',
        r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})'
    ]

    for pattern in date_patterns:
        m = re.search(r'(invoice\s*date|dated)\s*[:\-]?\s*' + pattern, text, re.I)
        if m:
            data["Invoice Date"] = m.group(len(m.groups()))
            break

    for pattern in date_patterns:
        m = re.search(r'(due\s*date|payment\s*due)\s*[:\-]?\s*' + pattern, text, re.I)
        if m:
            data["Due Date"] = m.group(len(m.groups()))
            break

    # ------------------ SUBTOTAL ------------------
    m = re.search(r'sub\s*total\s*[:\-]?\s*(₹|\$)?\s*([\d,]+\.\d{2})', text, re.I)
    if m:
        data["Subtotal"] = (m.group(1) or "") + m.group(2)

    # ------------------ TAX ------------------
    m = re.search(r'(tax|gst|vat)\s*[:\-]?\s*(₹|\$)?\s*([\d,]+\.\d{2})', text, re.I)
    if m:
        data["Tax"] = (m.group(2) or "") + m.group(3)

    # ------------------ TOTAL (SMART - LAST BIG NUMBER) ------------------
    total_patterns = re.findall(
        r'(grand\s*total|amount\s*due|total)\s*[:\-]?\s*(₹|\$)?\s*([\d,]+\.\d{2})',
        text,
        re.I
    )

    if total_patterns:
        last = total_patterns[-1]
        data["Total Amount"] = (last[1] or "") + last[2]

    # ------------------ PHONE / ACCOUNT ------------------
    m = re.search(r'\b\d{10,}\b', text)
    if m:
        data["Phone / Account"] = m.group()

    return data


# ---------------------------
# PROCESS FILE
# ---------------------------

if uploaded_file:

    text = ""

    try:

        # PDF
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(uploaded_file.read())
            for img in images:
                text += pytesseract.image_to_string(img)

        # IMAGE
        else:
            image = Image.open(uploaded_file)
            st.image(image, width=400)
            text = pytesseract.image_to_string(image)

        if len(text.strip()) < 40:
            st.error("❌ This does not look like a valid invoice.")
        else:
            extracted = extract_fields(text)

            st.success("✅ Invoice processed successfully")

            with st.expander("📑 Extracted Details"):
                for k, v in extracted.items():
                    st.write(f"**{k}:** {v}")

            with st.expander("🔍 View OCR Text"):
                st.text(text)

    except Exception as e:
        st.error("⚠ OCR processing failed safely")
        st.code(str(e))
