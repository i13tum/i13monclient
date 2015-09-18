#I13 Mon Client


I13MonClient is an alternative client for your EmonPi. The only reason we created it was that we required very accurate timestamps in the millisecond range and also to combine it with a second datastream from ZigBee devices.

The data is transmitted over a SSL socket to the I13 Mon Server. The connection will try to reconnect and buffer locally in case of connection outages.

Minimal Python Version is Python 3.4
