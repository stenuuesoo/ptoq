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