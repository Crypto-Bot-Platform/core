GlobalMarketCommandSchema = """
{
        "namespace": "confluent.io.examples.serialization.avro",
        "name": "CBPCommand",
        "type": "record",
        "fields": [  
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},           
            {"name": "pair", "type": "string"},
            {"name": "command", "type": {
                    "type": "enum",
                    "name": "Command",
                    "symbols": ["Tick", "OrderBook"]
                }
            }
        ]
}
"""