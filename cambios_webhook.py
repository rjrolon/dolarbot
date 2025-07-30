from flask import Flask, request
import requests
import os
from datetime import datetime

# CONFIG
API_URL = "https://api.comparadolar.ar/quotes"
NOMBRES_OBJETIVO = ["cocos", "fiwind", "plus", "tiendadolar", "brubank", "letsbit"]
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# FLASK APP
app = Flask(__name__)

@app.route('/')
def home():
    return '🟢 Bot corriendo correctamente'

@app.route('/', methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        mensaje = data["message"]["text"]
        chat_id = str(data["message"]["chat"]["id"])
        if chat_id != str(CHAT_ID):
            print("🔒 Mensaje ignorado: no es el chat autorizado.")
            return '', 200

        print("📩 Mensaje recibido:", mensaje)

        if mensaje.lower().strip() == "/cotizaciones":
            enviar_cotizaciones(chat_id)
        else:
            enviar_mensaje(chat_id, "❌ Comando no reconocido.")
    except Exception as e:
        print("❌ Error en webhook:", e)
    return '', 200

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload)
        print("📤 Mensaje enviado:", texto)
    except Exception as e:
        print("❌ Error enviando mensaje:", e)

def enviar_cotizaciones(chat_id):
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        datos = response.json()
        if not isinstance(datos, list):
            raise ValueError("La API no devolvió una lista válida.")

        objetivos = [item for item in datos if item["name"].lower() in NOMBRES_OBJETIVO]
        objetivos_ordenados = sorted(objetivos, key=lambda x: float(x["ask"]))

        hora = datetime.now().strftime("%H:%M:%S")
        mensaje = f"*📊 Cotizaciones – {hora}*\n\n"
        for item in objetivos_ordenados:
            nombre = item.get("prettyName", item["name"])
            ask = item.get("ask", "N/D")
            url = item.get("url", "")
            mensaje += f"*{nombre}*: ${ask}\n{url}\n\n"

        enviar_mensaje(chat_id, mensaje)
    except Exception as e:
        error_msg = f"❌ Error al obtener cotizaciones:\n{e}"
        print(error_msg)
        enviar_mensaje(chat_id, error_msg)

if __name__ == '__main__':
    print("🔄 Bot iniciado a las", datetime.now().strftime("%H:%M:%S"))
    app.run(host="0.0.0.0", port=8080)
