import datetime
import threading
import time
from eslogger import Logger
from pymongo import MongoClient
import events
from schemas.globalmarket import GlobalMarketCommandSchema

log = Logger("global-market")

db_client = MongoClient()
config = db_client.cbp.config.find_one({"_id": "global-market"}, {"crypto.bases": 1, "crypto.coins": 1})
bases = config['crypto']['bases']
coins = config['crypto']['coins']


def filter_pairs(pairs):
    result = []
    for pair in pairs:
        if '/' not in pair:
            continue
        [coin, base] = pair.split('/')
        if coin in coins and base in bases:
            result.append(pair)
    return result


exchanges = []
for exchange in db_client.cbp.exchanges.find():
    exchanges.append({
        "id":       exchange['_id'],
        "pairs":    filter_pairs(exchange['symbols']),
        "rate":     exchange['rateLimit']
    })


def pulse_commands(exchange):
    try:
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
    except Exception as e:
        log.error(f"Error while sending commands to {exchange['id']}. [{e}]")


for exchange in exchanges:
    log.info(f"Start sending command to exchange {exchange['id']}")
    x = threading.Thread(target=pulse_commands, args=(exchange,))
    x.start()
