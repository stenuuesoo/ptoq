import json
import time
from tradingview_ta import Interval
from farm.trader import Trader

if __name__ == "__main__":
    with open('config.json', 'r') as f:
        config = json.load(f)

    custom_intervals = {key: getattr(Interval, value) for key, value in config['custom_intervals'].items()}
    indicator_names = config['indicator_names']
    min_score = config['min_score']
    token = config['token']
    chat_id = config['chat_id']
    currencies = config['currencies']

    trader = Trader(min_score, currencies, custom_intervals, indicator_names, token, chat_id)
    trader.analysis_cache = {(trade['symbol'], trade['time_frame']): trade for trade in trader.potential_trades}

    while True:
        time_passed = time.process_time()
        trader.execute_trades()
        time.sleep(600)
        trader.update_open_trades(currencies, custom_intervals, indicator_names, time_passed)
