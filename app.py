import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Память текущих диалогов Алисы

conversations = {}

SYSTEM_PROMPT = """
Ты — интеллектуальный голосовой ассистент.

Твои основные принципы:

1. Отвечай только по существу вопроса.
2. Не добавляй приветствия, вежливые фразы, комплименты, эмоциональные комментарии и другую воду.
3. Не повторяй вопрос пользователя.
4. Не используй фразы вроде «конечно», «разумеется», «рад помочь», «давай разберёмся» и подобные вводные конструкции.
5. Отвечай кратко, конкретно и логично. Если для полноценного ответа нужны подробности — дай только необходимые подробности.
6. Не выдумывай факты, источники, цифры, события, цитаты или сведения, которых у тебя нет.
7. Если точного ответа нет или информация неизвестна, прямо скажи об этом. Не пытайся угадать.
8. Чётко отделяй установленные факты от предположений и оценок.
9. Если вопрос содержит ошибочное утверждение, укажи на ошибку и дай правильную информацию.
10. Если существует несколько вариантов ответа и невозможно определить правильный без дополнительных данных, укажи это и назови необходимые данные.
11. Не скрывай неопределённость. Если информация может быть устаревшей или зависит от текущих обстоятельств, скажи об этом.
12. Не используй чрезмерное форматирование. Ответ должен нормально восприниматься на слух.
13. Не используй таблицы, если ответ предназначен для голосового воспроизведения.
14. Не делай выводов, которые не следуют из имеющихся данных.
15. При сложных вопросах сначала обдумай информацию и только после этого сформулируй краткий итоговый ответ.
16. Если пользователь просит мнение, явно обозначай, что это оценка, а не установленный факт.
17. При медицинских, юридических, финансовых и других важных вопросах не выдавай предположение за установленный факт.

Главный принцип:
ТОЧНОСТЬ > ПОЛНОТА > КРАТКОСТЬ.

Не добавляй информацию только ради увеличения объёма ответа.
"""


@app.route("/", methods=["GET"])
def home():
    return "Alice ChatGPT server is running!"


@app.route("/alice", methods=["POST"])
def alice():
    data = request.get_json(silent=True) or {}

    request_data = data.get("request", {})
    session = data.get("session", {})

    user_text = request_data.get("command", "").strip()
    session_id = session.get("session_id", "default")

    # Если пользователь только запустил навык
    if not user_text:
        return jsonify({
            "response": {
                "text": "Привет! Я готова. Что ты хочешь узнать?",
                "end_session": False
            },
            "version": "1.0"
        })

    try:
        previous_response_id = conversations.get(session_id)

        if previous_response_id:
            response = client.responses.create(
                model="gpt-5-mini",
                previous_response_id=previous_response_id,
                input=user_text
            )
        else:
            response = client.responses.create(
                model="gpt-5-mini",
                instructions=SYSTEM_PROMPT,
                input=user_text
            )

        answer = response.output_text.strip()

        # Запоминаем последний ответ для продолжения разговора
        conversations[session_id] = response.id

        # Алиса лучше работает с достаточно короткими голосовыми ответами
        if len(answer) > 4000:
            answer = answer[:3990] + "..."

        return jsonify({
            "response": {
                "text": answer,
                "end_session": False
            },
            "version": "1.0"
        })

    except Exception as e:
        print("ERROR:", e)

        return jsonify({
            "response": {
                "text": "Извини, сейчас не получилось получить ответ. Попробуй ещё раз.",
                "end_session": False
            },
            "version": "1.0"
        })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
