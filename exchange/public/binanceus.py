import time

from exchange.public import ExchangePublic
from events import EventManager


class BinanceUS(ExchangePublic):
    def __init__(self, conf=None):
        exchange_id = 'binanceus'
        super().__init__(exchange_id, conf)
        EventManager().modify_mailbox_size(exchange_id, 5)


if __name__ == "__main__":
    b = BinanceUS()
    b.listen()
