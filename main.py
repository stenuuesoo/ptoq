import uuid
import time
from tradingview_ta import TA_Handler, Interval


class Pairs:
    def __init__(self, symbol, screener, exchange, intervals=None):
        self.symbol = symbol
        self.screener = screener
        self.exchange = exchange
        # If intervals is not passed, use a default value
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

    RSI_LIMITS = {'min': 30, 'max': 70}
    MACD_SIGNAL_DIFF = {'buy': 0.01, 'sell': -0.01}
    STOCHASTIC_OSCILLATOR_LIMITS = {'min': 20, 'max': 80}
    UO_LIMITS = {'min': 30, 'max': 70}
    ADX_LIMITS = {'min': 20, 'max': 25}
    CCI20_LIMITS = {'min': -100, 'max': 100}
    RECOMMEND_THRESHOLDS = {'buy': 0.7, 'sell': 0.3}

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
            return
        reason = self.get_ma_message(time_frame, ma_value)
        if 'BUY' in reason:
            direction_scores['BUY'] += self.INDICATOR_WEIGHTS["MA"]
        elif 'SELL' in reason:
            direction_scores['SELL'] += self.INDICATOR_WEIGHTS["MA"]
        reasoning.append(reason)

    def ma_logic(self, ema_20_value, ema_50_value, direction_scores, reasoning):
        if ema_20_value is None or ema_50_value is None:
            return
        if ema_20_value > ema_50_value:
            direction_scores['BUY'] += 1
            reasoning.append("EMA20 is above EMA50, potential BUY")
        elif ema_20_value < ema_50_value:
            direction_scores['SELL'] += 1
            reasoning.append("EMA50 is above EMA20, potential SELL")
        else:
            reasoning.append("EMA20 and EMA50 are equal, no clear direction")

    def rsi_logic(self, rsi_value, direction_scores, reasoning):
        if rsi_value is None:
            return
        if rsi_value < self.RSI_LIMITS['min']:
            reasoning.append(f"RSI is below {self.RSI_LIMITS['min']} - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["RSI"]
        elif rsi_value > self.RSI_LIMITS['max']:
            reasoning.append(f"RSI is above {self.RSI_LIMITS['max']} - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["RSI"]

    def macd_logic(self, macd_value, direction_scores, reasoning):
        if macd_value is None:
            return
        if macd_value > self.MACD_SIGNAL_DIFF['buy']:
            reasoning.append("MACD is above the signal line - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["MACD"]
        elif macd_value < self.MACD_SIGNAL_DIFF['sell']:
            reasoning.append("MACD is below the signal line - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["MACD"]

    def oscillator_logic(self, osc_value, direction_scores, reasoning):
        if osc_value is None:
            return
        if osc_value < self.STOCHASTIC_OSCILLATOR_LIMITS['min']:
            reasoning.append("Stochastic Oscillator is in oversold region - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["Stoch.RSI.K"]
        elif osc_value > self.STOCHASTIC_OSCILLATOR_LIMITS['max']:
            reasoning.append("Stochastic Oscillator is in overbought region - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["Stoch.RSI.K"]

    def adx_logic(self, adx_value, direction_scores, reasoning):
        if adx_value is None:
            return
        if adx_value > self.ADX_LIMITS['max']:
            reasoning.append("Strong trend strength (ADX)")
        elif adx_value < self.ADX_LIMITS['min']:
            reasoning.append("Weak trend strength (ADX)")

    def uo_logic(self, uo_value, direction_scores, reasoning):
        if uo_value is None:
            return
        if uo_value > self.UO_LIMITS['max']:
            reasoning.append("UO indicates overbought conditions - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["UO"]
        elif uo_value < self.UO_LIMITS['min']:
            reasoning.append("UO indicates oversold conditions - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["UO"]

    def cci20_logic(self, cci20_value, direction_scores, reasoning):
        if cci20_value is None:
            return
        if cci20_value > self.CCI20_LIMITS['max']:
            reasoning.append("CCI indicates overbought conditions - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["CCI20"]
        elif cci20_value < self.CCI20_LIMITS['min']:
            reasoning.append("CCI indicates oversold conditions - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["CCI20"]

    def bollinger_logic(self, bb_upper_value, bb_lower_value, close_value, direction_scores, reasoning):
        if None in [bb_upper_value, bb_lower_value, close_value]:
            return
        if close_value > bb_upper_value:
            reasoning.append("Price is above Bollinger Band upper limit - potential SELL")
            direction_scores["SELL"] += self.INDICATOR_WEIGHTS["BB"]
        elif close_value < bb_lower_value:
            reasoning.append("Price is below Bollinger Band lower limit - potential BUY")
            direction_scores["BUY"] += self.INDICATOR_WEIGHTS["BB"]

    def recommend_logic(self, recommend_all_value, direction_scores, reasoning):
        if recommend_all_value is None:
            return
        if recommend_all_value > self.RECOMMEND_THRESHOLDS['buy']:
            direction_scores['BUY'] += self.INDICATOR_WEIGHTS["RECO"]
            reasoning.append("Recommendation score indicates potential BUY")
        elif recommend_all_value < self.RECOMMEND_THRESHOLDS['sell']:
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


class Trade:
    def __init__(self, pair, entry_price, stop_loss, target_price, time_frame, trade_direction):
        self.pair = pair
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.target_price = target_price
        self.time_frame = time_frame
        self.trade_direction = trade_direction


def collect_potential_trades(symbols, screener, exchange, custom_intervals):
    potential_trades = []

    for symbol in symbols:
        trade_id = str(uuid.uuid4())[:8]
        pairs_instance = Pairs(symbol, screener, exchange, intervals=custom_intervals)

        all_data = Retrieve(pairs_instance).data
        analysis_component = Technical_Analysis(all_data)
        trade_decision = analysis_component.decide_trade_action()

        for time_frame, decision_data in trade_decision.items():
            potential_trades.append({
                'symbol': symbol,
                'time_frame': time_frame,
                'reasoning': decision_data['reasoning'],
                'confidence_score': decision_data['confidence_score'],
                'indicators': all_data[time_frame]['indicators']
            })

    return potential_trades


class Trader:
    def __init__(self, potential_trades):
        self.potential_trades = potential_trades
        self.best_candidate = self.find_best_candidate()
        self.open_trades = []  # List to hold the currently open trades
        self.max_open_trades = 2  # Maximum allowed open trades
        self.pips_target = 20  # Pips challenge target
        self.display_best_candidate()

    def find_best_candidate(self):
        max_score = 0
        best_candidate = None

        for trade in self.potential_trades:

            print(
                f"\nCandidate: {trade['symbol']} ({trade['time_frame']}) with a score of {trade['confidence_score']}. Reasoning: {', '.join(trade['reasoning'])}")

            symbol = trade['symbol']
            time_frame = trade['time_frame']

            # Modifying the access structure to match the appended data
            buy_score = trade['confidence_score']['BUY']
            sell_score = trade['confidence_score']['SELL']

            # A simplistic way to determine score
            # Modify this based on your trading strategy and risk appetite
            score = buy_score - sell_score

            if score > max_score:
                max_score = score
                best_candidate = {
                    'symbol': symbol,
                    'time_frame': time_frame,
                    'score': score,
                    'confidence_score': trade['confidence_score'],
                    'reasoning': trade['reasoning'],
                    'indicators': trade['indicators']
                }

        return best_candidate

    def display_best_candidate(self):
        if self.best_candidate:
            print(
                f"\nBest trading opportunity is for {self.best_candidate['symbol']} ({self.best_candidate['time_frame']}) with a score of {self.best_candidate['score']}. Reasoning: {', '.join(self.best_candidate['reasoning'])}")

    def find_sorted_candidates(self):
        return sorted(self.potential_trades, key=lambda x: x['confidence_score'], reverse=True)

    def find_new_candidates(self, screener, exchange, custom_intervals):
        if len(self.open_trades) < self.max_open_trades:
            print("\n<2 trades. Finding new trade candidates...")
            self.potential_trades = collect_potential_trades(symbols, screener, exchange, custom_intervals)
            temp_open_trades = self.open_trades[:]
            self.potential_trades = [trade for trade in self.potential_trades if
                                     not self.trade_open_for_pair(trade['symbol'])]
            self.best_candidate = self.find_best_candidate()
            self.open_trades = temp_open_trades[:]

            if self.best_candidate:
                print(f"New best candidate found: {self.best_candidate['symbol']}")
            else:
                print("No suitable candidate found.")

    @property
    def current_market_price(self):
        return self.best_candidate['indicators']['close']

    def trade_open_for_pair(self, pair):
        for trade in self.open_trades:
            if trade.pair == pair:
                return True
        return False

    def refresh_trade_pair_price_data(self, symbol, time_frame, screener, exchange, custom_intervals):
        pairs_instance = Pairs(symbol, screener, exchange)
        all_data = Retrieve(pairs_instance).data

        return all_data["5m"]["indicators"]["close"]

    def execute_trade(self, time_frame):
        pair = self.best_candidate['symbol']
        entry_price = self.current_market_price
        confidence_scores = self.best_candidate['confidence_score']
        print(confidence_scores)
        buy_score = confidence_scores.get('BUY', 0)
        sell_score = confidence_scores.get('SELL', 0)

        if buy_score >= sell_score:
            trade_direction = 'BUY'
            target_price = entry_price + (self.pips_target / 1000)  # Target price is above entry for BUY trades
            stop_loss = entry_price - (self.pips_target / 1000)  # Stop loss is below entry for BUY trades
        else:
            trade_direction = 'SELL'
            target_price = entry_price - (self.pips_target / 1000)  # Target price is below entry for SELL trades
            stop_loss = entry_price + (self.pips_target / 1000)  # Stop loss is above entry for SELL trades

        new_trade = Trade(pair, entry_price, stop_loss, target_price, time_frame, trade_direction)
        self.open_trades.append(new_trade)

        print(
            f"\n{trade_direction} trade opened for {pair} at {entry_price}, with target {target_price} and stop loss {stop_loss}")

    def update_open_trades(self, screener, exchange, custom_intervals):
        trades_to_remove = []  # List to hold trades that need to be closed

        for trade in self.open_trades:

            current_price = self.refresh_trade_pair_price_data(trade.pair, trade.time_frame, screener, exchange,
                                                               custom_intervals)

            total_pips_move = trade.entry_price - current_price if trade.trade_direction == 'BUY' else current_price - trade.entry_price

            print(
                f"\nCurrent price for {trade.pair}: {current_price}. Target {trade.target_price}. So far {total_pips_move} Pips")

            if current_price >= trade.target_price:
                print(f"Take profit hit for {trade.pair}. Closing trade.")
                self.open_trades.remove(trade)
            elif current_price <= trade.stop_loss:
                print(f"Stop loss hit for {trade.pair}. Closing trade.")
                self.open_trades.remove(trade)

        for trade in trades_to_remove:
            self.open_trades.remove(trade)

    def execute_trades(self):
        if self.best_candidate is not None:
            time_frame = self.best_candidate['time_frame']
            pair = self.best_candidate['symbol']
            if not self.trade_open_for_pair(pair) and len(self.open_trades) < self.max_open_trades:
                self.execute_trade(time_frame)
        else:
            print("\nNo candidate to execute trade for.")


if __name__ == "__main__":
    symbols = ["USDJPY", "GBPJPY", "EURJPY", "EURUSD", "AUDUSD", "GBPUSD", "EURRUB", "GBPJPY", "USDCAD"]
    screener = "forex"
    exchange = "FX_IDC"

    custom_intervals = {
        "15m": Interval.INTERVAL_15_MINUTES,
    }

    potential_trades = collect_potential_trades(symbols, screener, exchange, custom_intervals)
    trader = Trader(potential_trades)

    last_time_update_trades = 0
    last_time_find_candidates = 0

    update_interval = 60  # Refresh open trades every 60 seconds
    find_new_interval = 900  # Find new candidates every 900 seconds (15 minutes)

    while True:
        current_time = time.time()

        if current_time - last_time_update_trades >= update_interval:
            print("Checking open trades...")
            trader.update_open_trades(screener, exchange, custom_intervals)
            last_time_update_trades = current_time

        if current_time - last_time_find_candidates >= find_new_interval:
            trader.find_new_candidates(screener, exchange, custom_intervals)
            last_time_find_candidates = current_time

        trader.execute_trades()

        time.sleep(15)