import datetime
import time
from typing import Optional
import events
import talib
import psycopg2
from eslogger import Logger
from pandas import DataFrame

from schemas.recorder import RecorderSchema


class TechnicalAnalysisIndicators:
    def __init__(self):
        self.log = Logger(self.__class__.__name__)
        self.em = events.EventManager()
        # TODO: Use config file
        db_name = "cbp"
        db_user = "cbp_user"
        db_pass = "Password1234"
        db_host = "10.0.0.124"
        db_port = 5432
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

    def get_closing_prices(self, exchange: str, pair: str, interval: str) -> Optional[DataFrame]:
        c = self.conn.cursor()
        try:
            query = f"""
            SELECT time_bucket('1 minute', time) as bucket,
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

    def RSI(self, exchange: str, pair: str):
        df = self.get_closing_prices(exchange, pair, '1 hour')
        res = talib.RSI(df[1].to_numpy())
        self.em.send_command_to_address("db-recorder", RecorderSchema, {
            "timestamp": int(time.time() * 1000),
            "type": "indicator",
            "data": {
                "pair": pair,
                "exchange": exchange,
                "name": "RSI",
                "value1": res[-1]
            }
        })

    def MACD(self, exchange: str, pair: str):
        df = self.get_closing_prices(exchange, pair, '1 hour')
        macd, macdsignal, macdhist = talib.MACD(df[1].to_numpy())
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

    def calculate_indicators(self):
        # start = datetime.datetime.now()
        available_pairs = self.get_available_pairs()
        # print(f"Found {len(available_pairs)} pairs. Calculating Indicators")
        # count = 1
        for (exchange, pair) in available_pairs:
            self.RSI(exchange, pair)
            self.MACD(exchange, pair)
            # print(f"{count}: Indicators ready for {exchange}, pair {pair}")
            # count += 1
        # print(f"Duration: {datetime.datetime.now() - start}")


if __name__ == "__main__":
    indicators = TechnicalAnalysisIndicators()
    while True:
        indicators.calculate_indicators()
        time.sleep(10)
