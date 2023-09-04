import time

from tradingview_ta import TA_Handler


class Pairs:
    def __init__(self, symbol, screener, exchange, intervals=None):
        self.symbol = symbol
        self.screener = screener
        self.exchange = exchange
        if intervals is None:
            intervals = {"5m": "5m"}  # Replace "5m" with the appropriate interval constant if needed

        self.intervals = intervals

        self.handlers = {}
        for k, v in self.intervals.items():
            time.sleep(0.3)
            self.handlers[k] = TA_Handler(
                symbol=self.symbol,
                screener=self.screener,
                exchange=self.exchange,
                interval=v
            )