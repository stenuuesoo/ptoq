import uuid
import time
import requests
from tradingview_ta import TA_Handler, Interval

class Telegram_ptoq_bot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def send_telegram_message(self, message):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.chat_id}&text={message}"
        response = requests.get(url)
        return response.json()


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


class Retrieve:
    def __init__(self, pairs_instance, indicator_names, attributes=None):
        self.pairs = pairs_instance
        self.indicator_names = indicator_names
        self.attributes = attributes if attributes else ["ma", "indicators"]
        self.data = self.collect_data_for_all_timeframes()

    def collect_data_for_all_timeframes(self):
        data = {}
        for key, handler in self.pairs.handlers.items():
            analysis = handler.get_analysis()
            subset = {}

            if "ma" in self.attributes:
                subset["ma"] = analysis.moving_averages

            if "indicators" in self.attributes:
                subset["indicators"] = {name: analysis.indicators[name] for name in self.indicator_names}

            data[key] = subset

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
    def __init__(self, pair, entry_price, stop_loss, target_price, time_frame, trade_direction,
                 lot_size, trade_amount_in_dollars, potential_profit_or_loss, pip_value):
        self.pair = pair
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.target_price = target_price
        self.time_frame = time_frame
        self.trade_direction = trade_direction
        self.lot_size = lot_size  # Added to store lot_size
        self.trade_amount_in_dollars = trade_amount_in_dollars  # Added to store trade_amount_in_dollars
        self.potential_profit_or_loss = potential_profit_or_loss  # Added to store potential_profit_or_loss
        self.pip_value = pip_value  # Save pip_value


