class Trade:
    def __init__(self, pair, entry_price, stop_loss, target_price, time_frame, trade_direction,
                 lot_size, trade_amount_in_dollars, potential_profit_or_loss, pip_value, pip_scale):
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
        self.pip_scale = pip_scale