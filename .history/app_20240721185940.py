from flask import Flask, request, send_from_directory, send_file, after_this_request
import pandas as pd
import os
import time
import logging
from io import BytesIO

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def mask_value(value):
    if isinstance(value, str):
        masked = []
        for char in value:
            if char.isalpha():
                masked.append('X')
            elif char.isdigit():
                masked.append('#')
            else:
                masked.append(char)
        return ''.join(masked)
    elif isinstance(value, (int, float)):
        return '#' * len(str(value))
    else:
        return value

def mask_data(metadata_file, data_file):
    metadata_df = pd.read_excel(metadata_file)
    data_df = pd.read_excel(data_file)

    sensitive_attributes = metadata_df[
        metadata_df['termInstance'].isin(['Confidential', 'Restricted', 'Protected'])
    ]['attribute_name'].tolist()

    for attribute in sensitive_attributes:
        if attribute in data_df.columns:
            data_df[attribute] = data_df[attribute].apply(mask_value)

    output = BytesIO()
    data_df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return output

@app.route('/')
def upload_file():
    return send_from_directory('', 'index.html')

@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        metadata_file = request.files['metadata_file']
        data_file = request.files['data_file']

        metadata_path = os.path.join('uploads', metadata_file.filename)
        data_path = os.path.join('uploads', data_file.filename)

        metadata_file.save(metadata_path)
        data_file.save(data_path)
        logging.info(f"Metadata file saved to {metadata_path}")
        logging.info(f"Data file saved to {data_path}")

        output = mask_data(metadata_path, data_path)
        logging.info("Data masked")

        @after_this_request
        def remove_file(response):
            try:
                time.sleep(1)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                    logging.info(f"Metadata file {metadata_path} removed")
                if os.path.exists(data_path):
                    os.remove(data_path)
                    logging.info(f"Data file {data_path} removed")
            except Exception as error:
                app.logger.error("Error removing file: %s", error)
            return response

        return send_file(output, as_attachment=True, download_name='masked_data.xlsx')

@app.route('/styles.css')
def serve_css():
    return send_from_directory('', 'styles.css')

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
