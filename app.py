from flask import Flask, request, jsonify, make_response
import os
import requests
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    # Обработка preflight-запросов
    if request.method == "OPTIONS":
        return cors_response({})

    try:
        data = request.get_json(silent=True) or {}
        user_prompt = data.get("prompt")
        image_base64 = data.get("image_base64")

        # Проверка входных данных
        if not user_prompt or not image_base64:
            logger.error("Missing prompt or image_base64")
            return cors_response({"error": "Prompt or image not provided"}, 400)

        # Проверка размера изображения
        image_size = len(image_base64)
        logger.info(f"Размер image_base64: {image_size} байт")
        if image_size > 4_000_000:  # Лимит 4 МБ
            logger.error("Image too large")
            return cors_response({"error": "Image size exceeds 4MB limit"}, 413)

        # Подготовка тела для Gemini
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

        # Запрос к Gemini API с таймаутом 7 секунд
        logger.info("Отправка запроса к Gemini API")
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=gemini_request,
            timeout=7  # Таймаут для Vercel
        )

        logger.info(f"Ответ Gemini API: status={response.status_code}")

        if response.status_code == 200:
            result = response.json()
            text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not text:
                logger.error("Пустой текстовый ответ от Gemini")
                return cors_response({"error": "Empty response from Gemini API"}, 500)
            return cors_response({"response": text})
        else:
            logger.error(f"Ошибка Gemini API: {response.status_code}, {response.text}")
            return cors_response({
                "error": "Gemini API error",
                "details": response.text
            }, response.status_code)

    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе к Gemini API")
        return cors_response({"error": "Request to Gemini API timed out"}, 504)
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка соединения с Gemini API")
        return cors_response({"error": "Connection error to Gemini API"}, 502)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к Gemini API: {str(e)}")
        return cors_response({"error": f"Request error: {str(e)}"}, 500)
    except Exception as e:
        logger.error(f"Внутренняя ошибка сервера: {str(e)}")
        return cors_response({"error": f"Server error: {str(e)}"}, 500)

# Запуск для Vercel (без изменений)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)