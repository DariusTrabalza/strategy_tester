import talib as ta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover,resample_apply
from backtesting.test import SMA, GOOG


#strategy permanent variables
data = GOOG
cash = 1_000_000
fee = 0.0002
#still needs implenting
leverage = 0.5 
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


def main():
    bt= Backtest(data,RSI_70_30,cash = cash, commission  = fee)
    stats = bt.run()
    bt.plot()

class RSI_70_30(Strategy):
    #strategy variables
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    def init(self):
        self.rsi = self.I(ta.RSI,self.data.Close,self.rsi_window)
        
    def next(self):
        #buy cond
        if (crossover(self.rsi,self.upper_bound)):
            if self.position.is_short or not self.position:
                self.position.close()
                self.buy()
        #sell cond
        elif (crossover(self.lower_bound,self.rsi)):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell()

class RSI_80_20(Strategy):
    #strategy variables
    upper_bound = 80
    lower_bound = 20
    rsi_window = 14

    def init(self):
        self.rsi = self.I(ta.RSI,self.data.Close,self.rsi_window)
        
    def next(self):
        #buy cond
        if (crossover(self.rsi,self.upper_bound)):
            if self.position.is_short or not self.position:
                self.position.close()
                self.buy()
        #sell cond
        elif (crossover(self.lower_bound,self.rsi)):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell()

class RSI_multi_timeframe(Strategy):
    #strategy variables
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    def init(self):
        self.daily_rsi = self.I(ta.RSI,self.data.Close,self.rsi_window)
        self.weekly_rsi = resample_apply("2D",ta.RSI,self.data.Close,self.rsi_window)
    
    def next(self):
        #buy cond
        if (crossover(self.daily_rsi,self.upper_bound) and self.weekly_rsi[-1]  > self.lower_bound):
            if self.position.is_short or not self.position:
                self.position.close()
                self.buy()
        #sell cond
        elif (crossover(self.lower_bound,self.daily_rsi) and self.weekly_rsi[-1]  <  self.upper_bound ):
            if self.position.is_long or not self.position:
                self.position.close()
                self.sell()
           
if __name__ == "__main__":
    main()