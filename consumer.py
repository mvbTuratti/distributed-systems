#!/usr/bin/env python
import pika, sys, os
from requests import Session
from json import loads

def main():
    base_url = "http://localhost:8000/message/"
    session = Session()
    session.headers.update({"Content-Type": "application/json"})
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='messages')

    def callback(ch, method, properties, body):
        print(body)
        payload = loads(body.decode('utf-8'))
        session.post(url=base_url,json=payload)

    channel.basic_consume(queue='messages', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)