import uuid
import json
import time
from datetime import datetime
from tradingview_ta import TA_Handler, Interval


class Pairs:
    def __init__(self, symbol, screener, exchange, intervals=None):
        self.symbol = symbol
        self.screener = screener
        self.exchange = exchange
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


class Retrieve:
    def __init__(self, pairs_instance):
        self.pairs = pairs_instance
        self.data = self.collect_data_for_all_timeframes()

    def collect_data_for_all_timeframes(self):
        indicator_names = [
            "open", "close", "Mom", "RSI", "volume", "MACD.macd", "EMA20",
            "EMA50", "BB.upper", "BB.lower", "Pivot.M.Classic.R1",
            "Stoch.RSI.K", "ADX", "UO", "CCI20", "P.SAR", "Recommend.All"
        ]

        data = {}
        for key, handler in self.pairs.handlers.items():
            analysis = handler.get_analysis()
            indicators = {name: analysis.indicators[name] for name in indicator_names}
            data[key] = {"ma": analysis.moving_averages, "indicators": indicators}

        return data


class Technical_Analysis:
    RSI_MIN = 30
    RSI_MAX = 70
    MACD_SIGNAL_DIFF_BUY = 0.01
    MACD_SIGNAL_DIFF_SELL = -0.01
    STOCHASTIC_OSCILLATOR_MIN = 20
    STOCHASTIC_OSCILLATOR_MAX = 80
    UO_MIN = 30
    UO_MAX = 70
    ADX_MIN = 20
    ADX_MAX = 25
    CCI20_MIN = -100
    CCI20_MAX = 100
    RECOMMEND_BUY_THRESHOLD = 0.7
    RECOMMEND_SELL_THRESHOLD = 0.3

    INDICATOR_WEIGHTS = {
        "MA": 2,
        "RSI": 1,
        "MACD": 1,
        "BB": 1,
        "Stoch.RSI.K": 1,
        "ADX": 1,
        "UO": 1,
        "CCI20": 1,
        "RECO": 1,
        "PIVOT": 1,
        "PSAR": 1
    }

    def __init__(self, data):
        self.data = data

    def get_ma_message(self, time_frame, ma_value):
        ma_data = self.data[time_frame]['ma']
        if 'STRONG_BUY' == ma_value:
            return f"Moving Average: potential STRONG BUY ({ma_data['BUY']})"
        elif 'BUY' == ma_value:
            return f"Moving Average: potential BUY ({ma_data['BUY']}, {ma_data['SELL']}, {ma_data['NEUTRAL']})"
        elif 'STRONG_SELL' == ma_value:
            return f"Moving Average: potential STRONG SELL ({ma_data['SELL']})"
        elif 'SELL' == ma_value:
            return f"Moving Average: potential SELL ({ma_data['BUY']}, {ma_data['SELL']}, {ma_data['NEUTRAL']})"
        elif 'NEUTRAL' == ma_value:
            return f"Moving Average: WAIT ({ma_data['NEUTRAL']})"
        return "MA: HOLD"

    def ma_rec(self, time_frame, ma_value, direction_scores, reasoning):
        if ma_value is None:
            # reasoning.append("Moving Average value is missing (None)")
            return
        reason = self.get_ma_message(time_frame, ma_value)
        if 'BUY' in reason:
            direction_scores['BUY'] += self.INDICATOR_WEIGHTS["MA"]
        elif 'SELL' in reason:
            direction_scores['SELL'] += self.INDICATOR_WEIGHTS["MA"]
        reasoning.append(reason)

    def ma_logic(self, ema_20_value, ema_50_value, direction_scores, reasoning):
        if ema_20_value is None or ema_50_value is None:
            # reasoning.append("EMA value is missing (None)")
            return
        # Bullish Signal
        if ema_20_value > ema_50_value:
            direction_scores['BUY'] += 1
            reasoning.append("EMA20 is above EMA50, potential BUY")

        # Bearish Signal
        elif ema_20_value < ema_50_value:
            direction_scores['SELL'] += 1
            reasoning.append("EMA50 is above EMA20, potential SELL")

        # Neither bullish nor bearish
        else:
            reasoning.append("EMA20 and EMA50 are equal, no clear direction")

    def rsi_logic(self, rsi_value, direction_scores, reasoning):
        if rsi_value is None:
            # reasoning.append("RSI value is missing (None)")
            return
        if rsi_value < self.RSI_MIN:
            reasoning.append(f"RSI is below {self.RSI_MIN} - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["RSI"]
        elif rsi_value > self.RSI_MAX:
            reasoning.append(f"RSI is above {self.RSI_MAX} - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["RSI"]

    def macd_logic(self, macd_value, direction_scores, reasoning):
        if macd_value is None:
            # reasoning.append("MACD value is missing (None)")
            return
        if macd_value > self.MACD_SIGNAL_DIFF_BUY:
            reasoning.append("MACD is above the signal line - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["MACD"]
        elif macd_value < self.MACD_SIGNAL_DIFF_SELL:
            reasoning.append("MACD is below the signal line - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["MACD"]

    def bollinger_logic(self, bb_upper_value, bb_lower_value, close_value, direction_scores, reasoning):
        if None in [bb_upper_value, bb_lower_value, close_value]:
            # reasoning.append("Bollinger Band or Price value is missing (None)")
            return
        if close_value > bb_upper_value:
            reasoning.append("Price is above Bollinger Band upper limit - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["BB"]
        elif close_value < bb_lower_value:
            reasoning.append("Price is below Bollinger Band lower limit - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["BB"]

    def oscillator_logic(self, osc_value, direction_scores, reasoning):
        if osc_value is None:
            # reasoning.append("Stochastic Oscillator value is missing (None)")
            return
        if osc_value < self.STOCHASTIC_OSCILLATOR_MIN:
            reasoning.append("Stochastic Oscillator is in oversold region - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["Stoch.RSI.K"]
        elif osc_value > self.STOCHASTIC_OSCILLATOR_MAX:
            reasoning.append("Stochastic Oscillator is in overbought region - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["Stoch.RSI.K"]

    def adx_logic(self, adx_value, direction_scores, reasoning):
        if adx_value is None:
            # reasoning.append("ADX value is missing (None)")
            return
        if adx_value > self.ADX_MAX:
            reasoning.append("Strong trend strength (ADX)")
        elif adx_value < self.ADX_MIN:
            reasoning.append("Weak trend strength (ADX)")

    def uo_logic(self, uo_value, direction_scores, reasoning):
        if uo_value is None:
            # reasoning.append("UO value is missing (None)")
            return
        if uo_value > self.UO_MAX:
            reasoning.append("UO indicates overbought conditions - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["UO"]
        elif uo_value < self.UO_MIN:
            reasoning.append("UO indicates oversold conditions - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["UO"]

    def cci20_logic(self, cci20_value, direction_scores, reasoning):
        if cci20_value is None:
            return
        if cci20_value > self.CCI20_MAX:
            reasoning.append("CCI indicates overbought conditions - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["CCI20"]
        elif cci20_value < self.CCI20_MIN:
            reasoning.append("CCI indicates oversold conditions - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["CCI20"]

    def recommend_logic(self, recommend_all_value, direction_scores, reasoning):
        if recommend_all_value is None:
            return
        if recommend_all_value > self.RECOMMEND_BUY_THRESHOLD:
            direction_scores['BUY'] += self.INDICATOR_WEIGHTS["RECO"]
            reasoning.append("Recommendation score indicates potential BUY")
        elif recommend_all_value < self.RECOMMEND_SELL_THRESHOLD:
            direction_scores['SELL'] += self.INDICATOR_WEIGHTS["RECO"]
            reasoning.append("Recommendation score indicates potential SELL")
        else:
            direction_scores['WAIT'] += self.INDICATOR_WEIGHTS["RECO"]
            reasoning.append("Recommendation score is neutral - WAIT")

    def pivot_logic(self, current_price, pivot_r1, direction_scores, reasoning):
        if pivot_r1 is None or current_price is None:
            return
        if current_price > pivot_r1:
            direction_scores['BUY'] += self.INDICATOR_WEIGHTS["PIVOT"]
            reasoning.append("Price is above Pivot Point R1, potential BUY")

    def psar_logic(self, current_price, psar_value, direction_scores, reasoning):
        if psar_value is None or current_price is None:
            return
        if current_price > psar_value:
            direction_scores['BUY'] += self.INDICATOR_WEIGHTS["PSAR"]
            reasoning.append("Price is above P.SAR, potential BUY")
        else:
            direction_scores['SELL'] += self.INDICATOR_WEIGHTS["PSAR"]
            reasoning.append("Price is below P.SAR, potential SELL")

    def decide_trade_action(self):
        decisions = {}
        for timeframe, values in self.data.items():
            direction_scores = {"BUY": 0, "SELL": 0, "WAIT": 0}
            reasoning = []
            self.ma_rec(timeframe, values["ma"]['RECOMMENDATION'], direction_scores, reasoning)
            self.ma_logic(values["indicators"]['EMA20'], values["indicators"]['EMA50'], direction_scores, reasoning)
            self.rsi_logic(values["indicators"]['RSI'], direction_scores, reasoning)
            self.macd_logic(values["indicators"]['MACD.macd'], direction_scores, reasoning)
            self.bollinger_logic(values["indicators"]['BB.upper'], values["indicators"]['BB.lower'],
                                 values["indicators"]['close'], direction_scores, reasoning)
            self.oscillator_logic(values["indicators"]['Stoch.RSI.K'], direction_scores, reasoning)
            self.adx_logic(values["indicators"]['ADX'], direction_scores, reasoning)
            self.uo_logic(values["indicators"]['UO'], direction_scores, reasoning)
            self.cci20_logic(values["indicators"]['CCI20'], direction_scores, reasoning)
            self.recommend_logic(values["indicators"]['Recommend.All'], direction_scores, reasoning)
            self.pivot_logic(values["indicators"]['close'], values["indicators"]['Pivot.M.Classic.R1'],
                             direction_scores, reasoning)
            self.psar_logic(values["indicators"]['close'], values["indicators"]['P.SAR'],
                            direction_scores, reasoning)

            decisions[timeframe] = {
                'reasoning': reasoning,
                'confidence_score': direction_scores,
            }

        return {k: decisions[k] for k in self.data.keys()}


class Logger:
    def __init__(self, base_path):
        self.base_path = base_path

    def prepare_log_data(self, symbol, trade_id, trade_decision, indicators):
        log_data = {
            'symbol': symbol,
            'run_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trade_id': trade_id,
            'decisions': {},
            'indicators': indicators
        }

        for time_frame, decision in trade_decision.items():
            decision_data = trade_decision[time_frame]
            confidence_score = decision_data['confidence_score']
            strategies = decision_data['reasoning']

            log_data['decisions'][time_frame] = {
                'confidence_score': confidence_score,
                'strategies': strategies,
            }

        return log_data

    def log_symbol_data(self, symbol, symbol_data):
        current_time = datetime.now().strftime('%Y_%m_%d_%H_%M')
        filename = f"{symbol.lower()}_{current_time}.txt"
        log_file_path = f"{self.base_path}/{filename}"

        with open(log_file_path, 'w') as file:
            file.write(json.dumps(symbol_data, indent=4))
            file.write("\n\n")


class Trader:
    def __init__(self, potential_trades):
        self.potential_trades = potential_trades
        self.best_candidate = self.find_best_candidate()

    def find_best_candidate(self):
        # This function finds the best trading candidate based on confidence scores
        max_score = 0
        best_candidate = None

        for trade in self.potential_trades:
            symbol = trade['symbol']
            time_frame = trade['time_frame']
            buy_score = trade['confidence_score']['BUY']
            sell_score = trade['confidence_score']['SELL']

            score = buy_score - sell_score

            if score > max_score:
                max_score = score
                best_candidate = {
                    'symbol': symbol,
                    'time_frame': time_frame,
                    'score': score,
                    'reasoning': trade['reasoning']
                }

        return best_candidate

    def display_best_candidate(self):
        if self.best_candidate:
            print(
                f"Best trading opportunity is for {self.best_candidate['symbol']} ({self.best_candidate['time_frame']}) "
                f"with a score of {self.best_candidate['score']}. Reasoning: {', '.join(self.best_candidate['reasoning'])}")


if __name__ == "__main__":

    symbols = ["USDJPY", "GBPJPY", "EURJPY", "EURUSD", "AUDUSD", "GBPUSD", "EURRUB", "GBPJPY", "USDCAD"]
    screener = "forex"
    exchange = "FX_IDC"
    trade_logger = Logger("/Users/stenuuesoo/Ladna/ptoq/logs")
    custom_intervals = {
        "5m": Interval.INTERVAL_5_MINUTES,
        "15m": Interval.INTERVAL_15_MINUTES,
        "30m": Interval.INTERVAL_30_MINUTES,
        "1h": Interval.INTERVAL_1_HOUR,
        "2h": Interval.INTERVAL_2_HOURS,
        "4h": Interval.INTERVAL_4_HOURS,
    }
    potential_trades = []

    for symbol in symbols:
        trade_id = str(uuid.uuid4())[:8]
        pairs_instance = Pairs(symbol, screener, exchange, intervals=custom_intervals)

        all_data = Retrieve(pairs_instance).data
        analysis_component = Technical_Analysis(all_data)
        trade_decision = analysis_component.decide_trade_action()

        symbol_data = trade_logger.prepare_log_data(symbol, trade_id, trade_decision, all_data)

        for time_frame, decision_data in trade_decision.items():
            potential_trades.append({
                'symbol': symbol,
                'time_frame': time_frame,
                'reasoning': decision_data['reasoning'],
                'confidence_score': decision_data['confidence_score']
            })

    trader = Trader(potential_trades)
    trader.display_best_candidate()