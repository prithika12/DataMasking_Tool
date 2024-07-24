from flask import Flask, request, send_from_directory, send_file, after_this_request
import pandas as pd
import os
import time
import logging
from io import BytesIO
import random
import string
from faker import Faker

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

fake = Faker()

# Mapping of attribute names to Faker methods
faker_methods = {
    'name': fake.first_name,
    'address': fake.address,
    'email': fake.email,
    'phone_number': fake.phone_number,
    'company': fake.company,
    'job': fake.job,
    'date_of_birth': fake.date_of_birth,
    'credit_card_number': fake.credit_card_number,
    'ssn': fake.ssn
}

def generate_random_string(length, chars):
    return ''.join(random.choice(chars) for _ in range(length))

def mask_value(value, column_name):
    # Normalize the column name to lower case for comparison
    normalized_column_name = column_name.lower()

    # Find a matching Faker method based on column name
    for key, faker_method in faker_methods.items():
        if key in normalized_column_name:
            if key == 'email':
                # Extract parts of the original email
                if isinstance(value, str) and '@' in value:
                    local_part, domain_part = value.split('@', 1)
                    domain, ext = domain_part.rsplit('.', 1)
                    
                    # Generate parts using Faker
                    fake_local = fake.user_name()[:len(local_part)]
                    fake_domain = fake.domain_name().split('.')[0][:len(domain)]
                    fake_ext = fake.domain_suffix().lstrip('.')
                    
                    # Construct new email with similar structure
                    faker_value = f"{fake_local}@{fake_domain}.{fake_ext[:len(ext)]}"
                    
                    # Ensure the format is preserved
                    return ''.join(
                        f_char if f_char.isalpha() or f_char in '@._-' else random.choice(string.ascii_lowercase)
                        for f_char in faker_value
                    )
            
            faker_value = faker_method()
            # Ensure faker_value matches the length of the original value
            if isinstance(value, str):
                if len(faker_value) < len(value):
                    faker_value = faker_value.ljust(len(value), 'x')
                elif len(faker_value) > len(value):
                    faker_value = faker_value[:len(value)]
                # Preserve original letter case in Faker-generated values
                return ''.join(
                    f_char.upper() if o_char.isupper() else f_char.lower()
                    for o_char, f_char in zip(value, faker_value)
                )
            return faker_value
    
    # Default masking behavior for other types
    if isinstance(value, str):
        # Ensure the masked value has the same length and format
        masked = []
        for char in value:
            if char.isalpha():
                if char.islower():
                    masked.append(random.choice(string.ascii_lowercase))
                elif char.isupper():
                    masked.append(random.choice(string.ascii_uppercase))
            elif char.isdigit():
                masked.append(random.choice(string.digits))
            else:
                masked.append(char)
        return ''.join(masked).ljust(len(value), 'x')[:len(value)]
    elif isinstance(value, (int, float)):
        return generate_random_string(len(str(value)), string.digits)
    else:
        return value

def mask_data(metadata_file, data_file):
    metadata_df = pd.read_excel(metadata_file)
    data_df = pd.read_excel(data_file)

    # Store the original data types
    original_dtypes = data_df.dtypes

    sensitive_attributes = metadata_df[
        metadata_df['termInstance'].isin(['Confidential', 'Restricted', 'Protected'])
    ]['attribute_name'].tolist()

    for attribute in sensitive_attributes:
        if attribute in data_df.columns:
            # Apply masking
            data_df[attribute] = data_df[attribute].apply(lambda x: mask_value(x, attribute))
    
    # Revert the data types to the original types
    data_df = data_df.astype(original_dtypes)

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
        metadata_file = request.files['file1']
        data_file = request.files['file2']

        metadata_path = os.path.join('uploads', 'metadata_file.xlsx')
        data_path = os.path.join('uploads', 'data_file.xlsx')

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
