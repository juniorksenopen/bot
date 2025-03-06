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
USER_ID = "U08GCDNPAC9"  # Tu ID de usuario de Slack

# Cliente de Slack
client = WebClient(token=SLACK_BOT_TOKEN)

# Zona horaria de Colombia
COL_TIMEZONE = pytz.timezone("America/Bogota")

# Horario fuera de oficina
HORA_INICIO = 14  # 2 PM en Colombia
HORA_FIN = 9  # 9 AM en Colombia

# Diccionario para almacenar últimas respuestas por canal
ultimas_respuestas = {}
TIEMPO_ESPERA = 600  # 10 minutos en segundos

def fuera_de_horario():
    """Verifica si la hora actual en Colombia está fuera del horario laboral."""
    hora_actual = datetime.now(COL_TIMEZONE).hour
    return hora_actual >= HORA_INICIO or hora_actual < HORA_FIN

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json
    logging.info(f"Evento recibido: {data}")

    # Responder al desafío de verificación de Slack
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Verificar si es un evento
    event = data.get("event", {})
    
    # Responder a diferentes tipos de eventos que podrían mencionar al usuario
    if event.get("type") == "message" and "subtype" not in event:
        process_message_event(event)
    elif event.get("type") == "app_mention":
        process_app_mention_event(event)

    return jsonify({"status": "OK"}), 200

def process_message_event(event):
    channel = event.get("channel")
    user_id = event.get("user")
    text = event.get("text", "").lower()
    
    # No responder a mensajes enviados por el bot
    if user_id == "USLACKBOT" or user_id == client.auth_test()["user_id"]:
        return
    
    # Verificar si el mensaje menciona al usuario o es un DM
    channel_type = event.get("channel_type")
    is_mention = f"<@{USER_ID}>" in text
    is_dm = channel_type == "im"
    
    if (is_mention or is_dm) and should_respond(channel):
        if fuera_de_horario():
            try:
                client.chat_postMessage(
                    channel=channel,
                    text=f"Hola <@{user_id}>, gracias por tu mensaje para <@{USER_ID}>. Actualmente está fuera de horario laboral, pero responderá en cuanto esté disponible. 😊"
                )
                # Registrar la respuesta
                ultimas_respuestas[channel] = time.time()
            except SlackApiError as e:
                logging.error(f"Error al enviar mensaje: {e.response['error']}")

def process_app_mention_event(event):
    channel = event.get("channel")
    user_id = event.get("user")
    
    if should_respond(channel):
        if fuera_de_horario():
            try:
                client.chat_postMessage(
                    channel=channel,
                    text=f"Hola <@{user_id}>, gracias por tu mensaje. <@{USER_ID}> está fuera de horario laboral en este momento, pero responderá en cuanto esté disponible. 😊"
                )
                # Registrar la respuesta
                ultimas_respuestas[channel] = time.time()
            except SlackApiError as e:
                logging.error(f"Error al enviar mensaje: {e.response['error']}")

def should_respond(channel):
    """Determina si debemos responder basado en el tiempo transcurrido desde la última respuesta."""
    tiempo_actual = time.time()
    if channel in ultimas_respuestas and (tiempo_actual - ultimas_respuestas[channel]) < TIEMPO_ESPERA:
        return False
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", 3000))  
    app.run(host="0.0.0.0", port=port)
