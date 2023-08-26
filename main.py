import uuid
from collector import Pairs, Retrieve
from analyzer import Analysis
from logger import Logger
from trader import Trader

if __name__ == "__main__":

    symbols = ["EURUSD", "USDJPY", "AUDUSD", "GBPUSD", "EURRUB", "GBPJPY", "USDCAD",]
    screener = "forex"
    exchange = "FX_IDC"
    trade_logger = Logger("/Users/stenuuesoo/Ladna/ptoq/logs")

    for symbol in symbols:
        trade_id = str(uuid.uuid4())[:8]
        # 1. Instantiate Pairs
        pairs_instance = Pairs(symbol, screener, exchange)

        # 2. Fetch all necessary data.
        all_data = Retrieve(pairs_instance).data

        # 3. Analyze the fetched data based on rules.
        analysis_component = Analysis(all_data)
        trade_decision = analysis_component.decide_trade_action()

        # 4. Log data
        logged_data = trade_logger.log_trade_decision(symbol,trade_id, trade_decision, all_data)

        print(f"Trade decision for {symbol}: {trade_decision}")
        trader = Trader(trade_id)