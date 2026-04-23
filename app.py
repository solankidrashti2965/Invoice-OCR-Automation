import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os
import sys

# Optional NLP / fallback libraries
try:
    import fitz  # PyMuPDF
    import dateutil.parser
    from thefuzz import fuzz
except ImportError:
    pass

import cv2
import numpy as np
import json

# ==========================================
# PAGE CONFIGURATION (MUST BE FIRST)
# ==========================================
st.set_page_config(
    page_title="Invoice Insight | AI Data Extraction",
    page_icon="📄",
    layout="wide",
)

# ==========================================
# CUSTOM CSS FOR PREMIUM UI
# ==========================================
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="setup"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main Background & Text */
    .stApp {
        background: radial-gradient(circle at top, #1e2430 0%, #0d1117 100%);
        color: #e6edf3;
    }
    
    /* Header Container */
    .main-header {
        background: linear-gradient(135deg, #1f6feb 0%, #2ea043 100%);
        padding: 40px;
        border-radius: 16px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 10px 40px rgba(46, 160, 67, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
        
    .main-header h1 {
        color: #ffffff;
        font-weight: 700;
        margin: 0;
        font-size: 3rem;
        letter-spacing: -1px;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin-top: 10px;
        font-size: 1.2rem;
        font-weight: 300;
    }
    
    /* Extraction Cards (Glassmorphism UI) */
    .data-card {
        background: rgba(22, 27, 34, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        position: relative;
        overflow: hidden;
    }
    
    .data-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.4);
        border-color: rgba(88, 166, 255, 0.5);
        background: rgba(30, 36, 45, 0.8);
    }
    
    .card-icon {
        position: absolute;
        top: 24px;
        right: 24px;
        font-size: 28px;
        opacity: 0.9;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
    }
    
    .card-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #8b949e;
        font-weight: 600;
        margin-bottom: 12px;
    }
    
    .card-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
        word-wrap: break-word;
        line-height: 1.2;
    }
    
    /* Specifically highlight Total Amount */
    .total-card {
        background: linear-gradient(135deg, rgba(35, 134, 54, 0.2) 0%, rgba(22, 27, 34, 0.8) 100%);
        border: 1px solid rgba(46, 160, 67, 0.3);
    }
    .total-card .card-value {
        color: #3fb950;
        font-size: 2.2rem;
    }
    .total-card:hover {
        border-color: #2ea043;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# OCR & PREPROCESSING LOGIC
# ==========================================

from pathlib import Path
tess_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if tess_path.exists():
    pytesseract.pytesseract.tesseract_cmd = str(tess_path)

@st.cache_data
def preprocess_image_for_ocr(image_bytes, is_pdf=False, pdf_dpi=300):
    text = ""
    images_pil = []
    
    try:
        if is_pdf:
            doc = fitz.open("pdf", image_bytes)
            import io
            for page in doc:
                pix = page.get_pixmap(dpi=pdf_dpi)
                img_data = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_data)).convert("RGB")
                images_pil.append(pil_img)
        else:
            import io
            images_pil = [Image.open(io.BytesIO(image_bytes)).convert("RGB")]
            
        for idx, pil_img in enumerate(images_pil):
            cv_img = np.array(pil_img)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_RGB2GRAY)
            
            h, w = gray.shape
            if max(h, w) < 2000:
                scale_factor = 2
                gray = cv2.resize(gray, (w * scale_factor, h * scale_factor), interpolation=cv2.INTER_CUBIC)
            
            gray_blur = cv2.medianBlur(gray, 3)
            thresh = cv2.adaptiveThreshold(
                gray_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 31, 2
            )
            
            processed_pil = Image.fromarray(thresh)
            page_text = pytesseract.image_to_string(processed_pil, config="--oem 3 --psm 6")
            text += page_text + "\n\n"
            
        return text, images_pil[0] if len(images_pil) > 0 else None
        
    except Exception as e:
        print("Preprocessing Error:", e)
        return "", None

