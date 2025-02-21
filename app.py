from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pdfplumber
import re
from transformers import pipeline, AutoTokenizer
from models import db, User, bcrypt
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ehr_users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "super_secret_key"

db.init_app(app)

# Load NLP model
model_name = "Falconsai/medical_summarization"
summarizer = pipeline("summarization", model=model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)


# Function to split text into chunks
def split_text_into_chunks(text, max_length=2056):
    tokens = tokenizer.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_length):
        chunk = tokenizer.decode(tokens[i:i + max_length], skip_special_tokens=True)
        chunks.append(chunk)
    return chunks
# Function to summarize text
def summarize_text(text):
    chunks = split_text_into_chunks(text)
    summaries = [summarizer(chunk)[0]['summary_text'] for chunk in chunks]
    return " ".join(summaries)


def extract_blood_data_and_remarks(pdf_file):
    try:
        data = []
        remarks_list = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Extract remarks section
                    remarks_match = re.search(r'Remarks:\s*(.*?)(?=Authorized by:|$)', text, re.DOTALL)
                    if remarks_match:
                        remarks_text = remarks_match.group(1).strip()
                        # Extract individual lines from the remarks (split by newline or bullet point)
                        remarks_lines = re.split(r'\n|•', remarks_text)
                        remarks_lines = [line.strip() for line in remarks_lines if line.strip()]
                        first_three_lines = "\n".join(remarks_lines[:3])
                        remarks_list.append(first_three_lines)

                    # Extract key blood parameters
                    date_match = re.search(r'Date of Test:\s*([\w\s,]+)', text)
                    hemoglobin_match = re.search(r'Hemoglobin \(Hb\)\s*([\d.]+)', text)
                    rbc_match = re.search(r'Red Blood Cell Count \(RBC\)\s*([\d.]+)', text)
                    wbc_match = re.search(r'White Blood Cell Count \(WBC\)\s*([\d.]+)', text)
                    platelets_match = re.search(r'Platelet Count\s*([\d,]+)', text)
                    hct_match = re.search(r'Hematocrit \(HCT\)\s*([\d.]+)', text)

                    if date_match and hemoglobin_match and rbc_match and wbc_match and platelets_match and hct_match:
                        data.append({
                            'Date': date_match.group(1),
                            'Hemoglobin': float(hemoglobin_match.group(1)),
                            'RBC': float(rbc_match.group(1)),
                            'WBC': float(wbc_match.group(1)),
                            'Platelets': int(platelets_match.group(1).replace(',', '')),
                            'HCT': float(hct_match.group(1)),
                        })
        
        combined_remarks = " ".join(remarks_list)  # Combine all remarks from the reports
        return data, combined_remarks

    except Exception as e:
        raise ValueError(f"Error extracting data: {str(e)}")

# Route: Home
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):

            session['logged_in'] = True
            session['username'] = username
            session['role'] = user.role

            if user.role == "patient":
                return redirect(url_for('patient_dashboard'))  # ✅ Redirect to the correct page
            elif user.role == "doctor":
                return redirect(url_for('doctor_dashboard'))
            elif user.role == "nurse":
                return redirect(url_for('nurse_dashboard'))
            elif user.role == "admin":
                return redirect(url_for('admin_dashboard'))

        return render_template('login.html', message="Incorrect Details")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Route: Patient Dashboard
@app.route('/patient_dashboard')
def patient_dashboard():
    if session.get('role') == "patient":
        return render_template('patient_dashboard.html', username=session['username'])
    return redirect(url_for('home'))

# Route: Doctor Dashboard
@app.route('/doctor_dashboard')
def doctor_dashboard():
    if session.get('role') == "doctor":
        return render_template('doctor_dashboard.html', username=session['username'])
    return redirect(url_for('home'))

# Route: Nurse Dashboard
@app.route('/nurse_dashboard')
def nurse_dashboard():
    if session.get('role') == "nurse":
        return render_template('nurse_dashboard.html', username=session['username'])
    return redirect(url_for('home'))

# Route: Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') == "admin":
        return render_template('admin_dashboard.html', username=session['username'])
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    session.pop("user", None)  # Remove user session
    return redirect(url_for("login"))

# Route: Upload Blood Report
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    files = request.files.getlist('file')  # Handle multiple files
    all_data = []
    all_remarks = []

    try:
        for file in files:
            extracted_data, remarks = extract_blood_data_and_remarks(file)
            all_data.extend(extracted_data)
            all_remarks.append(remarks)

        if not all_data:
            return jsonify({'error': 'No valid data found in the PDFs'}), 400

        combined_remarks = " ".join(all_remarks)
        remarks_summary = summarize_text(combined_remarks) if combined_remarks else "No remarks available."

        return jsonify({'data': all_data, 'remarks_summary': remarks_summary}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
