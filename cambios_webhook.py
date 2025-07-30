from flask import Flask, request
import requests
from datetime import datetime
import os

# CONFIGURACIÓN
API_URL = "https://api.comparadolar.ar/quotes"
NOMBRES_OBJETIVO = ["cocos", "fiwind", "plus", "tiendadolar", "brubank", "letsbit"]
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # Opcional

app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Bot online (webhook activo)"

@app.route('/', methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 Payload recibido:", data)

    if "message" in data:
        mensaje = data["message"]
        chat_id = mensaje["chat"]["id"]
        texto = mensaje.get("text", "").strip().lower()

        print("💬 Mensaje:", texto)
        print("💬 Chat ID:", chat_id)

        if texto in ["/cotizaciones", "cotizaciones"]:
            enviar_cotizaciones(chat_id)
        else:
            enviar_mensaje(chat_id, "🤖 Usa /cotizaciones para ver los valores actuales.")
    return "ok", 200

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        print("✅ Mensaje enviado:", response.status_code)
    except Exception as e:
        print(f"❌ Error al enviar mensaje: {e}")

def enviar_cotizaciones(chat_id):
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        datos = response.json()

        objetivos = [item for item in datos if item["name"].lower() in NOMBRES_OBJETIVO]
        objetivos_ordenados = sorted(objetivos, key=lambda x: float(x["ask"]))
        hora = datetime.now().strftime("%H:%M:%S")

        mensaje = f"*📊 Cotizaciones – {hora}*\n\n"
        for item in objetivos_ordenados:
            nombre = item["prettyName"]
            ask = float(item["ask"])
            mensaje += f"*{nombre}*: ${ask}\n{item['url']}\n\n"

        enviar_mensaje(chat_id, mensaje)

    except Exception as e:
        print(f"❌ Error al obtener cotizaciones: {e}")
        enviar_mensaje(chat_id, "❌ Error al obtener cotizaciones.")

# INICIO FLASK
if __name__ == "__main__":
    print(f"🔄 Bot iniciado a las {datetime.now().strftime('%H:%M:%S')}")
    app.run(host="0.0.0.0", port=8080)
