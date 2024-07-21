from flask import Flask, request, send_from_directory, send_file, after_this_request
import pandas as pd
import os
import time
import logging
from io import BytesIO


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


def mask_data(input_file):
    df = pd.read_excel(input_file)


    # Function to mask individual data values
    def mask_value(value):
        if isinstance(value, str):
            # Masking based on character types
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
            # Convert numbers to string and mask
            return '#' * len(str(value))
        else:
            # Return the value as is for other characters
            return value




    df['data_value'] = df['data_value'].apply(mask_value)


    # Save the modified DataFrame to a BytesIO object instead of a file
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)  # Rewind the BytesIO object to the beginning


    return output


@app.route('/')
def upload_file():
    return send_from_directory('', 'index.html')


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        f = request.files['file']
        input_path = os.path.join('uploads', f.filename)
       
        f.save(input_path)
        logging.info(f"File saved to {input_path}")
       
        # Get the masked data as a BytesIO object
        output = mask_data(input_path)
        logging.info("Data masked")


        @after_this_request
        def remove_file(response):
            try:
                time.sleep(1)
                if os.path.exists(input_path):
                    os.remove(input_path)
                    logging.info(f"File {input_path} removed")
            except Exception as error:
                app.logger.error("Error removing file: %s", error)
            return response


        return send_file(output, as_attachment=True, download_name='masked_' + f.filename)


@app.route('/styles.css')
def serve_css():
    return send_from_directory('', 'styles.css')


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)