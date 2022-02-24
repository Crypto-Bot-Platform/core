import datetime
import threading
import time
from exchange.public.bittrex import Bittrex
import events
from schemas.globalmarket import GlobalMarketCommandSchema

# TODO: Read this from config file
bases = ['BTC', 'USD', 'ETH', 'USDT', 'USDC']
coins = ['BTC', 'ETH', 'USDT', 'USDC', 'BNB', 'ADA', 'SOL', 'XRP', 'LUNA', 'DOT', 'DODGE', 'AVAX', 'BUSD', 'MATIC',
         'SHIB', 'UST', 'BCH', 'RVN', 'IOTX']


def filter_pairs(pairs):
    result = []
    for pair in pairs:
        if '/' not in pair:
            continue
        [coin, base] = pair.split('/')
        if coin in coins and base in bases:
            result.append(pair)
    return result


# TODO: Get exchanges from DB
bittrex = Bittrex()
exchanges = [{
    "id": "bittrex",
    "pairs": filter_pairs(bittrex.get_symbols()),
    "rate": bittrex.rate
}]


def pulse_commands(exchange):
    counter = 0
    total_pairs = len(exchange['pairs'])
    em = events.EventManager()
    while True:
        pair = exchange['pairs'][counter % total_pairs]
        em.send_command_to_address(exchange['id'], GlobalMarketCommandSchema, {
            "timestamp": int(datetime.datetime.timestamp(datetime.datetime.now())),
            "pair": pair,
            "command": "Tick"
        })
        counter += 1
        time.sleep(exchange['rate'] / 1000)


for exchange in exchanges:
    x = threading.Thread(target=pulse_commands, args=(exchange,))
    x.start()
