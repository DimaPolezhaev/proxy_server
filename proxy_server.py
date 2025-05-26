from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("AIzaSyBU4Qvoc_gBsJ_EjD6OeToGl9cDrInANSg")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    user_prompt = data.get("prompt")

    if not user_prompt:
        return jsonify({"error": "No prompt provided"}), 400

    gemini_request = {
        "contents": [
            {
                "parts": [{"text": user_prompt}],
                "role": "user"
            }
        ]
    }

    response = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json=gemini_request
    )

    if response.status_code == 200:
        result = response.json()
        return jsonify({
            "response": result["candidates"][0]["content"]["parts"][0]["text"]
        })
    else:
        return jsonify({"error": "Gemini API error", "details": response.text}), response.status_code

@app.route("/", methods=["GET"])
def home():
    return "Gemini Proxy Server is running"

if __name__ == "__main__":
    app.run(debug=True)
