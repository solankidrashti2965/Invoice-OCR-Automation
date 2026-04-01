import os
import re
import json
import base64
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image, ImageFilter, ImageEnhance
import anthropic

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def preprocess_image(img: Image.Image) -> Image.Image:
    """Enhance image quality for better OCR accuracy."""
    # Convert to RGB if needed
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Upscale small images
    w, h = img.size
    if w < 1000 or h < 1000:
        scale = max(1000 / w, 1000 / h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Sharpen and increase contrast
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    return img


def image_to_base64(img: Image.Image) -> tuple[str, str]:
    """Convert PIL image to base64 string."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        img.save(tmp.name, "JPEG", quality=92)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    os.unlink(tmp_path)
    return data, "image/jpeg"


def extract_invoice_with_ai(img: Image.Image) -> dict:
    """Use Claude Vision to extract structured invoice fields."""
    img = preprocess_image(img)
    img_data, media_type = image_to_base64(img)

    prompt = """You are an expert invoice data extraction system. Analyze this invoice image and extract ALL available fields.

Return ONLY a valid JSON object (no markdown, no explanation) with this structure:
{
  "invoice_number": "string or null",
  "invoice_date": "string or null",
  "due_date": "string or null",
  "vendor": {
    "name": "string or null",
    "address": "string or null",
    "email": "string or null",
    "phone": "string or null",
    "tax_id": "string or null"
  },
  "bill_to": {
    "name": "string or null",
    "address": "string or null",
    "email": "string or null"
  },
  "line_items": [
    {
      "description": "string",
      "quantity": "string or null",
      "unit_price": "string or null",
      "amount": "string or null"
    }
  ],
  "subtotal": "string or null",
  "tax": "string or null",
  "discount": "string or null",
  "shipping": "string or null",
  "total": "string or null",
  "currency": "string or null",
  "payment_terms": "string or null",
  "payment_method": "string or null",
  "notes": "string or null",
  "po_number": "string or null",
  "confidence": "high|medium|low"
}

Rules:
- Extract EXACTLY what is written on the invoice, do not guess or fabricate
- For missing fields, use null
- For currency, detect from symbols ($ = USD, € = EUR, ₹ = INR, £ = GBP, etc.)
- confidence should reflect overall extraction quality
- Return ONLY the JSON object, nothing else"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/upload", methods=["POST"])
def upload_invoice():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    allowed = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".pdf"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        return jsonify({"error": f"Unsupported file type: {ext}"}), 400

    try:
        if ext == ".pdf":
            # For PDFs, convert first page to image
            try:
                import fitz  # PyMuPDF
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    file.save(tmp.name)
                    doc = fitz.open(tmp.name)
                    page = doc[0]
                    mat = fitz.Matrix(2, 2)
                    pix = page.get_pixmap(matrix=mat)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    doc.close()
                    os.unlink(tmp.name)
            except ImportError:
                return jsonify({"error": "PDF support requires PyMuPDF. Install with: pip install pymupdf"}), 500
        else:
            img = Image.open(file.stream)

        result = extract_invoice_with_ai(img)
        return jsonify({"success": True, "data": result})

    except json.JSONDecodeError as e:
        return jsonify({"error": f"AI returned invalid JSON: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
