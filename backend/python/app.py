from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from json import dumps, loads
import pika
import uvicorn

import random

def generate_funny_name(): 
    adjectives = ["adorable", "bubbly", "crazy", "dizzy", "energetic", "fluffy", "giggly", "happy", "jolly", "kooky", "loopy", "merry", "nutty", "playful", "quirky", "silly", "twinkly", "wacky", "zany"]
    nouns = ["apple", "banana", "cookie", "donut", "elephant", "flamingo", "giraffe", "hedgehog", "iguana", "jellyfish", "koala", "lemur", "monkey", "narwhal", "octopus", "penguin", "quokka", "rhinoceros", "sloth", "toucan", "unicorn", "vampire", "walrus", "x-ray fish", "yeti", "zebra"]

    # Generate a funny name by combining a random adjective and noun
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    separator = random.choice(["-", "_", " ", ""])
    funny_name = f"{adjective}{separator}{noun}"

    return funny_name

RABBITMQ_HOST = "localhost"
MESSAGE_QUEUE = "messages"


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=MESSAGE_QUEUE)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.sockets: dict[str, WebSocket] = {}

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

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = generate_funny_name()
    print(f"{connection_id} joined!")
    await manager.connect(websocket, connection_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f'received message from websocket: {data}')
            [hash, content] = data.split(" - ", 1)
            channel.basic_publish(exchange='', routing_key=MESSAGE_QUEUE, body=dumps({"name":connection_id, "content": content, "hash": hash}))
    except:
        manager.disconnect(websocket, connection_id)

class Message(BaseModel):
    name:str
    content: str
    hash: str

@app.post("/message/")
async def broadcast_message(body: Message):
    print(body)
    await manager.broadcast(dumps({"n": body.name, "c": body.content, "h": body.hash}))
    return {"status":"sent"}

@app.get("/", response_class=HTMLResponse )
async def return_app(request: Request):
    return HTMLResponse(content=open("static/index.html", "r").read())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)