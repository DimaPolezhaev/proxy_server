# app.py
from flask import Flask, request, jsonify, make_response
import os
import requests

app = Flask(__name__)

# Ключ и URL Gemini из переменных окружения
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def cors_response(payload, status=200):
    """Обёртка для JSON-ответа с CORS-заголовками."""
    resp = make_response(jsonify(payload), status)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.route("/", methods=["GET", "OPTIONS"])
def home():
    if request.method == "OPTIONS":
        return cors_response({})
    return cors_response({"status": "✅ Gemini Proxy Server is running"})

@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    # Обработка preflight
    if request.method == "OPTIONS":
        return cors_response({})

    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt")
    image_b64 = data.get("image_base64")

    if not prompt or not image_b64:
        return cors_response({"error": "Prompt or image not provided"}, 400)

    # Подготовка тела для Gemini
    gemini_payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}
                ],
                "role": "user"
            }
        ]
    }

    # Запрос к Gemini API
    resp = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json=gemini_payload,
        timeout=30
    )

    if resp.status_code == 200:
        result = resp.json()
        # Берём первый текстовый кусок из ответа
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return cors_response({"response": text})
    else:
        return cors_response({
            "error": "Gemini API error",
            "details": resp.text
        }, resp.status_code)
