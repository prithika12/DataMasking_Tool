from flask import Flask, request, send_from_directory, send_file, after_this_request, Response
import pandas as pd
import os

app = Flask(__name__)

# Function to mask data values
def mask_data(input_file, output_file):
    # Read the Excel file
    df = pd.read_excel(input_file)

    # Check if 'termInstance' column contains 'Confidential' or 'Restricted' and mask the 'data_value' column
    df.loc[df['termInstance'].str.contains('Confidential|Restricted|Protected', case=False, na=False), 'data_value'] = 'XXXXXXX'

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

        def generate():
            with open(output_path, 'rb') as f:
                yield from f
            # After sending the file, remove it
            try:
                os.remove(output_path)
            except Exception as error:
                app.logger.error("Error removing file after sending: %s", error)

        response = Response(generate(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response.headers['Content-Disposition'] = f'attachment; filename={os.path.basename(output_path)}'
        return response

#CSS file
@app.route('/styles.css')
def serve_css():
    return send_from_directory('', 'styles.css')

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
