import time

import ccxt
import events
from os import environ

class Exchange:
    def __init__(self, exchange_id: str, config=None):
        kafka_host = environ['KAFKA_HOST']
        kafka_port = environ['KAFKA_PORT']
        print(f"*** Environment variables: KAFKA_HOST={kafka_host}, KAFKA_PORT={kafka_port}")
        self.exchange_id = exchange_id
        exchange_class = getattr(ccxt, exchange_id)
        if config is not None:
            self.client = exchange_class(config)
        self.client = exchange_class()

        self.em = events.EventManager(host=kafka_host, port=int(kafka_port))
        # self.em.delete_address(f"{exchange_id}")
        self.em.create_address(f"{exchange_id}")

    def __del__(self):
        self.em.delete_address(f"{self.exchange_id}")

    def get_name(self):
        return self.exchange_id
