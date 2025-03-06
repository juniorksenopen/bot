import os
import logging
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime

# Configurar Flask
app = Flask(__name__)

# Variables de entorno (Railway)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Cliente de Slack
client = WebClient(token=SLACK_BOT_TOKEN)

# Horario fuera de oficina
HORA_INICIO = 18  # 6 PM
HORA_FIN = 9  # 9 AM

def fuera_de_horario():
    hora_actual = datetime.now().hour
    return hora_actual >= HORA_INICIO or hora_actual < HORA_FIN

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
    app.run(host="0.0.0.0", port=3000)
