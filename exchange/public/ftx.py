from events import EventManager
from exchange.public import ExchangePublic


class FTX(ExchangePublic):
    def __init__(self, conf=None):
        exchange_id = 'ftx'
        super().__init__(exchange_id, conf)
        self.em.modify_mailbox_size(exchange_id, 7)


if __name__ == "__main__":
    b = FTX()
    b.listen()
