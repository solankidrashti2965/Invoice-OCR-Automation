import streamlit as st
from PIL import Image
import pytesseract
import re
import pdfplumber
import io

st.set_page_config(page_title="Universal Invoice OCR", layout="centered")
st.title(" Invoice OCR Automation")
st.write("Upload any Invoice (Image or PDF)")

uploaded = st.file_uploader(
    "Upload Invoice",
    type=["jpg", "jpeg", "png", "pdf"]
)

# ---------------- CLEAN FUNCTION ----------------
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

# ---------------- UNIVERSAL EXTRACTION LOGIC ----------------
def extract_invoice_details(text):

    data = {
        "Vendor / Company": "Not found",
        "Invoice Number": "Not found",
        "Invoice Date": "Not found",
        "Due Date": "Not found",
        "Subtotal": "Not found",
        "Tax": "Not found",
        "Total Amount": "Not found",
        "Phone / Account": "Not found"
    }

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ---------- Vendor Detection (first valid line) ----------
    for ln in lines[:10]:
        if not re.search(r'invoice|bill|date|total|amount|tax|qty|description', ln, re.I):
            if len(ln) > 4:
                data["Vendor / Company"] = ln
                break

    # ---------- Invoice Number ----------
    inv_patterns = [
        r'invoice\s*(no|number|#)\s*[:\-]?\s*([A-Z0-9\-\/]+)',
        r'\bINV[- ]?\d+\b',
        r'\b[A-Z]{2,5}-\d{2,6}\b'
    ]

    for p in inv_patterns:
        m = re.search(p, text, re.I)
        if m:
            data["Invoice Number"] = m.group(m.lastindex)
            break

    # ---------- Dates ----------
    date_patterns = [
        r'invoice\s*date\s*[:\-]?\s*([0-9A-Za-z\/,\- ]+)',
        r'due\s*date\s*[:\-]?\s*([0-9A-Za-z\/,\- ]+)',
        r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',
        r'\b\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\b'
    ]

    found_dates = re.findall(
        r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',
        text
    )

    if found_dates:
        data["Invoice Date"] = found_dates[0]
        if len(found_dates) > 1:
            data["Due Date"] = found_dates[1]

    # ---------- Phone / Account ----------
    phone = re.search(r'\b\d{3}[- ]?\d{3}[- ]?\d{4}\b', text)
    if phone:
        data["Phone / Account"] = phone.group()

    # ---------- Subtotal ----------
    sub = re.search(r'subtotal\s*[:\-]?\s*(₹|\$)?\s*([\d,]+(?:\.\d{2})?)', text, re.I)
    if sub:
        data["Subtotal"] = (sub.group(1) or "") + sub.group(2)

    # ---------- Tax ----------
    tax = re.search(r'tax\s*[:\-]?\s*(₹|\$)?\s*([\d,]+(?:\.\d{2})?)', text, re.I)
    if tax:
        data["Tax"] = (tax.group(1) or "") + tax.group(2)

    # ---------- Total (Take Last Highest Amount) ----------
    totals = re.findall(
        r'(total|grand\s*total|amount\s*due)[^\d]{0,15}(₹|\$)?\s*([\d,]+(?:\.\d{2})?)',
        text,
        re.I
    )

    if totals:
        currency = totals[-1][1] or ""
        amount = totals[-1][2]
        data["Total Amount"] = currency + amount
    else:
        # fallback: highest amount in document
        amounts = re.findall(r'(₹|\$)?\s*([\d,]+\.\d{2})', text)
        if amounts:
            highest = max(amounts, key=lambda x: float(x[1].replace(",", "")))
            data["Total Amount"] = (highest[0] or "") + highest[1]

    return data

# ---------------- MAIN LOGIC ----------------
if uploaded:

    st.success("File Uploaded Successfully ✅")

    raw_text = ""

    try:
        # --------- PDF ---------
        if uploaded.type == "application/pdf":
            with pdfplumber.open(io.BytesIO(uploaded.read())) as pdf:
                for page in pdf.pages:
                    raw_text += page.extract_text() + "\n"

        # --------- IMAGE ---------
        else:
            image = Image.open(uploaded).convert("RGB")
            st.image(image, width=450)
            raw_text = pytesseract.image_to_string(
                image,
                config="--oem 3 --psm 6"
            )

        if not raw_text or len(raw_text.strip()) < 40:
            st.error("❌ This does not look like a valid invoice.")
            st.stop()

        extracted = extract_invoice_details(raw_text)

        st.success("✅ Invoice Processed Successfully")

        with st.expander("📄 Extracted Details"):
            for key, value in extracted.items():
                st.write(f"**{key}:** {clean_text(value)}")

        with st.expander("🔍 View OCR Text"):
            st.text(raw_text)

    except Exception as e:
        st.error("❌ Processing Failed Safely")
        st.code(str(e))