class Trader:
    def __init__(self, min_score, symbols, screener, exchange, custom_intervals, indicator_names, trade_size=100000, account_balance=10000):

        self.potential_trades = self.collect_potential_trades(symbols, screener, exchange, custom_intervals, indicator_names)
        self.min_score = min_score
        self.best_candidate = self.find_best_candidate()
        self.open_trades = []  # List to hold the currently open trades
        self.max_open_trades = 2  # Maximum allowed open trades
        self.trade_target = 30  # Pips challenge target
        self.analysis_cache = {}  # Step 1: Initialize the cache here
        self.trade_size = trade_size  # New attribute to store trade size
        self.account_balance = account_balance  # Added account_balance
        self.last_cache_update_time = 0
        self.trade_score = 0

    def collect_potential_trades(self, symbols, screener, exchange, custom_intervals, indicator_names):
        potential_trades = []

        for symbol in symbols:
            trade_id = str(uuid.uuid4())[:8]
            pairs_instance = Pairs(symbol, screener, exchange, intervals=custom_intervals)

            all_data = Retrieve(pairs_instance, indicator_names).data
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

    def execute_trade(self, time_frame):
        pair, entry_price, trade_direction, stop_loss, target_price, lot_size, trade_amount_in_dollars, max_risk_dollars, pip_value, stop_loss_pips, target_pips = self.set_trade_parameters(
            time_frame)
        new_trade = Trade(pair, entry_price, stop_loss, target_price, time_frame, trade_direction,
                          lot_size, trade_amount_in_dollars, max_risk_dollars, pip_value)
        self.open_trades.append(new_trade)

        message = (
            f"\n{trade_direction} trade opened: {pair} at {entry_price:.4f}, lot size: {lot_size:.2f} units."
            f"\nTarget: {target_price:.4f} ({target_pips} pips), Stop Loss: {stop_loss:.4f} ({stop_loss_pips} pips)"
        )
        print(message)
        telegram_messager.send_telegram_message(message)

    def update_open_trades(self, screener, exchange, custom_intervals, indicator_names, time_passed):
        trades_to_remove = []

        for trade in self.open_trades:
            current_price = round(
                self.refresh_trade_pair_price_data(trade.pair, trade.time_frame, screener, exchange, custom_intervals,
                                                   ["open", "close"]), 4)

            trade.target_price = round(trade.target_price, 4)
            trade.stop_loss = round(trade.stop_loss, 4)
            # Debugging line to print and check the values.
            #print(f"current_price: {current_price}, target_price: {trade.target_price}, stop_loss: {trade.stop_loss}")

            change_in_price = current_price-trade.entry_price

            should_close_trade = (trade.trade_direction == 'BUY' and (
                    current_price >= trade.target_price or current_price <= trade.stop_loss)) or \
                                 (trade.trade_direction == 'SELL' and (
                                         current_price <= trade.target_price or current_price >= trade.stop_loss))

            if should_close_trade:
                action_type = "Take profit hit" if current_price >= trade.target_price else "Stop loss hit"
                relevant_price = trade.target_price if current_price >= trade.target_price else trade.stop_loss
                action = (
                    f"{action_type} for {trade.pair}."
                    f"\nEntry: {trade.entry_price:.4f}, Change: {change_in_price:.4f}"
                    f"\nRelevant Price: {relevant_price:.4f}. Trade closed."
                )
                print(action)
                telegram_messager.send_telegram_message(action)
                trades_to_remove.append(trade)

        for trade in trades_to_remove:
            self.open_trades.remove(trade)
        time_since_last_check = time_passed - self.last_cache_update_time

        if len(self.open_trades) < self.max_open_trades and time_since_last_check >= 6:
            self.find_new_candidates(screener, exchange, custom_intervals, indicator_names)
            self.last_cache_update_time = time_passed  # Update last cache update time

    def trade_open_for_pair(self, pair):
        base_currency = pair[:3]
        quote_currency = pair[3:]

        for trade in self.open_trades:
            existing_base = trade.pair[:3]
            existing_quote = trade.pair[3:]

            if existing_base == base_currency or existing_base == quote_currency \
                    or existing_quote == base_currency or existing_quote == quote_currency:
                return True

        return False

    @property
    def current_market_price(self):
        return self.best_candidate['indicators']['close']

    def refresh_trade_pair_price_data(self, symbol, time_frame, screener, exchange, custom_intervals, indicator_names):
        pairs_instance = Pairs(symbol, screener, exchange)
        all_data = Retrieve(pairs_instance, indicator_names, attributes=["indicators"]).data
        return all_data["5m"]["indicators"]["close"]

    def execute_trades(self):
        if self.best_candidate is not None:
            time_frame = self.best_candidate['time_frame']
            pair = self.best_candidate['symbol']
            if not self.trade_open_for_pair(pair) and len(self.open_trades) < self.max_open_trades:
                self.execute_trade(time_frame)

    def find_new_candidates(self, screener, exchange, custom_intervals, indicator_names):
        if len(self.open_trades) >= self.max_open_trades:
            return

        temp_open_trades = self.open_trades.copy()
        self.collect_potential_trades(screener, exchange, custom_intervals, indicator_names)
        self.filter_already_open_trades()
        self.best_candidate = self.find_best_candidate()

        if self.best_candidate:
            self.execute_trades()

        self.open_trades = temp_open_trades

    def filter_already_open_trades(self):

        self.potential_trades = [trade for trade in self.potential_trades if not self.trade_open_for_pair(trade['symbol'])]

    def find_best_candidate(self):
        best_candidate = None
        max_score = 0

        for trade in self.potential_trades:
            print(
                f"\nCandidate: {trade['symbol']} ({trade['time_frame']}) with a score of {trade['confidence_score']}. "
                f"Reasoning: {', '.join(trade['reasoning'])}"
            )

            trade_score, trade_direction = self.calculate_trade_score(trade)
            if trade_score > max_score:
                max_score = trade_score
                best_candidate = self.build_candidate(trade, trade_score, trade_direction)

        if best_candidate and best_candidate['score'] >= self.min_score:
            self.notify_best_candidate(best_candidate)

        return best_candidate

    def calculate_trade_score(self, trade):
        buy_score = trade['confidence_score']['BUY']
        sell_score = trade['confidence_score']['SELL']

        if buy_score > sell_score:
            return buy_score, "BUY"
        else:
            return sell_score, "SELL"

    def build_candidate(self, trade, trade_score, trade_direction):
        return {
            'symbol': trade['symbol'],
            'time_frame': trade['time_frame'],
            'score': trade_score,
            'confidence_score': trade['confidence_score'],
            'reasoning': trade['reasoning'],
            'indicators': trade['indicators'],
            'direction': trade_direction
        }

    def notify_best_candidate(self, best_candidate):
        message = (
            f"\nBest opportunity is to {best_candidate['direction']} {best_candidate['symbol']} "
            f"with an analysis score of {best_candidate['score']}."
        )

        for indicator in best_candidate['reasoning']:
            message += f"\n- {indicator}"

        print(message)
        telegram_messager.send_telegram_message(message)  # Assuming telegram_messager is imported

    def set_trade_parameters(self, time_frame):
        risk_percentage = 0.02  # 2%
        max_risk_dollars = self.account_balance * risk_percentage
        pair = self.best_candidate['symbol']
        entry_price = self.current_market_price
        confidence_scores = self.best_candidate['confidence_score']
        buy_score = confidence_scores.get('BUY', 0)
        sell_score = confidence_scores.get('SELL', 0)
        pip_value = 0.01 if 'JPY' in pair else 0.0001
        stop_loss_pips = 20
        target_pips = self.trade_target

        # Correcting the lot_size calculation
        risk_per_pip = max_risk_dollars / stop_loss_pips
        lot_size = risk_per_pip / 10  # Adjusting for the typical $10/pip value for a standard lot in EUR/USD

        if buy_score >= sell_score:
            trade_direction = 'BUY'
            stop_loss = entry_price - (stop_loss_pips * pip_value)
            target_price = entry_price + (target_pips * pip_value)
        else:
            trade_direction = 'SELL'
            stop_loss = entry_price + (stop_loss_pips * pip_value)
            target_price = entry_price - (target_pips * pip_value)

        trade_amount_in_dollars = max_risk_dollars
        return pair, entry_price, trade_direction, stop_loss, target_price, lot_size, trade_amount_in_dollars, max_risk_dollars, pip_value, stop_loss_pips, target_pips


