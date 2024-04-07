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


class SMA_21_55(Strategy):

    #strategy variables
    ma1 = 21
    ma2 = 55
    


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
                self.buy()

        #sell cond
        elif crossover(self.ma2,self.ma1):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell()

class SMA_9_21(Strategy):

    #strategy variables
    ma1 = 9
    ma2 = 21
    


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
                self.buy()

        #sell cond
        elif crossover(self.ma2,self.ma1):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell()

class SMA_21_89(Strategy):

    #strategy variables
    ma1 = 21
    ma2 = 89
    


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
                self.buy()

        #sell cond
        elif crossover(self.ma2,self.ma1):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell()

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
    bt= Backtest(data,RSI_70_30,cash = cash, commission  = fee)
    stats = bt.run()
    bt.plot()


class RSI_70_30(Strategy):

    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    def init(self):
        self.rsi = self.I(ta.RSI,self.data.Close,self.rsi_window)
        
    def next(self):
        if (crossover(self.rsi,self.upper_bound)):
            if self.position.is_short or not self.position:
                self.position.close()
                self.buy()
        
        elif (crossover(self.lower_bound,self.rsi)):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell()


class RSI_80_20(Strategy):

    upper_bound = 80
    lower_bound = 20
    rsi_window = 14

    def init(self):
        self.rsi = self.I(ta.RSI,self.data.Close,self.rsi_window)
        
    def next(self):
        if (crossover(self.rsi,self.upper_bound)):
            if self.position.is_short or not self.position:
                self.position.close()
                self.buy()
        
        elif (crossover(self.lower_bound,self.rsi)):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell()




class RSI_multi_timeframe(Strategy):

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