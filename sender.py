#!/usr/bin/env python
import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='messages')

channel.basic_publish(exchange='', routing_key='messages', 
                      body=json.dumps({"name":"Admin", "content": "admin test", "hash": "123", 
                                              "timestamp": "11/11/11 11:11:11"}))
print(" [x] Sent 'Hello World!'")

connection.close()