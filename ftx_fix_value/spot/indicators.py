from os import close
import pandas as pd
import time
import decimal
from datetime import datetime
import pytz
import csv
import account
from ta.volatility import BollingerBands, AverageTrueRange

def bb_trading_signal(pair, timeframe): 
    
    """ Last close price cross lower/upper bollinger band = buy / sell signal

    Args:
        pair ([str]): [trading pair]
        timeframe ([str]): [price feed timeframe]

    Returns:
        [str]: [return sell when close price cross upper bollinger band]
    """
    exchange = account.exchange
    
    bars = exchange.fetch_ohlcv(pair, timeframe, limit=21) # ย้อนหลังกี่แท่ง
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    bb_indicator = BollingerBands(df['close'])
    bb_upper = bb_indicator.bollinger_hband()
    bb_lower = bb_indicator.bollinger_lband()
    
    last_close_price = df.iloc[-1]['close']
    bb_upper_price = bb_upper.iloc[-1]
    bb_lower_price = bb_lower.iloc[-1]

    if last_close_price > bb_upper_price:
        print('Last close price {} > BB_upper_band {}'.format(last_close_price, bb_upper_price))
        print('Sell signal triggered')
        return "sell"
    elif last_close_price < bb_lower_price:
        print('Last close price {} < BB_lower_band {}'.format(last_close_price, bb_lower_price))
        print('buy signal triggered')
        return "buy"
    else:
        return print("BB_lower_band {} < Last close price {} < BB_upper_band {} : Waiting for signal".format(bb_lower_price, last_close_price, bb_upper_price))
    
def atr_signal(pair, timeframe):
    exchange = account.exchange
    
    bars = exchange.fetch_ohlcv(pair, timeframe, limit=15) # 
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    atr = AverageTrueRange(df['high'], df['low'], df['close'])
    atr_value = atr.average_true_range().iloc[-1]

    return atr_value

def atr_adjust(pair, timeframe, fix_value, price):
    exchange = account.exchange
    
    bars = exchange.fetch_ohlcv(pair, timeframe, limit=15) # 
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    atr = AverageTrueRange(df['high'], df['low'], df['close'])
    atr_value = atr.average_true_range().iloc[-1]

    atr_adjust_range = atr_value/price * fix_value

    return atr_adjust_range

#print(atr_adjust('SRM/USD', '4h', 10000, 2.3))