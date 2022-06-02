import datetime
import time
from typing import Optional
import events
import talib
import psycopg2
from eslogger import Logger
from pandas import DataFrame
from os import environ
from schemas.recorder import RecorderSchema
from concurrent.futures.thread import ThreadPoolExecutor


class TechnicalAnalysisIndicators:
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
        self.em = events.EventManager(host=kafka_host, port=int(kafka_port))
        self.conn = psycopg2.connect(f"postgres://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}")

    def get_available_pairs(self) -> list[(str, str)]:
        c = self.conn.cursor()
        try:
            c.execute("""
            SELECT distinct exchange, pair
            FROM ticks
            WHERE time >= now() - INTERVAL '1 hour'
            GROUP BY exchange, pair            
            """)
            data = c.fetchall()
            return data
        except (Exception, psycopg2.Error) as error:
            self.log.error(error.pgerror)
            return []

    def get_closing_prices(self, exchange: str, pair: str, interval: str, bucket_size: str = "1 minute") -> Optional[DataFrame]:
        c = self.conn.cursor()
        bucket_minutes = int(bucket_size.split()[0])
        try:
            if bucket_size.split()[1] in ["minutes", "minute"] and bucket_minutes in [1,5,10,30,60]:
                query = f"""
                    SELECT closing_price as avg_price
                    FROM ticks_{bucket_minutes}
                    WHERE time > (NOW() - INTERVAL '{interval}') and pair = '{pair}' and exchange = '{exchange}'            
                    ORDER BY time; 
                """
            else:
                query = f"""
                    SELECT time_bucket('{bucket_size}', time) as bucket,
                        avg(closing_price) as avg_price
                        FROM ticks
                        WHERE time > (NOW() - INTERVAL '{interval}') and pair = '{pair}' and exchange = '{exchange}'
                        GROUP BY bucket
                        ORDER BY bucket; 
                """
            c.execute(query)
            res = c.fetchall()
            return DataFrame(res)
        except (Exception, psycopg2.Error) as error:
            self.log.error(error.pgerror)
            return None
        finally:
            c.close()

    # TODO: Make it more modular! I'm just cutting corners
    def __RSI(self, df: DataFrame, pair: str, exchange: str, suffix: str = "1D"):
        res = talib.RSI(df[0].to_numpy())
        self.em.send_command_to_address("db-recorder", RecorderSchema, {
            "timestamp": int(time.time() * 1000),
            "type": "indicator",
            "data": {
                "pair": pair,
                "exchange": exchange,
                "name": f"RSI_{suffix}",
                "value1": res[-1]
            }
        })

    def RSI_1D(self, exchange: str, pair: str):
        start = datetime.datetime.now()
        df = self.get_closing_prices(exchange, pair, '1 day', '1 minute')
        self.__RSI(df, pair, exchange)
        print(f"RSI_1D: duration - {datetime.datetime.now() - start}")

    def RSI_5D(self, exchange: str, pair: str):
        start = datetime.datetime.now()
        df = self.get_closing_prices(exchange, pair, '5 days', "5 minutes")
        self.__RSI(df, pair, exchange, "5D")
        print(f"RSI_5D: duration - {datetime.datetime.now() - start}")

    def RSI_1M(self, exchange: str, pair: str):
        start = datetime.datetime.now()
        df = self.get_closing_prices(exchange, pair, '1 month', "30 minutes")
        self.__RSI(df, pair, exchange, "1M")
        print(f"RSI_1M: duration - {datetime.datetime.now() - start}")

    def RSI_3M(self, exchange: str, pair: str):
        start = datetime.datetime.now()
        df = self.get_closing_prices(exchange, pair, '3 months', "60 minutes")
        self.__RSI(df, pair, exchange, "3M")
        print(f"RSI_3M: duration - {datetime.datetime.now() - start}")

    def MACD(self, exchange: str, pair: str):
        start = datetime.datetime.now()
        df = self.get_closing_prices(exchange, pair, '1 hour')
        macd, macdsignal, macdhist = talib.MACD(df[0].to_numpy())
        self.em.send_command_to_address("db-recorder", RecorderSchema, {
            "timestamp": int(time.time() * 1000),
            "type": "indicator",
            "data": {
                "pair": pair,
                "exchange": exchange,
                "name": "MACD",
                "value1": macd[-1],
                "value2": macdsignal[-1],
                "value3": macdhist[-1]
            }
        })
        print(f"MACD: duration - {datetime.datetime.now() - start}")

    def PRICE_LR_ANGLE_5MIN(self, exchange: str, pair: str):
        start = datetime.datetime.now()
        df = self.get_closing_prices(exchange, pair, interval='5 minute', bucket_size="1 second")
        lra = talib.LINEARREG_ANGLE(df[1].to_numpy())
        self.em.send_command_to_address("db-recorder", RecorderSchema, {
            "timestamp": int(time.time() * 1000),
            "type": "indicator",
            "data": {
                "pair": pair,
                "exchange": exchange,
                "name": "PRICE_LR_ANGLE_5MIN",
                "value1": lra[-1],
            }
        })
        print(f"PRICE_LR_ANGLE_1MIN: duration - {datetime.datetime.now() - start}")


    def calculate_indicators(self):
        available_pairs = self.get_available_pairs()
        start = datetime.datetime.now()
        print('Start generating indicators')
        for (exchange, pair) in available_pairs:
            print(f"Generating indicators for {exchange}, pair {pair}")
            with ThreadPoolExecutor(max_workers=10) as executor:
                # RSI
                executor.submit(self.RSI_1D, exchange, pair)
                executor.submit(self.RSI_5D, exchange, pair)
                executor.submit(self.RSI_1M, exchange, pair)
                executor.submit(self.RSI_3M, exchange, pair)

                # MACD
                executor.submit(self.MACD, exchange, pair)

                # LR
                executor.submit(self.PRICE_LR_ANGLE_5MIN, exchange, pair)
        print(f"Finish generating indicators for. Duration: {datetime.datetime.now() - start}")




if __name__ == "__main__":
    indicators = TechnicalAnalysisIndicators()
    # indicators.PRICE_LR_ANGLE_1MIN("ftx", "BTC/USD")
    while True:
        indicators.calculate_indicators()
        time.sleep(2)
