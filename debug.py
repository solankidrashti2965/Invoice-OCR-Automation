import sys
from PIL import Image
import pytesseract
import cv2
import numpy as np
import glob
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def debug_ocr(img_path):
    print(f"=== Process: {img_path} ===")
    pil_img = Image.open(img_path).convert("RGB")
    cv_img = np.array(pil_img)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    if max(h, w) < 2000:
        gray = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    gray_blur = cv2.medianBlur(gray, 3)
    thresh = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    processed_pil = Image.fromarray(thresh)
    page_text = pytesseract.image_to_string(processed_pil, config="--oem 3 --psm 6")
    print(page_text)
    print("="*40)

files = glob.glob(r"c:\Users\DRASHTI\OneDrive\文档\invoice_ocr_project\*.jpg")
files += glob.glob(r"c:\Users\DRASHTI\OneDrive\文档\invoice_ocr_project\*.webp")
for f in files:
    try:
        debug_ocr(f)
    except Exception as e:
        print("Error:", e)
