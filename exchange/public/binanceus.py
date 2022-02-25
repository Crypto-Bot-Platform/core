from exchange.public import ExchangePublic


class BinanceUS(ExchangePublic):
    def __init__(self, conf=None):
        super().__init__('binanceus', conf)


if __name__ == "__main__":
    b = BinanceUS()
    b.listen()
