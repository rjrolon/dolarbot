from flask import Flask, request
import requests
import re
import os
from datetime import datetime

# CONFIG
API_URL = "https://api.comparadolar.ar/quotes"
NOMBRES_OBJETIVO = ["cocos", "fiwind", "plus", "tiendadolar", "brubank", "letsbit"]
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
UMBRAL_ASK = 9999
INTERVALO_MINUTOS = 10

app = Flask(__name__)

@app.route('/')
def index():
    return "🟢 Bot corriendo (webhook)"

def enviar_mensaje_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")

def enviar_cotizaciones():
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
            mensaje += f"*{nombre}*: ${ask}
{item['url']}

"
        enviar_mensaje_telegram(mensaje)
    except Exception as e:
        print(f"Error al enviar cotizaciones: {e}")

def interpretar_comando(texto):
    match = re.match(r"(\d+)([mh])\s+(\d+)", texto.lower())
    if not match:
        return "❌ Formato inválido. Usa: `15m 1180` o `1h 1200`"
    cantidad = int(match.group(1))
    unidad = match.group(2)
    nuevo_umbral = int(match.group(3))
    minutos = cantidad * (60 if unidad == "h" else 1)
    global UMBRAL_ASK, INTERVALO_MINUTOS
    UMBRAL_ASK = nuevo_umbral
    INTERVALO_MINUTOS = minutos
    return f"✅ Monitoreo actualizado:\n• Cada *{minutos} minutos*\n• Umbral: *${nuevo_umbral}*"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        mensaje = update["message"]
        texto = mensaje["text"].strip().lower()
        chat_id = mensaje["chat"]["id"]
        if str(chat_id) != str(CHAT_ID):
            return "❌ Chat no autorizado", 403
        if texto in ["/cotizaciones", "cotizaciones"]:
            enviar_cotizaciones()
        else:
            respuesta = interpretar_comando(texto)
            enviar_mensaje_telegram(respuesta)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
