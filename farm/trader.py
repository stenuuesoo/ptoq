import uuid

from datetime import datetime
import time

from farm.trade import Trade
from gathering.pairs import Pairs
from gathering.retrieve import Retrieve
from analysis.technical_analysis import Technical_Analysis
from messaging.telegram import Telegram

class Trader:
    def __init__(self, min_score, currencies, custom_intervals, indicator_names, token, chat_id, trade_size=100000,
                 account_balance=10000):
        self.current_price = None
        self.telegram_messager = Telegram(token, chat_id)
        self.potential_trades = self.collect_potential_trades(currencies, custom_intervals,
                                                              indicator_names)
        self.min_score = min_score
        self.best_candidate = self.find_best_trade_candidate()
        self.open_trades = []  # List to hold the currently open trades
        self.max_open_trades = 2  # Maximum allowed open trades
        self.trade_target = 30  # Pips challenge target
        self.analysis_cache = {}  # Step 1: Initialize the cache here
        self.trade_size = trade_size  # New attribute to store trade size
        self.account_balance = account_balance  # Added account_balance
        self.last_cache_update_time = 0
        self.trade_score = 0
        self.currencies = currencies



    def collect_potential_trades(self, currencies, custom_intervals, indicator_names):
        potential_trades = []  # Initialize an empty list to hold all potential trades

        # Get the current day of the week (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
        current_day = datetime.today().weekday()

        # Define which currencies to loop through based on the day of the week
        currencies_to_loop = currencies.keys() if current_day < 5 else ['crypto']

        for currency in currencies_to_loop:
            symbols = currencies[currency]["symbols"]
            screener = currencies[currency]["screener"]
            exchange = currencies[currency]["exchange"]

            for symbol in symbols:
                trade_id = str(uuid.uuid4())[:8]
                pairs_instance = Pairs(symbol, screener, exchange, intervals=custom_intervals)

                all_data = Retrieve(pairs_instance, indicator_names).data
                analysis_component = Technical_Analysis(all_data)
                trade_decision = analysis_component.calculate_analysis_score()

                for time_frame, decision_data in trade_decision.items():
                    potential_trades.append({
                        'symbol': symbol,
                        'time_frame': time_frame,
                        'reasoning': decision_data['reasoning'],
                        'confidence_score': decision_data['confidence_score'],
                        'indicators': all_data[time_frame]['indicators']
                    })

        return potential_trades

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
    def get_candidate_market_open_price(self):
        return self.best_candidate['indicators']['open']

    def refresh_trade_pair_open_price(self, symbol, time_frame, screener, exchange, indicator_names):
        pairs_instance = Pairs(symbol, screener, exchange)
        all_data = Retrieve(pairs_instance, indicator_names, attributes=["indicators"]).data
        return all_data["5m"]["indicators"]["open"]

    def filter_open_trades(self):

        self.potential_trades = [trade for trade in self.potential_trades if
                                 not self.trade_open_for_pair(trade['symbol'])]

    def calculate_trade_score(self, trade):
        buy_score = trade['confidence_score']['BUY']
        sell_score = trade['confidence_score']['SELL']

        if buy_score > sell_score:
            return buy_score, "BUY"
        else:
            return sell_score, "SELL"

    def build_best_candidate(self, trade, trade_score, trade_direction):
        return {
            'symbol': trade['symbol'],
            'time_frame': trade['time_frame'],
            'score': trade_score,
            'confidence_score': trade['confidence_score'],
            'reasoning': trade['reasoning'],
            'indicators': trade['indicators'],
            'direction': trade_direction
        }

    def generate_best_candidate_text(self, best_candidate):
        message = (
            f"\nBest opportunity is to {best_candidate['direction']} {best_candidate['symbol']} "
            f"with an analysis score of {best_candidate['score']}."
        )

        for indicator in best_candidate['reasoning']:
            message += f"\n- {indicator}"

        print(message)
        #self.telegram_messager.send_telegram_message(message)  # Assuming telegram_messager is imported
        try:
            self.telegram_messager.send_telegram_message(message)
        except Exception as e:
            self.telegram_messager.send_telegram_message(f"An error occurred sending message: {e}")

    def find_new_trade_candidates(self, currencies, custom_intervals, indicator_names):
        if len(self.open_trades) >= self.max_open_trades:
            return

        temp_open_trades = self.open_trades.copy()
        self.collect_potential_trades(currencies, custom_intervals, indicator_names)
        self.filter_open_trades()
        self.best_candidate = self.find_best_trade_candidate()

        if self.best_candidate:
            self.execute_trades()

        self.open_trades = temp_open_trades

    def find_best_trade_candidate(self):
        best_candidate = None
        max_score = 0

        for trade in self.potential_trades:
            message = f"\nCandidate: {trade['symbol']} ({trade['time_frame']}) with a score of {trade['confidence_score']}. " \
                      f"Reasoning: {', '.join(trade['reasoning'])}"

            print(message)

            trade_score, trade_direction = self.calculate_trade_score(trade)
            if trade_score > max_score:
                max_score = trade_score
                best_candidate = self.build_best_candidate(trade, trade_score, trade_direction)

        if best_candidate and best_candidate['score'] >= self.min_score:
            self.generate_best_candidate_text(best_candidate)

        return best_candidate

    def execute_trades(self):
        if self.best_candidate is not None:
            time_frame = self.best_candidate['time_frame']
            pair = self.best_candidate['symbol']
            if not self.trade_open_for_pair(pair) and len(self.open_trades) < self.max_open_trades:
                self.execute_trade(time_frame)

    def execute_trade(self, time_frame):
        pair, entry_price, trade_direction, stop_loss, target_price, lot_size, trade_amount_in_dollars, max_risk_dollars, pip_value, stop_loss_pips, target_pips, pip_scale = self.set_trade_parameters(
            time_frame)
        new_trade = Trade(pair, entry_price, stop_loss, target_price, time_frame, trade_direction,
                          lot_size, trade_amount_in_dollars, max_risk_dollars, pip_value, pip_scale)
        self.open_trades.append(new_trade)

        message = (
            f"\n{trade_direction} trade opened: {pair} at {entry_price:.4f}, lot size: {lot_size:.2f} units."
            f"\nTarget: {target_price:.4f} ({target_pips} pips), Stop Loss: {stop_loss:.4f} ({stop_loss_pips} pips)"
        )
        print(message)
        self.telegram_messager.send_telegram_message(message)

    def set_trade_parameters(self, time_frame):
        risk_percentage = 0.02  # 2%
        max_risk_dollars = self.account_balance * risk_percentage
        pair = self.best_candidate['symbol']
        entry_price = self.get_candidate_market_open_price
        confidence_scores = self.best_candidate['confidence_score']
        buy_score = confidence_scores.get('BUY', 0)
        sell_score = confidence_scores.get('SELL', 0)
        pip_scale = 0
        if 'crypto' in self.currencies.keys() and pair in self.currencies['crypto']['symbols']:
            pip_value = 1
            self.pip_scale = 6
        elif 'JPY' in pair:
            pip_value = 0.01
            self.pip_scale = 2
        else:
            pip_value = 0.0001
            self.pip_scale = 4

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
        return pair, entry_price, trade_direction, stop_loss, target_price, lot_size, trade_amount_in_dollars, max_risk_dollars, pip_value, stop_loss_pips, target_pips, pip_scale

    def update_open_trades(self, currencies, custom_intervals, indicator_names, time_passed):
        trades_to_remove = []

        for trade in self.open_trades:
            currency_type = None
            for curr_type, curr_data in currencies.items():
                if trade.pair in curr_data["symbols"]:
                    currency_type = curr_type
                    break

            # If currency_type is found, update screener and exchange variables
            if currency_type:
                screener = currencies[currency_type]["screener"]
                exchange = currencies[currency_type]["exchange"]

                # Update the trade (assuming self.refresh_trade_pair_price_data method exists)
                self.current_price = round(
                    self.refresh_trade_pair_open_price(
                        trade.pair, trade.time_frame, screener, exchange, ["open", "close"]
                    ),
                    4
                )
                # print(self.current_price)
            else:
                # print(f"Trade pair {trade.pair} not found in defined currencies. Skipping.")
                continue  # Skip to the next iteration if no match is found

            trade.target_price = round(trade.target_price, 4)
            trade.stop_loss = round(trade.stop_loss, 4)
            change_in_price = self.current_price - trade.entry_price

            # Debugging line to print and check the values.
            target_pips = ((trade.target_price - self.current_price) / trade.pip_value) * 10 ** trade.pip_scale
            loss_pips = ((self.current_price - trade.stop_loss) / trade.pip_value) * 10 ** trade.pip_scale

            # Adjust the direction of pips for target and loss based on trade direction
            if trade.trade_direction == 'SELL':
                target_pips *= -1
                loss_pips *= -1
            elif trade.trade_direction == 'BUY':
                pass  # The direction remains the same for a BUY trade

            message = f"\nPair:    {trade.trade_direction}, {trade.pair}" \
                      f"\nEntry:   {trade.entry_price:.4f}, Current: {self.current_price:.4f}" \
                      f"\nTarget:  {trade.target_price:.4f} to target: {target_pips:.1f} pips, " \
                      f"\nLoss:    {trade.stop_loss:.4f} to stop: {loss_pips:.1f} pips" \
                      f"\nChange:  {change_in_price:.4f} {change_in_price / trade.pip_value * 10 ** trade.pip_scale:.1f} pips" \
                      f"\nUpdated: {time.strftime('%H:%M:%S', time.localtime())}"

            print(message)
            self.telegram_messager.send_telegram_message(message)

            should_close_trade = (trade.trade_direction == 'BUY' and (
                    self.current_price >= trade.target_price or self.current_price <= trade.stop_loss)) or \
                                 (trade.trade_direction == 'SELL' and (
                                         self.current_price <= trade.target_price or self.current_price >= trade.stop_loss))

            if should_close_trade:
                action_type = "Take profit hit" if self.current_price >= trade.target_price else "Stop loss hit"
                relevant_price = trade.target_price if self.current_price >= trade.target_price else trade.stop_loss
                action = (
                    f"{action_type} for {trade.pair}."
                    f"\nEntry: {trade.entry_price:.4f}, Change: {change_in_price:.4f}"
                    f"\nRelevant Price: {relevant_price:.4f}. Trade closed."
                )
                print(action)
                self.telegram_messager.send_telegram_message(action)
                trades_to_remove.append(trade)

        for trade in trades_to_remove:
            self.open_trades.remove(trade)
        time_since_last_check = time_passed - self.last_cache_update_time

        if len(self.open_trades) < self.max_open_trades and time_since_last_check >= 6:
            self.find_new_trade_candidates(currencies, custom_intervals, indicator_names)
            self.last_cache_update_time = time_passed  # Update last cache update time