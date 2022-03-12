from typing import Optional

import events
import numpy
import pandas
import talib
import psycopg2
from eslogger import Logger
from pandas import DataFrame


class Indicators:
    def __init__(self):
        self.log = Logger(self.__class__.__name__)
        self.em = events.EventManager()
        # TODO: Use config file
        db_name = "cbp"
        db_user = "cbp_user"
        db_pass = "Password1234"
        db_host = "10.0.0.212"
        db_port = 5432
        self.conn = psycopg2.connect(f"postgres://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}")

    def get_available_pairs(self) -> list[(str, str)]:
        c = self.conn.cursor()
        try:
            c.execute("""
            SELECT distinct exchange, pair
            FROM ticks
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
            query = " \
            SELECT time, closing_price, opening_price, exchange, pair \
            FROM ticks \
            WHERE time > (NOW() - INTERVAL '1 minute') \
            ORDER BY time; \
            "
            c.execute(query)
            res = c.fetchall()
            return DataFrame(res)
        except (Exception, psycopg2.Error) as error:
            self.log.error(error.pgerror)
            return None
        finally:
            c.close()

    def RSI(self, exchange: str, pair: str):
        df = self.get_closing_prices(exchange, pair, '1 minute')
        res = talib.RSI(df[1].to_numpy())
        print(res[-1])

    def calculate_indicators(self):
        for (exchange, pair) in self.get_available_pairs():

            self.RSI(exchange, pair)


if __name__ == "__main__":
    i = Indicators()
    i.calculate_indicators()
    # print(pairs)

    # close = numpy.random.random(100)
    #
    # output = talib.SMA(close)
    # print(output)