import os
import threading
import time
from datetime import datetime

import events
import psycopg2
from eslogger import Logger
from os import environ
from schemas.recorder import RecorderSchema


class TimescaleRecorder:
    def __init__(self):
        kafka_host = environ['KAFKA_HOST']
        kafka_port = environ['KAFKA_PORT']
        elastic_host = environ['ELASTIC_HOST']
        elastic_port = environ['ELASTIC_PORT']
        db_name = environ['SQLDB_NAME']
        db_user = environ['SQLDB_USER']
        db_pass = environ['SQLDB_PASS']
        db_host = environ['SQLDB_HOST']
        db_port = int(environ['SQLDB_PORT'])
        print(f"*** Environment variables: KAFKA_HOST={kafka_host}, KAFKA_PORT={kafka_port}, "
              f"ELASTIC_HOST={elastic_host}, ELASTIC_PORT={elastic_port}, SQLDB_HOST={db_host}, "
              f"SQLDB_PORT={db_port}, SQLDB_NAME = {db_name}, SQLDB_USER={db_user}, SQLDB_PASS={db_pass}")

        self.log = Logger(self.__class__.__name__, host=elastic_host, port=int(elastic_port))
        self.address = "db-recorder"
        self.em = events.EventManager(host=kafka_host, port=int(kafka_port))
        self.em.create_address(self.address)
        self.em.modify_mailbox_size(self.address, 5)
        self.conn = psycopg2.connect(f"postgres://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}")
        self.init_db()

    def init_db(self):
        fd = open('recorder/bootstrap/init_db.sql', 'r')
        sql_content = fd.read()
        sql_content = sql_content.strip()
        fd.close()

        c = self.conn.cursor()
        sql_commands = sql_content.split(';')
        for command in sql_commands:
            try:
                if len(command.strip()) > 0:
                    self.log.info(command.strip())
                    c.execute(command.strip() + ';')
            except Exception as msg:
                self.log.error(f"Command skipped: {msg}")
        self.conn.commit()
        c.close()

    def record(self, data):
        c = self.conn.cursor()
        try:
            if data['type'] == 'ticker':
                c.execute("""
                INSERT INTO ticks 
                    (time, exchange, pair, opening_price, highest_price,   
                     lowest_price, closing_price, volume_base, volume_coin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);""", (
                          str(datetime.fromtimestamp(data['timestamp'] / 1000, datetime.now().astimezone().tzinfo)),
                          data['data']['exchange'],
                          data['data']['pair'],
                          data['data']['open'],
                          data['data']['high'],
                          data['data']['low'],
                          data['data']['close'],
                          data['data']['baseVolume'],
                          data['data']['quoteVolume']))
            elif data['type'] == 'indicator':
                c.execute("""
                INSERT INTO indicators
                (time, exchange, pair, name, value1, value2, value3, value4)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""", (
                    str(datetime.fromtimestamp(data['timestamp'] / 1000, datetime.now().astimezone().tzinfo)),
                    data['data']['exchange'],
                    data['data']['pair'],
                    data['data']['name'],
                    data['data']['value1'],
                    data['data']['value2'],
                    data['data']['value3'],
                    data['data']['value4']
                ))
            else:
                self.log.error(f"Got unknown request {data['type']}")
        except (Exception, psycopg2.Error) as error:
            self.log.error(error.pgerror)
        self.conn.commit()

    def on(self, data):
        self.record(data)

    def listen(self):
        self.em.wait_for_command(self.address, RecorderSchema, on=self.on)


if __name__ == "__main__":
    t = TimescaleRecorder()
    #t.listen()

    threading.Thread(target=t.listen).start()

    pair = "BTC/USD"

    em = events.EventManager()
    em.send_command_to_address("db-recorder", RecorderSchema, {
        "timestamp": int(time.time() * 1000),
        "type": "ticker",
        "search_index": "delete_me",
        "data": {
            "pair": pair,
            "exchange": "ftx",
            "high": 34501,
            "low": 34451,
            "bid": 34456.5555,
            "bidVolume": 345621234,
            "ask": 34458.567,
            "askVolume": 32123478,
            "open": 34456,
            "close": 34557,
            "last": 34501.786,
            "baseVolume": 98787665,
            "quoteVolume": 766537865
        }
    })

    em.send_command_to_address("db-recorder", RecorderSchema, {
        "timestamp": int(time.time() * 1000),
        "type": "indicator",
        "data": {
            "pair": pair,
            "exchange": "ftx_not_real",
            "name": "RSI",
            "value1": 56.89
        }
    })

    time.sleep(100)
