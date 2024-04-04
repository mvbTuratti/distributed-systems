from fastapi import FastAPI, Request, WebSocket
import aio_pika
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
from json import dumps
import pika
import uvicorn

from datetime import datetime
import random

def generate_funny_name(): 
    adjectives = ["adorable", "bubbly", "crazy", "dizzy", "energetic", "fluffy", "giggly", "happy", "jolly", "kooky", "loopy", "merry", "nutty", "playful", "quirky", "silly", "twinkly", "wacky", "zany"]
    nouns = ["apple", "banana", "cookie", "donut", "elephant", "flamingo", "giraffe", "hedgehog", "iguana", "jellyfish", "koala", "lemur", "monkey", "narwhal", "octopus", "penguin", "quokka", "rhinoceros", "sloth", "toucan", "unicorn", "vampire", "walrus", "x-ray fish", "yeti", "zebra"]
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    separator = random.choice(["-", "_", " ", ""])
    funny_name = f"{adjective}{separator}{noun} Python"

    return funny_name

RABBITMQ_HOST = "localhost"
MESSAGE_QUEUE = "messages"


app = FastAPI()

app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=MESSAGE_QUEUE)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.sockets: dict[str, WebSocket] = {}
        self.messages: list[dict] = []

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.sockets[client_id] = websocket
    def disconnect(self, websocket: WebSocket, client_id: str):
        self.active_connections.remove(websocket)
        del self.sockets[client_id]
    def get_websocket_for_connection(self, client_id: str):
        return self.sockets[client_id]
    async def send_message_to_socket(self, user_id, message):
        await self.get_websocket_for_connection(user_id).send_text(message)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
    async def add_message(self, msg):
        if len(self.messages) < 30: return self.messages.append(msg)
        self.messages = [m for m in self.messages[1:]].append(msg)

manager = ConnectionManager()

async def run_listener_loop():
    connection = await aio_pika.connect(host=RABBITMQ_HOST)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    queue = await channel.declare_queue(MESSAGE_QUEUE)

    async def callback(message):
        async with message.process():
            payload = message.body.decode('utf-8')
            await manager.add_message(payload)
            await manager.broadcast(payload)

    await queue.consume(callback)

task = asyncio.create_task(run_listener_loop())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = generate_funny_name()
    print(f"{connection_id} joined!")
    await manager.connect(websocket, connection_id)
    await websocket.send_text(connection_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f'received message from websocket: {data}')
            [hash, content] = data.split(" - ", 1)
            channel.basic_publish(exchange='', routing_key=MESSAGE_QUEUE, 
                                  body=dumps({"name":connection_id, "content": content, "hash": hash, 
                                              "timestamp": datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}))
    except:
        print("client disconnected!")
    finally:
        print(f"removing client {connection_id}")
        manager.disconnect(websocket, connection_id)


@app.get("/", response_class=HTMLResponse )
async def return_app(request: Request):
    return HTMLResponse(content=open("static/index.html", "r").read())

@app.get("/messages/")
async def return_messages():
    return JSONResponse(content={"messages": manager.messages})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)