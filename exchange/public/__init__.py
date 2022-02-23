import datetime
import time

from eslogger import Logger

from exchange import Exchange

schema_str = """
{
        "namespace": "confluent.io.examples.serialization.avro",
        "name": "CBPCommand",
        "type": "record",
        "fields": [   
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},         
            {"name": "pair", "type": "string"},
            {"name": "command", "type": {
                    "type": "enum",
                    "name": "Command",
                    "symbols": ["Tick", "OrderBook"]
                }
            }
        ]
}
"""


class ExchangePublic(Exchange):
    def __init__(self, exchange_id, conf=None):
        super().__init__(exchange_id, conf)
        self.client.load_markets()
        time.sleep(2)
        self.fees = {
            "trading": {
                "taker": self.client.fees['trading']['taker'],
                "maker": self.client.fees['trading']['maker']
            }
        }
        self.rate = self.client.rateLimit
        self.log = Logger(exchange_id)

    def get_symbols(self):
        return self.client.symbols

    def get_currencies(self):
        return self.client.currencies

    def get_order_book(self, pair):
        return self.client.fetch_order_book(pair)

    def get_ticker(self, pair):
        return self.client.fetch_ticker(pair)

    def on(self, command):
        if datetime.datetime.timestamp(datetime.datetime.now()) - command['timestamp'] >= 10:
            self.log.warning(f"Skip old command timestamp {command['timestamp']}")
            return
        if command['command'] == "Tick":
            self.log.info(f"Got ticker command for pair {command['pair']}")
            ticker = self.get_ticker(command['pair'])
            print(ticker)
        elif command['command'] == "OrderBook":
            self.log.info(f"Got order book command for pair {command['pair']}")
            ob = self.get_order_book(command['pair'])
            print(ob)
        else:
            self.log.error(f"Unknown command {command['command']}")

    def listen(self):
        self.em.wait_for_command(f"{self.exchange_id}", schema_str, on=self.on)


if __name__ == "__main__":
    e = ExchangePublic('bittrex')
