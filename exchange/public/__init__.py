import datetime
import time
import events
from eslogger import Logger
from exchange import Exchange
from schemas.globalmarket import GlobalMarketCommandSchema
from schemas.recorder import RecorderSchema


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
        self.em = events.EventManager()

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
            self.em.send_command_to_address('recorder', RecorderSchema, {
                "timestamp": int(datetime.datetime.timestamp(datetime.datetime.now())),
                "type": "ticker",
                "search_index": "global-data",
                "data": {
                    "pair": ticker['symbol'],
                    "exchange": self.exchange_id,
                    "high": ticker['high'],
                    "low": ticker['low'],
                    "bid": ticker['bid'],
                    "bidVolume": ticker['bidVolume'],
                    "ask": ticker['ask'],
                    "askVolume": ticker['askVolume'],
                    "open": ticker['open'],
                    "close": ticker['close'],
                    "last": ticker['last'],
                    "baseVolume": ticker['baseVolume'],
                    "quoteVolume": ticker['quoteVolume']
                }
            })
        elif command['command'] == "OrderBook":
            self.log.info(f"Got order book command for pair {command['pair']}")
            ob = self.get_order_book(command['pair'])
            self.em.send_command_to_address('recorder', RecorderSchema, {
                "timestamp": int(datetime.datetime.timestamp(datetime.datetime.now())),
                "type": "order_book",
                "search_index": "global-data",
                "data": {"pair": ob['symbol'], "exchange": self.exchange_id, "bids": ob['bids'], "asks": ob['asks']}
            })
        else:
            self.log.error(f"Unknown command {command['command']}")

    def listen(self):
        self.em.wait_for_command(f"{self.exchange_id}", GlobalMarketCommandSchema, on=self.on)


if __name__ == "__main__":
    # e = ExchangePublic('bittrex')
    pass
