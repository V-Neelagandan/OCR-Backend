from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pytesseract
from werkzeug.utils import secure_filename
import json
from pdf2image import convert_from_path
from PIL import Image

# Setup Flask app
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
JSON_FILE = 'extracted.json'
# ✅ Update this path after Poppler install
POPPLER_PATH = r'C:\Users\Neelagandan\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Set Tesseract path (for Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# 🧠 Helper: Check file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'pdf']


# 🧠 Helper: Extract text from image
def extract_text_from_image(img_path):
    try:
        image = Image.open(img_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"Image OCR Error: {str(e)}"


# 🧠 Helper: Extract text from PDF (convert to image)
def extract_text_from_pdf(pdf_path):
    try:
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        text = ''
        for img in images:
            text += pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"PDF OCR Error: {str(e)}"


# 📤 Upload Route
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(filepath)
        else:
            extracted_text = extract_text_from_image(filepath)

        entry = {
            "filename": filename,
            "extract_text": extracted_text.strip()
        }

        data = []
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, 'r') as f:
                    data = json.load(f)
            except:
                data = []

        data.append(entry)

        with open(JSON_FILE, "w") as f:
            json.dump(data, f, indent=2)

        return jsonify({"message": "File uploaded and text extracted"}), 200

    return jsonify({"error": "Unsupported file type"}), 400


# 📄 Retrieve extracted OCR results
@app.route('/retrieve', methods=['GET'])
def retrieve_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify([])


# 🖼 Serve uploaded image or PDF (preview support)
@app.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
