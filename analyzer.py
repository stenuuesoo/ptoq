import random

class Analysis:
    # RSI constants
    RSI_MIN = 30
    RSI_MAX = 70

    # MACD constants
    MACD_SIGNAL_DIFF_BUY = 0.01
    MACD_SIGNAL_DIFF_SELL = -0.01

    # Moving Averages constants
    MA_SHORT_TERM = 20  # Period for short-term moving average (SMA, EMA)
    MA_LONG_TERM = 50  # Period for long-term moving average (SMA, EMA)

    # Oscillators
    STOCHASTIC_OSCILLATOR_MIN = 20
    STOCHASTIC_OSCILLATOR_MAX = 80

    # Weights for each indicator
    INDICATOR_WEIGHTS = {
        "MA": 2000,
        "RSI": 1000,
        "MACD": 1000,
        "BB": 1000,
        "Stoch.RSI.K": 1000,
        "ADX": 1000,
        "UO": 1000,
        "CCI20": 1000
    }

    def __init__(self, data):
        self.data = data

    def decide_trade_action(self):
        decisions = {}
        for timeframe, values in self.data.items():
            action = 'HOLD'
            direction_scores = {"BUY": 0, "SELL": 0, "HOLD": 0}
            ma_value = values["ma"]['RECOMMENDATION']
            decider_indicators = values["indicators"]
            reasoning = []

            # Moving Averages Logic
            if ma_value == 'STRONG_BUY':
                reasoning.append("MA: STRONG BUY")
                direction_scores["BUY"] += self.INDICATOR_WEIGHTS["MA"]
            elif ma_value == 'BUY':
                reasoning.append("MA: BUY")
                direction_scores["BUY"] += 0.5 * self.INDICATOR_WEIGHTS["MA"]
            elif ma_value == 'STRONG_SELL':
                reasoning.append("MA: STRONG SELL")
                direction_scores["SELL"] += self.INDICATOR_WEIGHTS["MA"]
            elif ma_value == 'SELL':
                reasoning.append("MA: SELL")
                direction_scores["SELL"] += 0.5 * self.INDICATOR_WEIGHTS["MA"]
            else:
                reasoning.append("MA: HOLD")

            # RSI Logic
            if decider_indicators['RSI'] < self.RSI_MIN:
                reasoning.append(f"RSI is below {self.RSI_MIN}")
            elif decider_indicators['RSI'] > self.RSI_MAX:
                reasoning.append(f"RSI is above {self.RSI_MAX}")

            # MACD Logic
            if decider_indicators['MACD.macd'] > self.MACD_SIGNAL_DIFF_BUY:
                reasoning.append("MACD is above the signal line")
            elif decider_indicators['MACD.macd'] < self.MACD_SIGNAL_DIFF_SELL:
                reasoning.append("MACD is below the signal line")

            # Bollinger Bands Logic
            if decider_indicators['close'] > decider_indicators['BB.upper']:
                reasoning.append("Price is above Bollinger Band upper limit")
            elif decider_indicators['close'] < decider_indicators['BB.lower']:
                reasoning.append("Price is below Bollinger Band lower limit")

            # Stochastic Oscillator Logic
            if decider_indicators['Stoch.RSI.K'] < self.STOCHASTIC_OSCILLATOR_MIN:
                reasoning.append("Stochastic Oscillator is in oversold region")
            elif decider_indicators['Stoch.RSI.K'] > self.STOCHASTIC_OSCILLATOR_MAX:
                reasoning.append("Stochastic Oscillator is in overbought region")

            # ADX Logic
            if decider_indicators['ADX'] > 25:
                reasoning.append("Strong trend strength (ADX)")
            elif decider_indicators['ADX'] < 20:
                reasoning.append("Weak trend strength (ADX)")

            # UO (Ultimate Oscillator) Logic
            if decider_indicators['UO'] > 70:
                reasoning.append("UO indicates overbought conditions")
            elif decider_indicators['UO'] < 30:
                reasoning.append("UO indicates oversold conditions")

            # CCI20 (Commodity Channel Index) Logic
            if decider_indicators['CCI20'] > 100:
                reasoning.append("CCI indicates overbought conditions")
            elif decider_indicators['CCI20'] < -100:
                reasoning.append("CCI indicates oversold conditions")

            # Normalize scores
            total_score = sum(direction_scores.values())
            normalized_scores = {k: v / total_score for k, v in direction_scores.items() if total_score != 0}

            # Determine action based on the highest score
            action = max(direction_scores, key=direction_scores.get)

            # Compute confidence and probability
            confidence_score = int(normalized_scores[action] * 100)
            probability_score = normalized_scores[action]  # This already gives a value between 0 and 1

            decisions[timeframe] = {
                'action': action,
                'reasoning': reasoning,
                'confidence_score': confidence_score,
                'probability_score': probability_score
            }
        return decisions


