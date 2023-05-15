from random import randint
from typing import Set, Any

from aiohttp.web_middlewares import middleware
from kafka import TopicPartition
from fastapi import FastAPI, File, UploadFile
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.cors import CORSMiddleware

import uuid
import core.detection
import uvicorn
import aiokafka
import asyncio
import aioredis
import json
import logging
import os

# instantiate the API
app = FastAPI()

# init middleware
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# global variables
consumer_task = None
consumer = None
redis = None
status_ready = 'READY'

# env variables
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'detections')
KAFKA_CONSUMER_GROUP_PREFIX = os.getenv('KAFKA_CONSUMER_GROUP_PREFIX', 'group')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:29092')
IMAGE_DIR = "../files/"

# initialize logger
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
log = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    log.info('Initializing API ...')
    await initialize()
    await consume()


@app.on_event("shutdown")
async def shutdown_event():
    log.info('Shutting down API')
    consumer_task.cancel()
    await consumer.stop()


@app.get("/")
async def root():
    return {"message": "Recycle v0.0.1"}


@app.get("/detections/{detection_id}")
async def getDetection(detection_id):
    try:
        is_exist = await redis.exists(detection_id)

        if is_exist:
            value = await redis.get(detection_id)
            return json.loads(value)
        else:
            return {"status": "NOT_FOUND"}

    except RuntimeError:
        log.error(f"getDetection exc: {value}")

@app.post("/detections")
async def create_detection(file: UploadFile = File(...)):
    file.filename = f"{uuid.uuid4()}.jpg"
    contents = await file.read()
    image_path = f"{IMAGE_DIR}{file.filename}"

    with open(image_path, "wb") as f:
        f.write(contents)

    result = await core.detection.detect_from_image(image_path)

    return {"detectionId": file.filename, "result": result}


async def initialize():
    loop = asyncio.get_event_loop()

    # init redis
    global redis
    redis = await aioredis.create_redis(address=('localhost', 6379), password='qwerty')

    global consumer
    group_id = f'{KAFKA_CONSUMER_GROUP_PREFIX}-{randint(0, 10000)}'
    log.debug(f'Initializing KafkaConsumer for topic {KAFKA_TOPIC}, group_id {group_id}'
              f' and using bootstrap servers {KAFKA_BOOTSTRAP_SERVERS}')
    consumer = aiokafka.AIOKafkaConsumer(KAFKA_TOPIC, loop=loop,
                                         bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                                         group_id=group_id)
    await consumer.start()

    partitions: Set[TopicPartition] = consumer.assignment()
    nr_partitions = len(partitions)
    if nr_partitions != 1:
        log.warning(f'Found {nr_partitions} partitions for topic {KAFKA_TOPIC}. Expecting '
                    f'only one, remaining partitions will be ignored!')
    for tp in partitions:
        # get the log_end_offset
        end_offset_dict = await consumer.end_offsets([tp])
        end_offset = end_offset_dict[tp]

        if end_offset == 0:
            log.warning(f'Topic ({KAFKA_TOPIC}) has no messages (log_end_offset: '
                        f'{end_offset}), skipping initialization ...')
            return

        log.debug(f'Found log_end_offset: {end_offset} seeking to {end_offset - 1}')
        consumer.seek(tp, end_offset - 1)
        msg = await consumer.getone()
        log.info(f'Initializing API with data from msg: {msg}')

        # process recycle detection
        await process_detection(msg)
        return


async def consume():
    global consumer_task
    consumer_task = asyncio.create_task(send_consumer_message(consumer))


async def send_consumer_message(consumer):
    try:
        async for msg in consumer:
            # x = json.loads(msg.value)
            log.info(f"Consumed msg: {msg}")

            await process_detection(msg)
    finally:
        log.warning('Stopping consumer')
        await consumer.stop()


async def process_detection(message: Any) -> None:
    result = None
    value = json.loads(message.value)

    if 'detection_id' not in value:
        log.error(f"process_detection: detection id was empty: {value}")
        return

    try:
        result = await core.detection.detect_from_image(value['image_path'])
    except RuntimeError:
        log.error(f"process_detection value was empty: {value}")

    # set status of recycle detection
    result['status'] = status_ready
    dump = json.dumps(result)

    try:
        await redis.set(value['detection_id'], dump, expire=3600)
    except RuntimeError:
        log.error(f"process_detection redis exc: {value}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)


Instrumentator().instrument(app).expose(app)
