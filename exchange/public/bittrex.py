from exchange.public import ExchangePublic


class Bittrex(ExchangePublic):
    def __init__(self, conf=None):
        super().__init__('bittrex', conf)


if __name__ == "__main__":
    b = Bittrex()
    b.listen()