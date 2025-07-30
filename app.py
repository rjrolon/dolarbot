from flask import Flask, request
import threading
import requests
import time
import re
import schedule
from datetime import datetime
import os

# CONFIG
API_URL = "https://api.comparadolar.ar/quotes"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
NOMBRES_OBJETIVO = ["cocos", "fiwind", "plus", "tiendadolar", "brubank", "letsbit"]
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
UMBRAL_ASK = 9999
INTERVALO_MINUTOS = 10

app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Bot activo."

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        chat_id = str(data["message"]["chat"]["id"])
        texto = data["message"]["text"].strip().lower()
        if chat_id == CHAT_ID:
            if texto in ["/cotizaciones", "cotizaciones"]:
                enviar_cotizaciones_iniciales()
            else:
                respuesta = interpretar_comando(texto)
                enviar_mensaje_telegram(respuesta)
    return '', 200

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
        print(f"❌ Error al enviar mensaje: {e}")

def enviar_cotizaciones_iniciales():
    try:
        response = requests.get(API_URL, headers=HEADERS)
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
        enviar_mensaje_telegram(mensaje)
    except Exception as e:
        enviar_mensaje_telegram(f"❌ Error al obtener cotizaciones:\n{e}")

def verificar_ask():
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        datos = response.json()
        objetivos = [item for item in datos if item["name"].lower() in NOMBRES_OBJETIVO]
        objetivos_ordenados = sorted(objetivos, key=lambda x: float(x["ask"]))
        lineas_alerta = []
        for item in objetivos_ordenados:
            nombre = item["prettyName"]
            ask = float(item["ask"])
            if ask < UMBRAL_ASK:
                linea = f"*{nombre}*: ${ask} 🔻\n{item['url']}"
                lineas_alerta.append(linea)
        if lineas_alerta:
            mensaje = "⚠️ *ALERTA DE DÓLAR* ⚠️\n\n" + "\n\n".join(lineas_alerta)
            enviar_mensaje_telegram(mensaje)
    except Exception as e:
        print(f"❌ Error al verificar ask: {e}")

def interpretar_comando(texto):
    global UMBRAL_ASK, INTERVALO_MINUTOS
    match = re.match(r"(\d+)([mh])\s+(\d+)", texto.lower())
    if not match:
        return "❌ Formato inválido. Usa: `15m 1180` o `1h 1200`"
    cantidad = int(match.group(1))
    unidad = match.group(2)
    nuevo_umbral = int(match.group(3))
    INTERVALO_MINUTOS = cantidad * (60 if unidad == "h" else 1)
    UMBRAL_ASK = nuevo_umbral
    schedule.clear()
    schedule.every(INTERVALO_MINUTOS).minutes.do(verificar_ask)
    return f"✅ Monitoreo actualizado:\n• Cada *{INTERVALO_MINUTOS} minutos*\n• Umbral: *${UMBRAL_ASK}*"

def iniciar_bot():
    print(f"🔄 Bot iniciado a las {datetime.now().strftime('%H:%M:%S')}")
    enviar_cotizaciones_iniciales()
    schedule.every(INTERVALO_MINUTOS).minutes.do(verificar_ask)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=iniciar_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
