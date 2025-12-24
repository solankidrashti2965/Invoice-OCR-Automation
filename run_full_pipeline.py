# =========================
# run_full_pipeline.py
# =========================

import sys
from pathlib import Path
from PIL import Image
import pytesseract
import re
import json
#import dateparser

# ---------- CONFIG ----------
# Accept image path from command line (EXE / UiPath / CLI)
if len(sys.argv) > 1:
    IMG_PATH = Path(sys.argv[1])
else:
    IMG_PATH = Path("invoice_clean.jpg")

#pytesseract.pytesseract.tesseract_cmd = (
#   r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---------- LOAD IMAGE ----------
try:
    img = Image.open(IMG_PATH).convert("RGB")
except Exception as e:
    raise SystemExit(f"Cannot open image: {e}")

# ---------- OCR ----------
text = pytesseract.image_to_string(img, config="--oem 3 --psm 6")

print("\n================ FULL OCR TEXT ================\n")
print(text)
print("\n================================================\n")

lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

print("\n--- OCR: first 12 lines (for inspection) ---")
for i, ln in enumerate(lines[:12], 1):
    print(f"{i}. {ln}")

# ---------- INITIALIZE FIELDS ----------
invoice_no = ""
date_value = ""
vendor = ""
total_amount = ""
total_amount_numeric = ""
account_no = ""

# =========================================================
# 1️⃣ INVOICE NUMBER  (ONLY "Invoice # <digits>")
# =========================================================
for ln in lines:
    m = re.search(r'Invoice\s*#\s*(\d+)', ln, re.I)
    if m:
        invoice_no = m.group(1)
        break

# =========================================================
# 2️⃣ DATE EXTRACTION (Invoice Date preferred)
# =========================================================
for ln in lines:
    m = re.search(r'Invoice\s*date\s*([0-9\/\-]+)', ln, re.I)
    if m:
        dp = dateparser.parse(
            m.group(1),
            settings={"PREFER_DAY_OF_MONTH": "first"}
        )
        if dp:
            date_value = dp.strftime("%Y-%m-%d")
            break

# =========================================================
# 3️⃣ TOTAL AMOUNT (ONLY line starting with "Total")
# =========================================================
for ln in lines:
    if re.match(r'^Total\b', ln, re.I):
        m = re.search(r'\$([\d,.]+)', ln)
        if m:
            total_amount = "$" + m.group(1)
            total_amount_numeric = m.group(1).replace(",", "")
            break

# =========================================================
# 4️⃣ ACCOUNT / PHONE NUMBER
# =========================================================
for ln in lines:
    m = re.search(r'\b\d{3}-\d{3}-\d{4}\b', ln)
    if m:
        account_no = m.group()
        break

# =========================================================
# 5️⃣ VENDOR NAME (TOP LINES, REMOVE PHONE)
# =========================================================
for ln in lines[:6]:
    if re.search(r'landscaping', ln, re.I):
        vendor = re.sub(r'\d{3}-\d{3}-\d{4}', '', ln).strip()
        break

# ---------- FINAL DEBUG ----------
print("\n--- Final Extraction Debug ---")
print("Invoice No :", invoice_no)
print("Date       :", date_value)
print("Vendor     :", vendor)
print("Total      :", total_amount)
print("Total num  :", total_amount_numeric)
print("Account No :", account_no)

# ---------- FINAL JSON ----------
output = {
    "invoice_number": invoice_no,
    "date": date_value,
    "vendor": vendor,
    "total_amount": total_amount,
    "total_amount_numeric": total_amount_numeric,
    "account_number": account_no,
    "raw_lines_count": len(lines)
}

print("\n--- Final Extracted JSON ---")
print(json.dumps(output, indent=2, ensure_ascii=False))

# ---------- SAVE JSON ----------
out_file = f"invoice_output_{IMG_PATH.stem}.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSAVED_JSON: {Path(out_file).resolve()}")
