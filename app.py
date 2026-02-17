import streamlit as st
from openai import OpenAI
import base64
from PIL import Image
import tempfile
import os

st.set_page_config(page_title="AI Invoice OCR", layout="centered")
st.title("🤖 AI Invoice Extraction")

client = OpenAI()

uploaded = st.file_uploader("Upload Invoice (Image or PDF)", type=["jpg", "jpeg", "png", "pdf"])

if uploaded:

    st.success("Processing with AI...")

    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(uploaded.read())
        file_path = f.name

    # Convert image to base64
    with open(file_path, "rb") as img_file:
        base64_image = base64.b64encode(img_file.read()).decode("utf-8")

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Extract all invoice details in JSON format. Include vendor name, invoice number, invoice date, due date, subtotal, tax, total amount, phone, GST if available."},
                        {
                            "type": "input_image",
                            "image_base64": base64_image,
                        },
                    ],
                }
            ],
        )

        result = response.output_text

        st.success("✅ Invoice processed successfully")

        with st.expander("📄 Extracted Details"):
            st.write(result)

    except Exception as e:
        st.error("❌ Error occurred")
        st.code(str(e))

    finally:
        os.remove(file_path)
