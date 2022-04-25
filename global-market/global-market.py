import datetime
import threading
import time
from eslogger import Logger
from pymongo import MongoClient
import events
from schemas.globalmarket import GlobalMarketCommandSchema
from os import environ

kafka_host = environ['KAFKA_HOST']
kafka_port = environ['KAFKA_PORT']
mongo_host = environ['MONGODB_HOST']
mongo_port = environ['MONGODB_PORT']
elastic_host = environ['ELASTIC_HOST']
elastic_port = environ['ELASTIC_PORT']
print(f"*** Environment variables: KAFKA_HOST={kafka_host}, KAFKA_PORT={kafka_port}, "
      f"MONGODB_HOST={mongo_host}, MONGODB_PORT={mongo_port}, ELASTIC_HOST={elastic_host}, "
      f"ELASTIC_PORT={elastic_port}")

log = Logger("global-market", host=elastic_host, port=int(elastic_port))

db_client = MongoClient(host=mongo_host, port=int(mongo_port))
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
        "id": exchange['_id'],
        "pairs": filter_pairs(exchange['symbols']),
        "rate": exchange['rateLimit']
    })


def pulse_commands(exchange):
    try:
        time.sleep(40)
        counter = 0
        total_pairs = len(exchange['pairs'])
        em = events.EventManager(host=kafka_host, port=int(kafka_port))
        while True:
            pair = exchange['pairs'][counter % total_pairs]
            em.send_command_to_address(exchange['id'], GlobalMarketCommandSchema, {
                "timestamp": int(datetime.datetime.timestamp(datetime.datetime.now())),
                "pair": pair,
                "command": "Tick"
            })
            counter += 1
            request_rate = exchange['rate'] / 1000 if exchange['rate'] >= 1000 else exchange['rate'] * 2 / 1000
            time.sleep(request_rate)
    except Exception as e:
        log.error(f"Error while sending commands to {exchange['id']}. [{e}]")


for exchange in exchanges:
    log.info(f"Start sending command to exchange {exchange['id']}")
    x = threading.Thread(target=pulse_commands, args=(exchange,))
    x.start()
