import io
import json
import threading
import time
from datetime import datetime

import avro
import events
import pytz
from confluent_kafka import Producer
from elasticsearch import Elasticsearch
from eslogger import Logger
from schemas.recorder import RecorderSchema


class ElasticRecorder:
    def __init__(self):
        self.address = "recorder"
        self.es = Elasticsearch(hosts='10.0.0.124', port=9200)
        self.log = Logger(self.__class__.__name__)
        self.em = events.EventManager()
        self.em.create_address(self.address)
        self.em.modify_mailbox_size(self.address, 2)

    def record(self, data):
        body = {"timestamp":  datetime.fromtimestamp(data['timestamp']).astimezone(pytz.UTC),
                "type": data['type']}
        for name in data['data']:
            body[name] = json.dumps(data['data'][name])

        self.es.index(index=data['search_index'], document=body)

    def on(self, data):
        self.record(data)

    def listen(self):
        self.em.wait_for_command(self.address, RecorderSchema, on=self.on)


if __name__ == "__main__":
    er = ElasticRecorder()
    er.listen()

    # threading.Thread(target=er.listen).start()
    #
    # bids = [[0.0012, 1.5], [0.001245, 1.6], [0.001246, 0.9]]
    # asks = [[0.00126, 1.3], [0.001255, 0.6], [0.001266, 0.7]]
    # pair = "BTC/USD"
    #
    # record_schema = avro.schema.parse(RecorderSchema)
    # conf = {'bootstrap.servers': "127.0.0.1:9092"}
    #
    # producer = Producer(**conf)
    # writer = avro.io.DatumWriter(RecorderSchema)
    # bytes_writer = io.BytesIO()
    # encoder = avro.io.BinaryEncoder(bytes_writer)
    # writer.write({
    #     "timestamp": int(datetime.timestamp(datetime.now())),
    #     "type": "order_book",
    #     "search_index": "delete_me",
    #     "data": {"pair": pair, "bids": bids, "asks": asks}
    # }, encoder)
    # raw_bytes = bytes_writer.getvalue()
    # producer.produce("recorder", raw_bytes)
    #
    # bytes_writer = io.BytesIO()
    # encoder = avro.io.BinaryEncoder(bytes_writer)
    # writer.write({
    #     "timestamp": int(datetime.timestamp(datetime.now())),
    #     "type": "ticker",
    #     "search_index": "delete_me",
    #     "data": {"pair": "BTC/USD", "price": 43023.78, "volume": 120}
    # }, encoder)
    # raw_bytes = bytes_writer.getvalue()
    # producer.produce("recorder", raw_bytes)
    #
    # producer.flush()
    #
    # time.sleep(100)