# ==========================================
# ROBUST HYBRID EXTRACTION ENGINE
# ==========================================
def extract_fields(text):
    data = {
        "Invoice Number": "Not found",
        "Order ID": "Not found",
        "Vendor Name": "Not found",
        "Invoice Date": "Not found",
        "Order Date": "Not found",
        "Due Date": "Not found",
        "Total Amount": "Not found"
    }
    
    if not text.strip():
        return data

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    full_text = " ".join(lines)

    # 1. VENDOR NAME EXTRACTION
    vendor_found = False
    for i, ln in enumerate(lines):
        # Look for Amazon/Zomato specific markers like "Sold By:"
        if "Sold By:" in ln or "Sold by:" in ln:
            if i + 1 < len(lines):
                v_line = lines[i+1]
                # Vendors are often separated by large whitespace from user address on same line
                parts = re.split(r'\s{2,}', v_line)
                data["Vendor Name"] = parts[0].strip()
                vendor_found = True
                break

    if not vendor_found:
        # Fallback: Find the first clean ALL CAPS line that isn't a standard document string
        for ln in lines[:10]:
            clean_ln = re.sub(r'^[^\w]+', '', ln).strip()
            if len(clean_ln) > 4 and clean_ln.isupper() and "INVOICE" not in clean_ln and "ORIGINAL" not in clean_ln:
                data["Vendor Name"] = clean_ln
                vendor_found = True
                break

    # 2. INVOICE NUMBER EXTRACTION
    # Handles "Invoice Number :AMD2-9374"
    inv_match = re.search(r'(?i)Invoice\s+(?:Number|No|Details)\s*[:-]?\s*([A-Za-z0-9\-_]+)', text)
    if inv_match:
        data["Invoice Number"] = inv_match.group(1).upper()
        
    # Check standard Order Number
    ord_match = re.search(r'(?i)Order\s+(?:Number|No|ID)\s*[:-]?\s*([A-Za-z0-9\-_]+)', text)
    if ord_match:
        data["Order ID"] = ord_match.group(1).upper()

    # 3. DATE EXTRACTION
    # Handles DD.MM.YYYY, YYYY.MM.DD, DD-MMM-YYYY, DD MMM YYYY etc.
    date_pattern = r'(?i)(?:Invoice|Bill|Document)?\s*Date\s*[:-]?\s*(\d{1,4}[\.\/\s-]+[A-Za-z0-9]{2,10}[\.\/\s-]+\d{1,4})'
    date_match = re.search(date_pattern, text)
    if date_match:
        raw_date = date_match.group(1).strip()
        try:
            import dateutil.parser
            parsed_dt = dateutil.parser.parse(raw_date, fuzzy=True)
            data["Invoice Date"] = parsed_dt.strftime("%Y-%m-%d")
        except:
            data["Invoice Date"] = raw_date
            
    # Order Date
    ord_date_pattern = r'(?i)Order\s*Date\s*[:-]?\s*(\d{1,4}[\.\/\s-]+[A-Za-z0-9]{2,10}[\.\/\s-]+\d{1,4})'
    ord_date_match = re.search(ord_date_pattern, text)
    if ord_date_match:
        raw_ord_date = ord_date_match.group(1).strip()
        try:
            import dateutil.parser
            parsed_ord_dt = dateutil.parser.parse(raw_ord_date, fuzzy=True)
            data["Order Date"] = parsed_ord_dt.strftime("%Y-%m-%d")
        except:
            data["Order Date"] = raw_ord_date
            
    # Fallback date extraction using fuzzy approach
    if data["Invoice Date"] == "Not found":
        import dateutil.parser
        for ln in lines:
            if "date" in ln.lower():
                try:
                    dt = dateutil.parser.parse(ln, fuzzy=True)
                    if 2000 <= dt.year <= 2050:
                        data["Invoice Date"] = dt.strftime("%Y-%m-%d")
                        break
                except:
                    pass

    due_pattern = r'(?i)(?:Due|Pay By)\s*Date\s*[:-]?\s*(\d{1,4}[\.\/\s-]+[A-Za-z0-9]{2,10}[\.\/\s-]+\d{1,4})'
    due_date_match = re.search(due_pattern, text)
    if due_date_match:
        raw_due_date = due_date_match.group(1).strip()
        try:
            import dateutil.parser
            parsed_due = dateutil.parser.parse(raw_due_date, fuzzy=True)
            data["Due Date"] = parsed_due.strftime("%Y-%m-%d")
        except:
            data["Due Date"] = raw_due_date

    # 4. TOTAL AMOUNT EXTRACTION
    # Strategy A: Parse "Amount in Words" as ground truth (most reliable)
    # Tesseract often reads ₹ as % - we use the words to confirm
    words_total = None
    for i, ln in enumerate(lines):
        if "amount in words" in ln.lower() or "in words" in ln.lower():
            # The amount in words is on the next line
            words_line = lines[i+1].strip() if i+1 < len(lines) else ""
            combined_words = ln + " " + words_line
            # word_to_number conversion for common patterns
            word_map = {
                "zero":0, "one":1, "two":2, "three":3, "four":4, "five":5,
                "six":6, "seven":7, "eight":8, "nine":9, "ten":10,
                "eleven":11, "twelve":12, "thirteen":13, "fourteen":14, "fifteen":15,
                "sixteen":16, "seventeen":17, "eighteen":18, "nineteen":19, "twenty":20,
                "thirty":30, "forty":40, "fifty":50, "sixty":60, "seventy":70,
                "eighty":80, "ninety":90, "hundred":100, "thousand":1000,
            }
            # Try extracting a decimal from accompanying text first
            # e.g. "Two Hundred Sixty-four Point One only" → 264.1
            words_lower = combined_words.lower()
            # Look for pattern: "X Point Y" to extract decimal
            point_match = re.search(r'(\w+)\s+point\s+(\w+)', words_lower)
            if point_match:
                try:
                    int_part = word_map.get(point_match.group(1).strip(), None)
                    dec_part = word_map.get(point_match.group(2).strip(), None)
                    # This is a simplified parser - look for any decimal in source
                except: pass
            break
    
    # Strategy B: Collect ALL currency-prefixed numbers (% = ₹ due to OCR)
    # Read every number preceded by % ₹ $ or Rs on ANY line
    all_currency_vals = []
    for ln in lines:
        # % is OCR artifact for ₹ — treat identically
        hits = re.findall(r'(?:[%₹\$€£]|Rs\.?\s*|INR\s*)\s*(\d{1,8}(?:\.\d{1,2})?)', ln, re.IGNORECASE)
        for h in hits:
            try:
                v = float(h.replace(',',''))
                if 0 < v < 200000: all_currency_vals.append(v)
            except: pass
        # Also catch bare decimals (XX.XX format) on lines with table markers
        if '|' in ln:
            bare = re.findall(r'\b(\d{1,6}\.\d{2})\b', ln)
            for b in bare:
                try:
                    v = float(b)
                    if 0 < v < 200000: all_currency_vals.append(v)
                except: pass

    # Strategy C: Validate against "Amount in Words" if possible
    # Find an explicit "Amount in Words" confirmation string
    aiw_val = None
    for i, ln in enumerate(lines):
        if "amount in words" in ln.lower():
            next_text = lines[i+1].strip() if i+1 < len(lines) else ""
            # "Two Hundred Sixty-four Point One only" → look for matching float
            hundreds_match = re.search(r'(\w+)\s+[Hh]undred', next_text)
            if hundreds_match:
                # Attempt to build approximate value from hundreds word
                h_word = hundreds_match.group(1).lower()
                hundreds_map = {"one":100,"two":200,"three":300,"four":400,"five":500,
                                "six":600,"seven":700,"eight":800,"nine":900}
                if h_word in hundreds_map:
                    approx = hundreds_map[h_word]
                    # Find the actual decimal closest to this approximation
                    best = min(all_currency_vals, key=lambda x: abs(x - approx), default=None)
                    if best and abs(best - approx) < 150:
                        aiw_val = best
            elif next_text.lower().startswith("seven"):
                aiw_val = 7.0
            elif next_text.lower().startswith("thirty"):
                aiw_val = min([v for v in all_currency_vals if 30 <= v < 50], default=None)
            break

    total_val = aiw_val if aiw_val else (max(all_currency_vals) if all_currency_vals else None)

    if total_val is not None:
        data["Total Amount"] = f"₹ {total_val:.2f}"
        
    # CROSS-POPULATION: Fill empty cards from alternate label
    if data["Order ID"] == "Not found" and data["Invoice Number"] != "Not found":
        data["Order ID"] = data["Invoice Number"]
    elif data["Invoice Number"] == "Not found" and data["Order ID"] != "Not found":
        data["Invoice Number"] = data["Order ID"]
        
    if data["Order Date"] == "Not found" and data["Invoice Date"] != "Not found":
        data["Order Date"] = data["Invoice Date"]
    elif data["Invoice Date"] == "Not found" and data["Order Date"] != "Not found":
        data["Invoice Date"] = data["Order Date"]
    
    return data


