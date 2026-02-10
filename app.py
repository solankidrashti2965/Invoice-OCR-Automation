import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os


st.set_page_config(page_title="Invoice OCR Automation", layout="centered")
st.title("📄 Invoice OCR Automation")
st.write("Upload a **valid invoice image** to extract details")


uploaded = st.file_uploader(
    "Upload Invoice Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded:
    st.image(uploaded, width=450)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(uploaded.getvalue())
        img_path = f.name

    try:
        image = Image.open(img_path).convert("RGB")

        # OCR
        raw_text = pytesseract.image_to_string(
            image,
            config="--oem 3 --psm 6"
        )

        if not raw_text.strip():
            st.error("❌ No readable text found. Please upload a clear invoice.")
            st.stop()

        

        # Vendor / Company (top lines)
        vendor = "Not found"
        for line in raw_text.splitlines()[:6]:
            if len(line.strip()) > 3 and not any(
                k in line.lower() for k in ["invoice", "date", "bill", "total"]
            ):
                vendor = line.strip()
                break

        # Invoice Number
        invoice_no = "Not found"
        inv_patterns = [
            r"invoice\s*(no|number|#)\s*[:\-]?\s*(\w+)",
            r"inv\s*#\s*(\w+)"
        ]
        for p in inv_patterns:
            m = re.search(p, raw_text, re.I)
            if m:
                invoice_no = m.group(2)
                break

        # Invoice Date
        invoice_date = "Not found"
        m = re.search(
            r"(invoice\s*date|dated)\s*[:\-]?\s*([0-9A-Za-z ,/-]+)",
            raw_text,
            re.I
        )
        if m:
            invoice_date = m.group(2).strip()

        # Due Date
        due_date = "Not found"
        m = re.search(
            r"(due\s*date|payment\s*due)\s*[:\-]?\s*([0-9A-Za-z ,/-]+)",
            raw_text,
            re.I
        )
        if m:
            due_date = m.group(2).strip()

        # Total Amount 
        total_amount = "Not found"
        totals = re.findall(
            r"(total|grand\s*total|amount\s*due)\s*[:\-]?\s*(₹|\$)?\s*([\d,]+\.\d{2})",
            raw_text,
            re.I
        )
        if totals:
            total_amount = f"{totals[-1][1] or ''}{totals[-1][2]}"

        
        st.success("✅ Invoice processed successfully")

    
        with st.expander("📄 Extracted Details"):
            st.write(f"**Vendor / Company:** {vendor}")
            st.write(f"**Invoice Number:** {invoice_no}")
            st.write(f"**Invoice Date:** {invoice_date}")
            st.write(f"**Due Date:** {due_date}")
            st.write(f"**Total Amount:** {total_amount}")

            st.markdown("---")
            st.markdown("**🔍 Raw OCR Text**")
            st.text(raw_text)

    except Exception as e:
        st.error("❌ OCR processing failed safely")
        st.code(str(e))

    finally:
        if os.path.exists(img_path):
            os.remove(img_path)
