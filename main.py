import os
import logging
import time
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import pytz  

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

# Diccionario para almacenar últimas respuestas por usuario
ultimas_respuestas = {}
TIEMPO_ESPERA = 600  # 10 minutos en segundos

def fuera_de_horario():
    """Verifica si la hora actual en Colombia está fuera del horario laboral."""
    hora_actual = datetime.now(COL_TIMEZONE).hour
    return hora_actual >= HORA_INICIO or hora_actual < HORA_FIN

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json

    # Responder al desafío de verificación de Slack
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Verificar si es un mensaje de usuario
    event = data.get("event", {})
    if event.get("type") == "message" and "subtype" not in event:
        user_id = event.get("user")
        channel = event.get("channel")
        channel_type = event.get("channel_type")  # Detecta si es un DM

        # Evitar responder al mismo usuario varias veces en poco tiempo
        tiempo_actual = time.time()
        if user_id in ultimas_respuestas and (tiempo_actual - ultimas_respuestas[user_id]) < TIEMPO_ESPERA:
            return jsonify({"status": "OK"}), 200

        # Guardar el tiempo de respuesta
        ultimas_respuestas[user_id] = tiempo_actual

        # Responder si es un DM o fuera de horario en canales
        if channel_type == "im" or fuera_de_horario():
            try:
                client.chat_postMessage(
                    channel=channel,
                    text=f"Hola <@{user_id}>, ahora mismo no estoy disponible. Responderé en horario laboral. 😊"
                )
            except SlackApiError as e:
                logging.error(f"Error al enviar mensaje: {e.response['error']}")

    return jsonify({"status": "OK"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))  
    app.run(host="0.0.0.0", port=port)