if __name__ == "__main__":
    symbols = ["EURUSD"]#["USDJPY", "GBPJPY" , "EURJPY", "GBPUSD", "EURUSD", "GBPEUR", "AUDUSD",]
    screener = "forex"
    exchange = "FX_IDC"

    custom_intervals = {
        "15m": Interval.INTERVAL_15_MINUTES,
    }

    indicator_names = [
        "open", "close", "Mom", "RSI", "volume", "MACD.macd", "EMA20",
        "EMA50", "BB.upper", "BB.lower", "Pivot.M.Classic.R1",
        "Stoch.RSI.K", "ADX", "UO", "CCI20", "P.SAR", "Recommend.All"
    ]

    token = "6112505967:AAFvQzBpIiryzZfA4i9nzvVW63W6DFIqRpY"
    chat_id = "-1001910608077" #removed the - from the chat_id to disable sending messages
    telegram_messager = Telegram_ptoq_bot(token, chat_id)

    min_score = 2

    trader = Trader(min_score, symbols, screener, exchange, custom_intervals, indicator_names)
    trader.analysis_cache = {(trade['symbol'], trade['time_frame']): trade for trade in trader.potential_trades}

    while True:
        time_passed = time.process_time()
        trader.execute_trades()
        time.sleep(10)
        trader.update_open_trades(screener, exchange, custom_intervals, indicator_names, time_passed)

    #except Exception as e:
            #telegram_messager.send_telegram_message(f"An error occurred sending message: {e}")