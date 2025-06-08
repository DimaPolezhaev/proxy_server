from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Получаем API-ключ из переменной окружения
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    user_prompt = data.get("prompt")
    image_base64 = data.get("image_base64")

    if not user_prompt or not image_base64:
        return jsonify({"error": "Prompt or image not provided"}), 400

    # Формируем запрос к Gemini API
    gemini_request = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": user_prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "topK": 32,
            "topP": 1,
            "maxOutputTokens": 1024,
            "stopSequences": [],
            "candidateCount": 1,
            "enable_deep_research": True  # 👈 добавлен флаг
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_DEROGATORY", "threshold": 3},
            {"category": "HARM_CATEGORY_VIOLENCE", "threshold": 3},
            {"category": "HARM_CATEGORY_SEXUAL", "threshold": 3},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": 3}
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

# Запуск для локального тестирования или для Vercel
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
