import os
import logging
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import pytz  # Importar para manejar zonas horarias

# Configurar Flask
app = Flask(__name__)

# Variables de entorno (Render)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Cliente de Slack
client = WebClient(token=SLACK_BOT_TOKEN)

# Zona horaria de Colombia
COL_TIMEZONE = pytz.timezone("America/Bogota")

# Horario fuera de oficina
HORA_INICIO = 14  # 2 PM en Colombia
HORA_FIN = 9  # 9 AM en Colombia

def fuera_de_horario():
    """Verifica si la hora actual en Colombia está fuera del horario laboral."""
    hora_actual = datetime.now(COL_TIMEZONE).hour
    return hora_actual >= HORA_INICIO or hora_actual < HORA_FIN

@app.route("/")
def home():
    return "El bot de Slack está funcionando correctamente."

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json

    # Responder al desafío de verificación de Slack
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Verificar si es un mensaje directo
    event = data.get("event", {})
    if event.get("type") == "message" and "subtype" not in event:
        user_id = event.get("user")
        channel = event.get("channel")
        
        # Responder solo si es fuera de horario
        if fuera_de_horario():
            try:
                client.chat_postMessage(
                    channel=channel,
                    text=f"Hola <@{user_id}>, ahora mismo no estoy disponible. Responderé en horario laboral. 😊"
                )
            except SlackApiError as e:
                logging.error(f"Error al enviar mensaje: {e.response['error']}")

    return jsonify({"status": "OK"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))  # Render asigna el puerto dinámicamente
    app.run(host="0.0.0.0", port=port)