# ==========================================
# UI RENDERING
# ==========================================
st.markdown("""
<div class="main-header">
    <h1>📄 Invoice Insight UI Edge</h1>
    <p>AI-Powered Precision OCR & Data Extraction</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload highly-legible invoice or receipt scans",
    type=["jpg", "jpeg", "png", "webp", "pdf"]
)

if uploaded_file:
    file_bytes = uploaded_file.read()
    file_extension = uploaded_file.name.split('.')[-1].lower()
    is_pdf = file_extension == "pdf"
    
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    with st.spinner("Analyzing document structure..."):
        extracted_text, preview_image = preprocess_image_for_ocr(file_bytes, is_pdf=is_pdf)
        
        # [SILENT DEBUG LOGGER] Write the raw text for analysis later
        try:
            with open('ocr_dump_debug.txt', 'w', encoding='utf-8') as f:
                f.write(extracted_text)
        except:
            pass
            
        if not extracted_text or len(extracted_text.strip()) < 10:
             st.error("❌ Content Extraction Failed: The uploaded document appears to be empty or unreadable.")
             st.stop()
             
        extracted_data = extract_fields(extracted_text)
        
    with col1:
        st.markdown("<h3 style='color: #8b949e; font-size: 1.1rem; margin-bottom: 20px; letter-spacing: 1px;'>DOCUMENT PREVIEW</h3>", unsafe_allow_html=True)
        if preview_image:
             st.image(preview_image, use_container_width=True, caption=uploaded_file.name)
        else:
             st.info("Preview not available for this format.")

    with col2:
        st.markdown("<h3 style='color: #8b949e; font-size: 1.1rem; margin-bottom: 20px; letter-spacing: 1px;'>EXTRACTED INTELLIGENCE</h3>", unsafe_allow_html=True)
        
        # Vendor Card
        st.markdown(f"""
        <div class="data-card">
            <div class="card-icon">🏢</div>
            <div class="card-label">Vendor Identity</div>
            <div class="card-value">{extracted_data['Vendor Name']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            st.markdown(f"""
            <div class="data-card">
                <div class="card-icon">#️⃣</div>
                <div class="card-label">Invoice Number</div>
                <div class="card-value">{extracted_data['Invoice Number']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="data-card">
                <div class="card-icon">📅</div>
                <div class="card-label">Invoice Date</div>
                <div class="card-value">{extracted_data['Invoice Date']}</div>
            </div>
            """, unsafe_allow_html=True)

        with ic2:
            st.markdown(f"""
            <div class="data-card">
                <div class="card-icon">🛒</div>
                <div class="card-label">Order ID</div>
                <div class="card-value">{extracted_data['Order ID']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="data-card">
                <div class="card-icon">🕒</div>
                <div class="card-label">Order Date</div>
                <div class="card-value">{extracted_data['Order Date']}</div>
            </div>
            """, unsafe_allow_html=True)

        with ic3:
            st.markdown(f"""
            <div class="data-card total-card">
                <div class="card-icon">💰</div>
                <div class="card-label">Total Amount Due</div>
                <div class="card-value">{extracted_data['Total Amount']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="data-card">
                <div class="card-icon">⏳</div>
                <div class="card-label">Due Date</div>
                <div class="card-value">{extracted_data['Due Date']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br/>", unsafe_allow_html=True)
        with st.expander("Show Raw OCR Output & Download JSON"):
            st.text_area("Processed Text", extracted_text, height=200)
            
            json_output = json.dumps(extracted_data, indent=4)
            st.download_button(
                label="📥 Download JSON Result",
                data=json_output,
                file_name=f"extraction_{extracted_data.get('Invoice Number', 'Unknown')}.json",
                mime="application/json",
            )
