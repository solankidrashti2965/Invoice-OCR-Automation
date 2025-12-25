# =========================
# run_full_pipeline.py
# =========================

import sys
from pathlib import Path
from PIL import Image
import pytesseract
import re
import json
import dateparser   # ✅ FIXED

# ---------- CONFIG ----------
if len(sys.argv) > 1:
    IMG_PATH = Path(sys.argv[1])
else:
    IMG_PATH = Path("invoice_clean.jpg")

# Uncomment ONLY for Windows local run
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------- LOAD IMAGE ----------
try:
    img = Image.open(IMG_PATH).convert("RGB")
except Exception as e:
    raise SystemExit(f"Cannot open image: {e}")

# ---------- OCR ----------
text = pytesseract.image_to_string(img, config="--oem 3 --psm 6")

lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

# ---------- INITIALIZE ----------
invoice_no = ""
date_value = ""
vendor = ""
total_amount = ""
total_amount_numeric = ""
account_no = ""

# =========================================================
# 1️⃣ INVOICE NUMBER
# =========================================================
for ln in lines:
    m = re.search(r'Invoice\s*#?\s*(\d+)', ln, re.I)
    if m:
        invoice_no = m.group(1)
        break

# =========================================================
# 2️⃣ DATE (Invoice Date preferred)
# =========================================================
for ln in lines:
    if "invoice" in ln.lower() and "date" in ln.lower():
        date_candidate = re.findall(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', ln)
        if date_candidate:
            dp = dateparser.parse(date_candidate[0])
            if dp:
                date_value = dp.strftime("%Y-%m-%d")
                break

# =========================================================
# 3️⃣ TOTAL AMOUNT
# =========================================================
for ln in lines:
    if re.search(r'\btotal\b', ln, re.I):
        m = re.search(r'\$?\s*([\d,.]+)', ln)
        if m:
            total_amount_numeric = m.group(1).replace(",", "")
            total_amount = "$" + total_amount_numeric
            break

# =========================================================
# 4️⃣ PHONE / ACCOUNT NUMBER
# =========================================================
for ln in lines:
    m = re.search(r'\b\d{3}-\d{3}-\d{4}\b', ln)
    if m:
        account_no = m.group()
        break

# =========================================================
# 5️⃣ VENDOR NAME (TOP OF DOCUMENT)
# =========================================================
for ln in lines[:5]:
    if not re.search(r'\d', ln) and len(ln.split()) <= 4:
        vendor = ln
        break

# ---------- FINAL JSON ----------
output = {
    "invoice_number": invoice_no,
    "invoice_date": date_value,
    "vendor": vendor,
    "total_amount": total_amount,
    "total_amount_numeric": total_amount_numeric,
    "account_number": account_no,
    "raw_lines_count": len(lines)
}

print(json.dumps(output, indent=2))

# ---------- SAVE ----------
out_file = f"invoice_output_{IMG_PATH.stem}.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"SAVED_JSON: {Path(out_file).resolve()}")
