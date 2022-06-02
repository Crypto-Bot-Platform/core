import math
import threading
import time
from datetime import datetime
from typing import Optional

import events
import psycopg2
from eslogger import Logger
from os import environ

from pandas import DataFrame

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
        # Start dimensions update
        ttd = TickerTimeDimension()
        ttd.start()

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


# Creates and populates time "dimension" tables for "fact" table - `ticker`
class TickerTimeDimension:
    def __init__(self):
        elastic_host = environ['ELASTIC_HOST']
        elastic_port = environ['ELASTIC_PORT']
        db_name = environ['SQLDB_NAME']
        db_user = environ['SQLDB_USER']
        db_pass = environ['SQLDB_PASS']
        db_host = environ['SQLDB_HOST']
        db_port = int(environ['SQLDB_PORT'])
        self.log = Logger(self.__class__.__name__, host=elastic_host, port=int(elastic_port))
        self.conn = psycopg2.connect(f"postgres://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}")
        self.minutes = [1, 5, 10, 30, 60]
        [self.create_table_for_period(i) for i in self.minutes]

    def create_table_for_period(self, period: int):
        c = self.conn.cursor()
        try:
            c.execute(f"""
            CREATE TABLE IF NOT EXISTS "public".ticks_{period} ( time TIMESTAMPTZ,
                exchange varchar NOT NULL ,
                pair varchar NOT NULL ,
                opening_price double PRECISION NULL ,
                highest_price double PRECISION NULL ,
                lowest_price double PRECISION NULL ,
                closing_price double PRECISION NULL ,
                volume_base double PRECISION NULL ,
                volume_coin double PRECISION NULL
            );
            create unique index if not exists ticks_{period}_time_exchange_pair_uindex on ticks_{period} (time, exchange, pair);
            SELECT create_hypertable('ticks_{period}','time', if_not_exists => TRUE);
            """)
        except (Exception, psycopg2.Error) as error:
            self.log.error(error.pgerror)
        self.conn.commit()

    def start(self):
        for m in self.minutes:
            threading.Thread(target=self.handle_period, args=(m,)).start()

    # Period in minutes
    def handle_period(self, period: int):
        while True:
            time.sleep(5)
            available_pairs = self.get_available_pairs(f"{period * 2} minutes")
            for (exchange, pair) in available_pairs:
                idx = self.minutes.index(period)
                # query_db_table = f"ticks_{self.minutes[idx - 1]}" if idx > 0 else "ticks"
                query_db_table = "ticks"
                insert_db_table = f"ticks_{self.minutes[idx]}"
                prices = self.get_prices(query_db_table, exchange, pair, f"{period * 10} minutes", f"{period} minutes")
                self.record_prices(insert_db_table, exchange, pair, prices)
                print(prices)

    def get_prices(self, table: str, exchange: str, pair: str, interval: str, bucket_size: str) -> Optional[DataFrame]:
        c = self.conn.cursor()
        try:
            query = f"""
            SELECT time_bucket('{bucket_size}', time) as period,
                last(closing_price, time) as closing_price,
                first(closing_price, time) as opening_price,
                max(closing_price) as highest_price,
                min(closing_price) as lowest_price,
                avg(volume_base) as volume_base,
                avg(volume_coin) as volume_coin            
            FROM {table}
            WHERE time > (NOW() - INTERVAL '{interval}') and pair = '{pair}' and exchange = '{exchange}'
            GROUP BY period
            ORDER BY period;           
            """
            c.execute(query)
            res = c.fetchall()
            return DataFrame(res)
        except (Exception, psycopg2.Error) as error:
            self.log.error(error.pgerror)
            return None
        finally:
            c.close()

    def record_prices(self, target_table: str, exchange: str, pair: str, prices: DataFrame):
        c = self.conn.cursor()
        for index, row in prices.iterrows():
            if index == 0:
                # Skip first row (the latest entry usually contains residual recalculations)
                continue
            try:
                opening_price = row[2] if row[2] and not math.isnan(row[2]) else 'null'
                highest_price = row[3] if row[3] and not math.isnan(row[3]) else 'null'
                lowest_price = row[4] if row[4] and not math.isnan(row[4]) else 'null'
                closing_price = row[1] if row[1] else 'null'
                volume_base = row[5] if row[5] and not math.isnan(row[5]) else 'null'
                volume_coin = row[6] if row[6] and not math.isnan(row[6]) else 'null'
                query = f"""
                INSERT INTO {target_table}
                    (time, exchange, pair, opening_price, highest_price,   
                     lowest_price, closing_price, volume_base, volume_coin)
                VALUES ('{row[0]}', '{exchange}', '{pair}', {opening_price},
                        {highest_price}, {lowest_price}, {closing_price},
                        {volume_base}, {volume_coin})
                ON CONFLICT (time, exchange, pair)
                DO UPDATE SET opening_price = excluded.opening_price,
                              highest_price = excluded.highest_price,
                              lowest_price  = excluded.lowest_price,
                              closing_price = excluded.closing_price,
                              volume_base = excluded.volume_base,
                              volume_coin = excluded.volume_coin;  
                """
                # print(query)
                c.execute(query)
            except (Exception, psycopg2.Error) as error:
                print(query)
                self.log.error(error.pgerror)
            self.conn.commit()

    def get_available_pairs(self, interval: str = '1 hour') -> list[(str, str)]:
        c = self.conn.cursor()
        try:
            c.execute(f"""
            SELECT distinct exchange, pair
            FROM ticks
            WHERE time >= now() - INTERVAL '{interval}'
            GROUP BY exchange, pair            
            """)
            data = c.fetchall()
            return data
        except (Exception, psycopg2.Error) as error:
            self.log.error(error.pgerror)
            return []


if __name__ == "__main__":
    t = TimescaleRecorder()
    t.listen()
    # ttd = TickerTimeDimension()
    # ttd.start()

    # threading.Thread(target=t.listen).start()
    #
    # pair = "BTC/USD"
    #
    # em = events.EventManager()
    # em.send_command_to_address("db-recorder", RecorderSchema, {
    #     "timestamp": int(time.time() * 1000),
    #     "type": "ticker",
    #     "search_index": "delete_me",
    #     "data": {
    #         "pair": pair,
    #         "exchange": "ftx",
    #         "high": 34501,
    #         "low": 34451,
    #         "bid": 34456.5555,
    #         "bidVolume": 345621234,
    #         "ask": 34458.567,
    #         "askVolume": 32123478,
    #         "open": 34456,
    #         "close": 34557,
    #         "last": 34501.786,
    #         "baseVolume": 98787665,
    #         "quoteVolume": 766537865
    #     }
    # })
    #
    # em.send_command_to_address("db-recorder", RecorderSchema, {
    #     "timestamp": int(time.time() * 1000),
    #     "type": "indicator",
    #     "data": {
    #         "pair": pair,
    #         "exchange": "ftx_not_real",
    #         "name": "RSI",
    #         "value1": 56.89
    #     }
    # })

    time.sleep(1000)
