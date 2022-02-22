import ccxt
import events


class Exchange:
    def __init__(self, exchange_id: str, config=None):
        self.exchange_id = exchange_id
        exchange_class = getattr(ccxt, exchange_id)
        if config is not None:
            self.client = exchange_class(config)
        self.client = exchange_class()

        self.em = events.EventManager()
        self.em.create_address(f"{exchange_id}")

    def __del__(self):
        self.em.delete_address(f"{self.exchange_id}")

    def get_name(self):
        return self.exchange_id


# import datetime
# import time
#
# import events
# import threading
#
# em = events.EventManager()
# em.create_address('query_exchange')
# schema_str = """
# {
#         "namespace": "confluent.io.examples.serialization.avro",
#         "name": "CBPCommand",
#         "type": "record",
#         "fields": [
#             {"name": "pair", "type": "string"},
#             {"name": "command", "type": {
#                     "type": "enum",
#                     "name": "Command",
#                     "symbols": ["Tick", "OrderBook"]
#                 }
#             }
#         ]
# }
# """
#

# def send_messages():
#     em.send_command_to_address("bittrex", schema_str, {
#         "pair": "ETH/USD",
#         "command": "Tick"
#     })


# em.create_address("query_exchange")

# x = threading.Thread(target=send_messages)
# x.start()


# def command_executor(command):
#     print(f"{datetime.datetime.now()}: Got command {command}")
#
#
# y = threading.Thread(target=em.wait_for_command, args=("query_exchange", schema_str, command_executor))
# y.start()

# time.sleep(10)

# em.delete_address("query_exchange")