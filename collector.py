from tradingview_ta import TA_Handler, Interval, Exchange

class Pairs:
    def __init__(self, symbol="EURUSD", screener="forex", exchange="FX_IDC"):
        self.symbol = symbol
        self.screener = screener
        self.exchange = exchange

        self.intervals = {
            "1h": Interval.INTERVAL_1_HOUR,
        }

        self.handlers = {k: TA_Handler(
            symbol=self.symbol,
            screener=self.screener,
            exchange=self.exchange,
            interval=v
        ) for k, v in self.intervals.items()}


class Retrieve:
    def __init__(self, pairs_instance):
        self.pairs = pairs_instance
        self.data = self.collect_data_for_all_timeframes()

    def collect_data_for_all_timeframes(self):
        indicator_names = [
            "open", "close", "Mom", "RSI", "volume", "MACD.macd", "EMA20",
            "EMA50", "BB.upper", "BB.lower", "Pivot.M.Classic.R1",
            "Pivot.M.Classic.S1", "Stoch.RSI.K", "ADX", "UO", "CCI20", "P.SAR", "Recommend.All"
        ]

        data = {}
        for key, handler in self.pairs.handlers.items():
            analysis = handler.get_analysis()
            indicators = {name: analysis.indicators[name] for name in indicator_names}
            data[key] = {"ma": analysis.moving_averages, "indicators": indicators}

        return data