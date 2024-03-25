from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio  # Import asyncio for task creation
import pika

RABBITMQ_HOST = "localhost"
MESSAGE_QUEUE = "messages"


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

global websocket
websocket = None

async def callback(ch, method, properties, body):
    global websocket
    await websocket.send_text(body.decode())
    ch.basic_ack(delivery_tag=method.delivery_tag)


async def listen_to_events():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()

        channel.queue_declare(queue=MESSAGE_QUEUE)
        channel.basic_consume(queue=MESSAGE_QUEUE, on_message_callback=callback, auto_ack=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()
    except:
        print("consumer error!")


@app.websocket("/ws")
async def handle_websocket(webs: WebSocket):
    websocket = webs  # Store the connected websocket

    # Start listening to events in a separate task
    await asyncio.create_task(listen_to_events())

    async for message in websocket.receive_text():
        connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()

        channel.queue_declare(queue=MESSAGE_QUEUE)

        channel.basic_publish(exchange='', routing_key=MESSAGE_QUEUE, body=message)
        print(" [x] Sent 'Hello World!'")
        connection.close()

    await websocket.accept()

@app.get("/", response_class=HTMLResponse)
async def return_app(request: Request):
    # Assuming index.html is in the static directory
    return HTMLResponse(content=open("static/index.html", "r").read())

