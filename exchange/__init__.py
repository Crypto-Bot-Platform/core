import time

import ccxt
import events


class Exchange:
    def __init__(self, exchange_id: str, config=None):
        self.exchange_id = exchange_id
        exchange_class = getattr(ccxt, exchange_id)
        if config is not None:
            self.client = exchange_class(config)
        self.client = exchange_class()

        self.em = events.EventManager()
        self.em.delete_address(f"{exchange_id}")
        self.em.create_address(f"{exchange_id}")

    def __del__(self):
        self.em.delete_address(f"{self.exchange_id}")

    def get_name(self):
        return self.exchange_id
