from aiokafka import AIOKafkaProducer
import asyncio
import json
import os
from random import randint

# env variables
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'detections')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:29092')

# global variables
loop = asyncio.get_event_loop()


async def send_one():
    producer = AIOKafkaProducer(loop=loop, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        # produce message
        msg_id = f'{randint(1, 10000)}'
        # value = {'message_id': msg_id, 'text': 'some text', 'state': randint(1, 100)}
        value = {'message_id': msg_id, 'detection_id': '123',
                 'image_path': '../files/f8e1ee7e-30fa-47f6-bf74-407e352c9739.jpg'}
        print(f'Sending message with value: {value}')
        value_json = json.dumps(value).encode('utf-8')
        await producer.send_and_wait(KAFKA_TOPIC, value_json)
    finally:
        await producer.stop()


# send message
loop.run_until_complete(send_one())
