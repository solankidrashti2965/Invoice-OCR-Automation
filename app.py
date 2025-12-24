import streamlit as st
from PIL import Image
import pytesseract
import re
import tempfile
import os

st.title("📄 Invoice OCR")
st.write("Upload an invoice image")

uploaded = st.file_uploader("Choose file", type=['jpg', 'png', 'jpeg'])

if uploaded:
    st.image(uploaded, width=400)
    
    # Save file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
        f.write(uploaded.getvalue())
        temp = f.name
    
    try:
        # OCR
        img = Image.open(temp)
        text = pytesseract.image_to_string(img)
        
        # Find invoice number
        inv_match = re.search(r'Invoice\s*#?\s*(\d+)', text, re.I)
        invoice = inv_match.group(1) if inv_match else "Not found"
        
        # Find total
        total_match = re.search(r'Total\s*\$?\s*([\d,.]+)', text, re.I)
        total = "$" + total_match.group(1) if total_match else "Not found"
        
        # Show results
        st.success("✅ Done!")
        st.write(f"**Invoice #:** {invoice}")
        st.write(f"**Total Amount:** {total}")
        
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        if os.path.exists(temp):
            os.remove(temp)