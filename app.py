import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for Github Codespaces
CORS(app)

FREEIMAGE_API_KEY = "6d207e02198a847aa98d0a2a901485a5" 
ALBUM_ID = "DIt3l"
API_URL = "https://freeimage.host/api/1/upload"

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        
        files = {'source': (file.filename, file.stream, file.mimetype)}
        
        data = {
            'key': FREEIMAGE_API_KEY,
            'action': 'upload',
            'format': 'json',
            'album_id': ALBUM_ID 
        }

        print(f"Uploading {file.filename} to album {ALBUM_ID}...")
        response = requests.post(API_URL, data=data, files=files)
        
        api_response_json = response.json()
        print("API Response:", api_response_json)
        
        return jsonify(api_response_json), response.status_code

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "Proxy is online", "target_album": ALBUM_ID})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)