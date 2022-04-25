import time

import ccxt
import events
from os import environ

class Exchange:
    def __init__(self, exchange_id: str, config=None):
        elastic_host = environ['ELASTIC_HOST']
        elastic_port = environ['ELASTIC_PORT']
        print(f"*** Environment variables: ELASTIC_HOST={elastic_host}, ELASTIC_PORT={elastic_port}")
        self.exchange_id = exchange_id
        exchange_class = getattr(ccxt, exchange_id)
        if config is not None:
            self.client = exchange_class(config)
        self.client = exchange_class()

        self.em = events.EventManager(host=elastic_host, port=int(elastic_port))
        # self.em.delete_address(f"{exchange_id}")
        self.em.create_address(f"{exchange_id}")

    def __del__(self):
        self.em.delete_address(f"{self.exchange_id}")

    def get_name(self):
        return self.exchange_id
