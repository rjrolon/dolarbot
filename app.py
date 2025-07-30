
from flask import Flask, request
import requests
import os
from datetime import datetime

API_URL = "https://api.comparadolar.ar/quotes"
NOMBRES_OBJETIVO = ["cocos", "fiwind", "plus", "tiendadolar", "brubank", "letsbit"]
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "🟢 Bot corriendo correctamente"

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        texto = data["message"]["text"].strip().lower()
        if str(chat_id) != str(CHAT_ID):
            return "ignorado"
        if texto == "/cotizaciones":
            enviar_cotizaciones(chat_id)
    return "ok"

def enviar_mensaje(chat_id, mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown",
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")

def enviar_cotizaciones(chat_id):
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        datos = response.json()
        objetivos = [item for item in datos if item["name"].lower() in NOMBRES_OBJETIVO]
        objetivos_ordenados = sorted(objetivos, key=lambda x: float(x["ask"]))
        hora = datetime.now().strftime("%H:%M:%S")
        mensaje = f"*📊 Cotizaciones – {hora}*

"
        for item in objetivos_ordenados:
            nombre = item["prettyName"]
            ask = float(item["ask"])
            mensaje += f"*{nombre}*: ${ask}\n{item['url']}\n\n"
        enviar_mensaje(chat_id, mensaje)
    except Exception as e:
        enviar_mensaje(chat_id, "❌ Error al obtener cotizaciones.")
        print(f"Error al obtener cotizaciones: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
