from flask import Flask, request, render_template, send_file, redirect, url_for
import pandas as pd
import os
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def mask_data(file):
    # Read the Excel file from the uploaded file object
    df = pd.read_excel(file)

    # Check if 'termInstance' column contains 'Confidential', 'Restricted', or 'Protected' and mask the 'data_value' column
    df.loc[df['termInstance'].str.contains('Confidential|Restricted|Protected', case=False, na=False), 'data_value'] = 'XXXXXXX'

    # Save the modified dataframe to a BytesIO object
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False)
    writer.save()
    output.seek(0)  # Rewind the buffer

    return output

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        output = mask_data(file)
        return send_file(output, attachment_filename='Book1_masked.xlsx', as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)