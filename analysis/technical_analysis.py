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

    def calculate_analysis_score(self):
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