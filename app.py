from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Используем переменную окружения для API-ключа
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    user_prompt = data.get("prompt")
    image_base64 = data.get("image_base64")  # Ожидаем base64 изображение

    if not user_prompt or not image_base64:
        return jsonify({"error": "Prompt or image not provided"}), 400

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
        return jsonify({
            "error": "Gemini API error",
            "details": response.text
        }), response.status_code

@app.route("/", methods=["GET"])
def home():
    return "✅ Gemini Proxy Server is running"

# Запуск для Vercel
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)