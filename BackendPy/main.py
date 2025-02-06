from flask import Flask, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import requests as r
import re
import base64
import os
import googlemaps

# Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
maps_api_key = os.getenv("GOOGLE_API_KEY")

client = Groq(api_key=api_key)
gmaps = googlemaps.Client(key=maps_api_key)
app = Flask(__name__)

with open("backendPy\prompt.txt", "r") as f:
    prompt = f.read().strip()

#Return Nearby Results
@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400
    
    base64_image = data['image']

    image_format = 'jpeg'  # Default to JPEG
    if base64_image.startswith('/9j/'):  # JPEG header in base64
        image_format = 'jpeg'
    elif base64_image.startswith('iVBORw0KGgo'):  # PNG header in base64
        image_format = 'png'
    else:
        return jsonify({"error": "Unsupported image format"}), 400

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt + "\nIMPORTANT FINAL NOTE: The response MUST be in the format of a PYTHON LIST with TWO ELEMENTS as such: [element1, element2]. Do not include any extra text or anything not in a list format."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="llama-3.2-90b-vision-preview",
            temperature=0.2
        )
        
        response = chat_completion.choices[0].message.content
        
        groqRequest = response[0]
        groqRequest2 = response[1]

        lat = data['latitude']
        long = data['longitude']
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{long}&radius=5000&type={groqRequest}&keyword={groqRequest2}&key={maps_api_key}"
        response = r.request("GET", url)
        return response.text

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Running Flask Application
if __name__ == "__main__":
    app.run(port=5000, debug=True)