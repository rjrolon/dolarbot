from flask import Flask
import threading
import requests
import time
import schedule
import re
from datetime import datetime
import os

# CONFIG
API_URL = "https://api.comparadolar.ar/quotes"
NOMBRES_OBJETIVO = ["cocos", "fiwind", "plus", "tiendadolar", "brubank", "letsbit"]
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
UMBRAL_ASK = 9999
INTERVALO_MINUTOS = 10

# FLASK PARA MANTENER RENDER ACTIVO
app = Flask(__name__)

@app.route('/')
def index():
    return "🟢 Bot corriendo correctamente"

def enviar_mensaje_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown",
        "reply_markup": {
            "keyboard": [[{"text": "/cotizaciones"}]],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")

def enviar_cotizaciones_iniciales():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        datos = response.json()
        objetivos = [item for item in datos if item["name"].lower() in NOMBRES_OBJETIVO]
        objetivos_ordenados = sorted(objetivos, key=lambda x: float(x["ask"]))
        hora = datetime.now().strftime("%H:%M:%S")
        mensaje = f"*📊 Cotizaciones Iniciales – {hora}*

"
        for item in objetivos_ordenados:
            nombre = item["prettyName"]
            ask = float(item["ask"])
            mensaje += f"*{nombre}*: ${ask}\n{item['url']}\n\n"
        enviar_mensaje_telegram(mensaje)
    except Exception as e:
        print(f"Error al enviar cotizaciones iniciales: {e}")

def verificar_ask():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        datos = response.json()
        objetivos = [item for item in datos if item["name"].lower() in NOMBRES_OBJETIVO]
        objetivos_ordenados = sorted(objetivos, key=lambda x: float(x["ask"]))
        print("\n--- Cotizaciones ordenadas por 'ask' ---")
        lineas_alerta = []
        for item in objetivos_ordenados:
            nombre = item["prettyName"]
            ask = float(item["ask"])
            print(f"{nombre}: ${ask}")
            if ask < UMBRAL_ASK:
                linea = f"*{nombre}*: ${ask} 🔻\n{item['url']}"
                lineas_alerta.append(linea)
        if lineas_alerta:
            mensaje = "⚠️ *ALERTA DE DÓLAR* ⚠️\n\n" + "\n\n".join(lineas_alerta)
            enviar_mensaje_telegram(mensaje)
    except Exception as e:
        print(f"Error al verificar: {e}")

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

def escuchar_telegram():
    offset = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            if offset:
                url += f"?offset={offset}"
            response = requests.get(url)
            data = response.json()
            for update in data["result"]:
                offset = update["update_id"] + 1
                mensaje = update.get("message")
                if mensaje and "text" in mensaje and str(mensaje["chat"]["id"]) == CHAT_ID:
                    texto = mensaje["text"].strip().lower()
                    if texto in ["/cotizaciones", "cotizaciones"]:
                        enviar_cotizaciones_iniciales()
                    else:
                        respuesta = interpretar_comando(texto)
                        enviar_mensaje_telegram(respuesta)
        except Exception as e:
            print(f"Error en Telegram listener: {e}")
        time.sleep(5)

def iniciar_bot():
    print(f"🔄 Bot iniciado a las {datetime.now().strftime('%H:%M:%S')}")
    enviar_cotizaciones_iniciales()
    schedule.every(INTERVALO_MINUTOS).minutes.do(verificar_ask)
    threading.Thread(target=escuchar_telegram, daemon=True).start()
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=iniciar_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
