import os
import time
import requests
import html
from flask import Flask, request, render_template_string, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-me-in-production")

TELEGRAM_TOKEN = "8978439642:AAGSjQOggCU-C8_fP6Qj7QAEBvuCsgkGoRk"
TELEGRAM_CHAT_ID = "5244188429"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

RATE_LIMIT_SECONDS = 10

HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Сообщение Султану</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📩</text></svg>">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 40px 30px;
            max-width: 480px;
            width: 100%;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }
        h1 {
            font-size: 22px;
            color: #222;
            margin-bottom: 24px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .flash {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        .flash.success { background: #d4edda; color: #155724; }
        .flash.error   { background: #f8d7da; color: #721c24; }
        .flash.warning { background: #fff3cd; color: #856404; }
        textarea {
            width: 100%;
            min-height: 140px;
            padding: 14px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            resize: vertical;
            transition: border-color 0.2s;
        }
        textarea:focus { outline: none; border-color: #667eea; }
        button {
            width: 100%;
            margin-top: 16px;
            padding: 14px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(102,126,234,0.4); }
        button:active { transform: translateY(0); }
        .footer { margin-top: 18px; font-size: 13px; color: #888; }
    </style>
</head>
<body>
    <div class="card">
        <h1>НАПИШИ АНОНИМНОЕ СООБЩЕНИЕ СУЛТАНУ!</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <textarea name="message" placeholder="Ваше сообщение..." required maxlength="2000"></textarea>
            <button type="submit">Отправить анонимно</button>
        </form>
        
        <div class="footer">🔒 Ваше сообщение полностью конфиденциально</div>
    </div>
</body>
</html>
"""

def send_to_telegram(text):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()

@app.route("/")
def index_get():
    return render_template_string(HTML)

@app.route("/", methods=["POST"])
def index_post():
    msg = request.form.get("message", "").strip()
    
    if not msg:
        flash("Введите текст сообщения.", "error")
        return redirect(url_for("index_get"))
        
    last = session.get("last_sent_at", 0)
    now = time.time()
    if now - last < RATE_LIMIT_SECONDS:
        wait = int(RATE_LIMIT_SECONDS - (now - last))
        flash(f"Подождите {wait} сек. перед повторной отправкой.", "warning")
        return redirect(url_for("index_get"))
        
    session["last_sent_at"] = now
    safe_text = html.escape(msg)[:2000]
    final_text = f"📩 <b>Анонимное сообщение:</b>\n\n{safe_text}"
    
    try:
        send_to_telegram(final_text)
        flash("Сообщение успешно отправлено!", "success")
    except Exception as e:
        print(f"Ошибка Telegram: {e}")
        flash("Ошибка при отправке. Попробуйте позже.", "error")
        
    return redirect(url_for("index_get"))

@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
