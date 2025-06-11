# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)  # Разрешим все CORS-запросы

# Переменная окружения с ключом Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# URL модели Gemini
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@app.route("/", methods=["GET"])
def home():
    return "✅ Gemini Proxy Server is running"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    user_prompt = data.get("prompt")
    image_base64 = data.get("image_base64")

    if not user_prompt or not image_base64:
        return jsonify({"error": "Prompt or image not provided"}), 400

    # Формируем тело запроса к Gemini
    gemini_request = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ],
                "role": "user"
            }
        ]
    }

    # Отправляем запрос к Gemini API
    resp = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json=gemini_request,
        timeout=30
    )

    if resp.status_code == 200:
        result = resp.json()
        # Берём текст первого кандидата
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"response": text})
    else:
        return jsonify({
            "error": "Gemini API error",
            "details": resp.text
        }), resp.status_code
