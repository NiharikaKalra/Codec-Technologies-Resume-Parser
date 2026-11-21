from flask import Flask, request, render_template_string
import pdfplumber
import sqlite3
import re
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 1. SQLite 
def init_db():
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    skills TEXT,
                    education TEXT
                )''')
    conn.commit()
    conn.close()

# 2. PDF 
def parse_resume(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    
    # Name
    name = lines[0] if lines else "Not Found"

    # email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_text)
    email = email_match.group(0) if email_match else "Not Found"

    # phone no 
    phone_match = re.search(r'\+?\d[\d -]{8,12}\d', full_text)
    phone = phone_match.group(0) if phone_match else "Not Found"

    # skills
    skill_keywords = ['python', 'java', 'c++', 'html', 'css', 'javascript', 'sql', 'flask', 'django', 'machine learning', 'excel']
    found_skills = [skill.upper() for skill in skill_keywords if skill in full_text.lower()]
    skills = ", ".join(found_skills) if found_skills else "No specific skills matched"

    # education
    edu_keywords = ['b.tech', 'b.e', 'bca', 'mca', 'b.sc', 'm.sc', 'mba', 'bachelor', 'master', 'diploma', '12th', '10th']
    found_edu = [edu.upper() for edu in edu_keywords if edu in full_text.lower()]
    education = ", ".join(found_edu) if found_edu else "Not Mentioned"

    return name, email, phone, skills, education

# 3. web page design
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Automated Resume Parser</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; padding: 30px; }
        .box { max-width: 750px; margin: auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #2c3e50; text-align: center; }
        .upload-form { text-align: center; margin-bottom: 25px; padding: 20px; border: 2px dashed #3498db; border-radius: 8px; }
        button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }
        th { background: #2c3e50; color: white; }
    </style>
</head>
<body>
<div class="box">
    <h2>📄 Automated Resume Parser</h2>
    <form class="upload-form" method="POST" enctype="multipart/form-data">
        <input type="file" name="resume" accept=".pdf" required>
        <button type="submit">Upload & Extract Details</button>
    </form>

    <h3>Saved Candidate Records (Database)</h3>
    <table>
        <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Skills</th>
            <th>Education</th>
        </tr>
        {% for row in records %}
        <tr>
            <td>{{ row[1] }}</td>
            <td>{{ row[2] }}</td>
            <td>{{ row[3] }}</td>
            <td>{{ row[4] }}</td>
            <td>{{ row[5] }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
</body>
</html>
"""

# 4. main root 
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['resume']
        if file and file.filename.endswith('.pdf'):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            
            name, email, phone, skills, education = parse_resume(filepath)
            
            conn = sqlite3.connect('resumes.db')
            c = conn.cursor()
            c.execute("INSERT INTO candidates (name, email, phone, skills, education) VALUES (?, ?, ?, ?, ?)",
                      (name, email, phone, skills, education))
            conn.commit()
            conn.close()

    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM candidates ORDER BY id DESC")
    records = c.fetchall()
    conn.close()

    return render_template_string(HTML_TEMPLATE, records=records)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
