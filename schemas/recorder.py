RecorderSchema = """
{
        "namespace": "confluent.io.examples.serialization.avro",
        "name": "CBPRecord",
        "type": "record",
        "fields": [   
            {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},         
            {"name": "type", "type": "string"},
            {"name": "search_index", "type": ["string", "null"]},
            {"name": "data", "type": [                
                {
                    "type": "record",
                    "name": "order_book",                    
                    "fields": [
                        { "name": "pair", "type": "string" },
                        { "name": "exchange", "type": "string" },
                        { "name": "bids", "type": { "type": "array", "items": { "type": "array", "items": "float" } } },
                        { "name": "asks", "type": { "type": "array", "items": { "type": "array", "items": "float" } } }                  
                    ]
                },
                {
                    "type": "record",
                    "name": "ticker",
                    "fields": [                        
                        {"name": "pair", "type": "string" },
                        {"name": "exchange", "type": "string"},
                        {"name": "high", "type": ["float", "null"] },
                        {"name": "low", "type": ["float", "null"] },
                        {"name": "bid", "type": "float" },
                        {"name": "bidVolume", "type": ["float", "null"] },
                        {"name": "ask", "type": "float" },
                        {"name": "askVolume", "type": ["float", "null"] },
                        {"name": "open", "type": ["float", "null"] },
                        {"name": "close", "type": ["float", "null"] },
                        {"name": "last", "type": ["float", "null"] },
                        {"name": "baseVolume", "type": ["float", "null"] },
                        {"name": "quoteVolume", "type": ["float", "null"] }                        
                    ]                    
                },
                {
                    "type": "record",
                    "name": "indicator",
                    "fields": [                        
                        {"name": "pair", "type": "string" },
                        {"name": "exchange", "type": "string"},
                        {"name": "name", "type": "string" },
                        {"name": "value1", "type": "float" },                        
                        {"name": "value2", "type": ["float", "null"] },
                        {"name": "value3", "type": ["float", "null"] },
                        {"name": "value4", "type": ["float", "null"] }                        
                    ]                    
                }
            ]}
        ]
}
"""