from flask import Flask, request, send_from_directory, send_file, after_this_request
import pandas as pd
import os

app = Flask(__name__)

# Function to mask data values
def mask_data(input_file, output_file):
    # Read the Excel file
    df = pd.read_excel(input_file)

    # Function to mask individual data values
    def mask_value(value):
        if isinstance(value, str):
            # Count letters and digits
            letters = sum(c.isalpha() for c in value)
            digits = sum(c.isdigit() for c in value)

            # Mask letters with 'X' and digits with '#'
            masked = 'X' * letters + '#' * digits
            return masked if masked else value
        elif isinstance(value, (int, float)):
            # Convert numbers to string and mask
            return '#' * len(str(value))
        else:
            # Return the value as is for other characters
            return value

    # Apply masking to the data_value column
    df['data_value'] = df['data_value'].apply(mask_value)

    # Save the modified dataframe to a new Excel file
    df.to_excel(output_file, index=False)

@app.route('/')
def upload_file():
    return send_from_directory('', 'index.html')

@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        f = request.files['file']
        input_path = os.path.join('uploads', f.filename)
        output_path = os.path.join('uploads', 'masked_' + f.filename)
        
        f.save(input_path)
        mask_data(input_path, output_path)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(input_path)
                os.remove(output_path)
            except Exception as error:
                app.logger.error("Error removing file: %s", error)
            return response
        
        return send_file(output_path, as_attachment=True)

# Serve CSS file
@app.route('/styles.css')
def serve_css():
    return send_from_directory('', 'styles.css')

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
