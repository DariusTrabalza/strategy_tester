'''
#strategies to implement

all ma crosses
all ema crosses
RSI:
    -buy if oversold, sell if overbought (optimized values)
    -buy if oversold for x candles and sell if overbought for x candles
    -higher timeframe confluence
    -control zones
    -control zones with higher time frame confluence
    -position to EMA/MA of RSI + confluence
    -divereges + confluence
    -high and low structure on the RSI

MACD:
        -Cross overs of signal and macd
        -cross overs + positive or negative
        -divergence
        -histogram highs and low structure
        

stops: 
    -arbitrary value
    -ATR
    -Bollinger bands
    -Mas/EMAs
    -break of structure(highs and lows)
    -horizontals breakage
    -
take profits:

'''



import matplotlib.pyplot as plt
import pandas as pd
#import pandas_ta as ta
import requests
import numpy as np
import talib as ta
import seaborn as sns


from backtesting import Backtest, Strategy
from backtesting.lib import crossover,resample_apply
from backtesting.test import SMA, GOOG


#notes
##can add in leverage using the margin arguments  0.02 == 50x lev


data = GOOG
cash = 1_000_000
fee = 0.0002
leverage = 0.5 # is this 2x leverage?
sl = 0.95


class MySMAStrategy(Strategy):

    #strategy variables
    ma1 = 21
    ma2 = 50
    sl = 0.95
    tp = 1.05


    def init(self):
        price = self.data.Close
        self.ma1 = self.I(SMA,price,self.ma1)
        self.ma2 = self.I(SMA,price,self.ma2)
        

    def next(self):

        price = self.data.Close[-1]
        #buy cond
        if crossover(self.ma1,self.ma2):
            if self.position.is_short or not self.position:
                self.position.close()
                self.buy(sl = self.sl * price)

        #sell cond
        elif crossover(self.ma2,self.ma1):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell(sl = (price + ((1 - self.sl) * price)))


'''
#optimisation function
                
def optim_sma(series):
    if series["# Trades"] < 5:
        return -1
    else:
        return series["Sharpe Ratio"]


def main():
    bt_sma = Backtest(data,MySMAStrategy,cash = cash, commission  = fee)
    stats_sma = bt_sma.optimize(
        ma1 = range(1,199,1),
        ma2 = range(2,200,1),
        sl = [0.98,0.97,0.95,0.93,0.90,0.80,0.7,0.6,0.5,0.4,0.3,0.2,0.1],
        tp = [1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9],
        maximize = optim_sma,
        constraint = lambda x: x.ma1 > x.ma2
    )

'''
def main():
    bt= Backtest(data,MySMAStrategy,cash = cash, commission  = fee)
    stats = bt.run()
    bt.plot()







class RSI_oscillator(Strategy):

    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    def init(self):
        #14 is window
        self.daily_rsi = self.I(ta.RSI,self.data.Close,self.rsi_window)
        self.weekly_rsi = resample_apply("2D",ta.RSI,self.data.Close,self.rsi_window)
    
    def next(self):
        if (crossover(self.daily_rsi,self.upper_bound) and self.weekly_rsi[-1]  > self.lower_bound):
            if self.position.is_short or not self.position:
                self.position.close()
                self.buy()
        
        elif (crossover(self.lower_bound,self.daily_rsi) and self.weekly_rsi[-1]  <  self.upper_bound ):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell()
           

'''
bt = Backtest(data,RSI_oscillator,cash = cash,commission = fee)

stats = bt.run()
print(stats)
bt.plot()


'''


if __name__ == "__main__":
    main()