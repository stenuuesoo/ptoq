import json
import uuid
from datetime import datetime

class Logger:
    def __init__(self, base_path):
        self.base_path = base_path

    def log_trade_decision(self, symbol, trade_decision, indicators):
        # Generating unique trade_id
        trade_id = f"{symbol.lower()}_{str(uuid.uuid4())[:8]}"

        # Extracting decision details for filename
        time_frame = list(trade_decision.keys())[0]
        decision_data = trade_decision[time_frame]
        decision = decision_data['action']
        confidence_score = decision_data['confidence_score']
        probability_score = decision_data['probability_score']
        strategies = decision_data['reasoning']

        # Forming the filename
        current_time = datetime.now().strftime('%Y_%m_%d_%H_%M')
        filename = f"{symbol.lower()}_{time_frame}_{decision}_{confidence_score}_{probability_score}_{current_time}.txt"
        log_file_path = f"{self.base_path}/{filename}"

        # Extract indicators for specific timeframe (e.g., "1h")
        timeframe_indicators = indicators["1h"]["indicators"]

        # Log data with indicators at the same level as deciders
        log_data = {
            'symbol': symbol,
            'timeframe': time_frame,
            'run_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trade_id': trade_id,
            'confidence_score': confidence_score,
            'success_probability': probability_score,
            'strategies': strategies,
            'deciders': indicators["1h"]["ma"],  # updated this line
            'indicators': timeframe_indicators  # added this line
        }

        # Write to the log file
        with open(log_file_path, 'w') as file:  # 'w' means write mode
            file.write(json.dumps(log_data, indent=4))
            file.write("\n")

        return log_data
