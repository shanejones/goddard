
# --- Do not remove these libs ---

from functools import reduce
from freqtrade.strategy import IStrategy, stoploss_from_open
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.persistence import Trade
from datetime import datetime, timedelta
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta

def to_minutes(**timdelta_kwargs):
    return int(timedelta(**timdelta_kwargs).total_seconds() / 60)

class Apollo11(IStrategy):
    timeframe = "15m"

    # Stoploss¢
    stoploss = -0.20
    startup_candle_count: int = 480
    trailing_stop = False
    use_custom_stoploss = True
    use_sell_signal = False


    # signal controls
    buy_signal_1 = True
    buy_signal_2 = True

    # Indicator values:

    # Signal 1
    s1_ema_xs = 3
    s1_ema_sm = 5
    s1_ema_md = 10
    s1_ema_xl = 50
    s1_ema_xxl = 200


    # Signal 2
    s2_ema_input = 50
    s2_ema_offset_input = -1

    s2_bb_sma_length = 49
    s2_bb_std_dev_length = 64
    s2_bb_lower_offset = 3

    s2_fib_sma_len = 50
    s2_fib_atr_len = 14

    s2_fib_lower_value = 4.236

    
    @property
    def protections(self):
        return [
            {
                "method": "CooldownPeriod",     # Don't enter a trade right after selling a trade.
                "stop_duration": to_minutes(hours=1, minutes=15)
            },
            {
                "method": "MaxDrawdown",        # Stop trading if max-drawdown is reached.
                "lookback_period": to_minutes(hours=12),
                "trade_limit": 20,              # Considering all pairs that have a minimum of 20 trades
                "stop_duration": to_minutes(hours=1),
                "max_allowed_drawdown": 0.2     # If max-drawdown is > 20% this will activate
            },
            {
                "method": "StoplossGuard",      # Stop trading if a certain amount of stoploss occurred within a certain time window.
                "lookback_period": to_minutes(hours=6),
                "trade_limit": 4,               # Considering all pairs that have a minimum of 4 trades
                "stop_duration": to_minutes(minutes=30),
                "only_per_pair": False          # Looks at all pairs
            },
            {
                "method": "LowProfitPairs",     # Lock pairs with low profits
                "lookback_period": to_minutes(hours=1, minutes=30),
                "trade_limit": 2,               # Considering all pairs that have a minimum of 2 trades
                "stop_duration": to_minutes(hours=15),
                "required_profit": 0.02         # If profit < 2% this will activate for a pair
            },
            {
                "method": "LowProfitPairs",     # Lock pairs with low profits
                "lookback_period": to_minutes(hours=6),
                "trade_limit": 4,               # Considering all pairs that have a minimum of 4 trades
                "stop_duration": to_minutes(minutes=30),
                "required_profit": 0.01         # If profit < 1% this will activate for a pair
            }
        ]



    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Adding EMA's into the dataframe
        dataframe['s1_ema_xs'] = ta.EMA(dataframe, timeperiod=self.s1_ema_xs)
        dataframe['s1_ema_sm'] = ta.EMA(dataframe, timeperiod=self.s1_ema_sm)
        dataframe['s1_ema_md'] = ta.EMA(dataframe, timeperiod=self.s1_ema_md)
        dataframe['s1_ema_xl'] = ta.EMA(dataframe, timeperiod=self.s1_ema_xl)
        dataframe['s1_ema_xxl'] = ta.EMA(dataframe, timeperiod=self.s1_ema_xxl)


        s2_ema_value = ta.EMA(dataframe, timeperiod=self.s2_ema_input)
        s2_ema_xxl_value = ta.EMA(dataframe, timeperiod=200)
        dataframe['s2_ema'] = s2_ema_value - s2_ema_value * self.s2_ema_offset_input
        dataframe['s2_ema_xxl_off'] = s2_ema_xxl_value - s2_ema_xxl_value * self.s2_fib_lower_value
        dataframe['s2_ema_xxl'] = ta.EMA(dataframe, timeperiod=200)

        s2_bb_sma_value = ta.SMA(dataframe, timeperiod=self.s2_bb_sma_length)
        s2_bb_std_dev_value = ta.STDDEV(dataframe, self.s2_bb_std_dev_length)
        dataframe['s2_bb_std_dev_value'] = s2_bb_std_dev_value
        dataframe['s2_bb_lower_band'] = s2_bb_sma_value - (s2_bb_std_dev_value * self.s2_bb_lower_offset)

        s2_fib_atr_value = ta.ATR(dataframe, timeframe=self.s2_fib_atr_len)
        s2_fib_sma_value = ta.SMA(dataframe, timeperiod=self.s2_fib_sma_len)

        dataframe['s2_fib_lower_band'] = s2_fib_sma_value - s2_fib_atr_value * self.s2_fib_lower_value

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # basic buy methods to keep the strategy simple
        
        dataframe.loc[
        (
            (self.buy_signal_1 is True) &
            (dataframe['close'] < dataframe['s1_ema_xxl']) &
            (qtpylib.crossed_above(dataframe['s1_ema_sm'], dataframe['s1_ema_md'])) & 
            (dataframe['s1_ema_xs'] < dataframe['s1_ema_xl']) & 
            (dataframe['volume'] > 0)
        ),
        ['buy', 'buy_tag']] = (1, 'buy_signal_1')

        dataframe.loc[
        (
            (self.buy_signal_2 is True) &
            (qtpylib.crossed_above(dataframe['s2_fib_lower_band'], dataframe['s2_bb_lower_band'])) &
            (dataframe['close'] < dataframe['s2_ema']) &
            (dataframe['volume'] > 0)
        ),
        ['buy', 'buy_tag']] = (1, 'buy_signal_2')


        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # This is essentailly ignored as we're using strict ROI / Stoploss / TTP sale scenarios
        dataframe.loc[(), "sell"] = 0
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        if (current_profit > 0.2):
            return 0.04
        elif (current_profit > 0.1):
            return 0.03
        elif (current_profit > 0.06):
            return 0.02
        elif (current_profit > 0.03):
            return 0.01

        return 1