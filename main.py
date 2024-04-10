#This program will take trading strategies and test them on every asset in a list and on every timeframe.

#Features
#import all data one at a time
#have functions that are trading strategies
#take each assets many datasets of different timeframes and check the how it performs.
#be able to do within a certain time span such as monday to friday or 9am to 5pm


#graphs should show different timespans e.g how it performed in the last week, last month, this year, 2 years ago, 5 years to today.


#PICK UP NOTES****

#figure out how to get all the data ready to be visualised now just need finish the visualisation. maybe as a dashboard
#FYI the terminal doesnt print out the entire final dict i think its too big. the data is all there

#reload the data with all months
#plot top N strategies onto one graph with benchmarks such as S and P and BTC already on there to compare
#create dashboard of each strategy with a chart for each single kpi vs all timeframes together
#at the top of dashboard should be which a list of kpi's and which strategy performed best for each one



#need to figure out the final sorting and the visualisation
#then add more strategies 


#maybe the tables can be organisable by metric
#cells with positive values should be green  and bad red. or heat map vibe

#Best version needs:
#do i need to add in multiple api calls directly to exchanges in order to get reliable 1 min data?
#leverage 
#stop loss and take profit 
#optimised hyperparameters
#test strategies within time windows
#please create some unit tests


from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt
import pandas as pd
import pandas_ta as ta
import requests
import numpy as np
import os
import pickle
import seaborn as sns

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA

from strategy_classes import SMA_21_55,RSI_70_30,RSI_80_20,SMA_21_89,SMA_9_21




def main(force_load = False):

    initial_balance = 1_000_000
    position_size = [1]
    leverage = [1]
    fee = 0.0002
    file_path = "raw_data.csv"
    sort_metric = "Return [%]"
    #any strategies without n trades will not be shown
    trade_num_threshold = 1
    #number of results to return
    winners = 2


    #Check if data already downloaded or if forced load/ maybe put this into a function
    if not os.path.exists(file_path) or force_load:
        print("Downloading data...")
        collected_data = collector(file_path)
        print("Download Complete")

    else:
        with open(file_path,"rb") as file:
            print("Loading saved data...")
            collected_data = pickle.load(file)
            print("Load complete")


    #convert data to diff timeframes
    aggregated_data = aggregator(collected_data)
    #test different strategies and return the best
    complete_results = strategy_test(aggregated_data,leverage,position_size,initial_balance,fee,sort_metric,winners,trade_num_threshold)
    
    #visualise_data(results,results_list,sort_metric)

def collector(file_path):

    #list of all assets/here can we fetch a request of all available tickers or do we jusjt copy and paste a list
    tickers = ["MSFT","TSLA"]
    #api key
    alpha_v_key = "QJDF8ZZZBBQBTOS9"
    #interval
    interval = "1min"
   
    #store outputs as a dict
    master_dict = {}

    #initiate empty df for results
    #full_single_ticker_data = pd.DataFrame()

    #set months of last 2 years/Eventually this will use a function that generates to a specific amount of data
    months = ["2023-03","2023-04","2023-05","2023-06","2023-07","2023-08","2023-09","2023-10","2023-11","2023-12"]

    #make multiple requests. Let us aim to have 1 year of data initially
    for ticker in tickers:
        #initiate empty df for results
        full_single_ticker_data = pd.DataFrame()
        #for every month
        for month in months:
            #make the request
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval={interval}&month={month}&outputsize=full&apikey={alpha_v_key}"
            #store response
            response = requests.get(url)
            #get response as json
            data = response.json()
           

            #change json to df
            df = pd.DataFrame(data[f'Time Series ({interval})']).T
            
            #add the current month to full single ticker df
            full_single_ticker_data = full_single_ticker_data.append(df)

        #sort the data by timestamp
        full_single_ticker_data =full_single_ticker_data.sort_index()
        full_single_ticker_data.index = pd.to_datetime(full_single_ticker_data.index)
        full_single_ticker_data.rename(columns={"1. open":"Open","2. high":"High","3. low":"Low","4. close":"Close","5. volume": "Volume"},inplace=True)
        #print(f"full single ticker data\n{full_single_ticker_data}")
        #once the full ticker df is complete save it to a dict. keys = tickername, values = df
        master_dict[ticker] = full_single_ticker_data
    #inspect master_df here
    print(f"Master dict Items:\n{master_dict.items()}")

    #save master dict
    with open(file_path,"wb") as file:
        pickle.dump(master_dict, file)


    return(master_dict)
   




def aggregator(collected_data):

    aggregated_data = {}

    #time frame codes
    time_frames = ["5T","10T","15T","20T","30T","45T","1H","2H","3H","4H","12H","1D","2D","3D","1W","1M"]
 
    #for each asset in the master dict
    for asset in collected_data.keys():
        #for each timeframe in list
        for time_frame in time_frames:
            #add aggregated data as values and symbol + timeframe as keys
            aggregated_data[f"{asset}_{time_frame}"] = collected_data[asset].resample(time_frame).agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    
    return(aggregated_data) 



def strategy_test(aggregated_data,leverage,position_size,initial_balance,fee,sort_metric,winners,trade_num_threshold):
    
    strategies = [SMA_21_55,RSI_70_30,RSI_80_20,SMA_21_89,SMA_9_21]
    
    results = {}
    #for every df in aggregated data:
    for df_key,df in aggregated_data.items():
        #remove missing vals
        df = df.dropna()
    
        for i in df.columns:
            df[i] = pd.to_numeric(df[i],errors = "coerce")

        for strat in strategies:
            #create a strategy object
            backtest = Backtest(df,strat,commission = fee, exclusive_orders = True, cash = initial_balance)
            #run backtest and store result
            single_result = backtest.run()
            #convert result to dictionary
            result_dict = single_result.to_dict()
            #add name of df and strategy as key and results as value
            results_key = f"{df_key}_{strat.__name__}"
            
            results[results_key] = result_dict

    #This part is only necessary if i still want to show the best results        
    results_unsorted = [(k,v[sort_metric]) for k, v in results.items() if v["# Trades"] > trade_num_threshold]

    #PREVIOUS METHOD OF ONLY VISUALISING THE TOP N STRATS
    #the lambda function is the part sorting by the specific kpi
    #results_list =  sorted(results_unsorted, key=lambda x: x[1], reverse=True)[:winners]
    results_list =  sorted(results_unsorted, key=lambda x: x[1], reverse=True)
    

    

    #store dictionaries of the Kpis i want to graph
    strategy_metrics = {
        "return_metric": {},
        "buy_and_hold_return_metric" : {},
        "sharpe_ratio_metric" : {},
        "max_drawdown_metric" : {},
        "num_trades_metric" : {},
        "win_rate_metric" : {},
        "average_trade_metric" : {},
        "profit_factor_metric" : {},
        
    }
    #a list of the syntax for the metrics
    #desired_metrics = ["Return [%]", "Buy & Hold Return [%]", "Max. Drawdown [%]", "# Trades", "Win Rate [%]", "Avg. Trade [%]", "Profit Factor", "Sharpe Ratio"]

    #output list of names of dicts
    dicts_name_list = []


    #loop over every asset/timeframe & results
    for key, value in results.items():

        #append to stategy metrics strat names as key and metric score as value
        strategy_metrics["return_metric"][key] = value["Return [%]"]
        strategy_metrics["buy_and_hold_return_metric"][key] = value["Buy & Hold Return [%]"]
        strategy_metrics["sharpe_ratio_metric"][key] = value["Sharpe Ratio"]
        strategy_metrics["max_drawdown_metric"][key] = value["Max. Drawdown [%]"]
        strategy_metrics["num_trades_metric"][key] = value["# Trades"]
        strategy_metrics["win_rate_metric"][key] = value["Win Rate [%]"]
        strategy_metrics["average_trade_metric"][key] = value["Avg. Trade [%]"]
        strategy_metrics["profit_factor_metric"][key] = value["Profit Factor"]

        ticker_single,timeframe_single,strat_single= get_ticker_timeframe_strat(key)

        #check if name already in dict_name_list
        if (ticker_single,strat_single) not in dicts_name_list:
            dicts_name_list.append((ticker_single,strat_single))

    #final dict ready to be visualised
    final_dict = {}

    #get results and assign the to correct strat ticker combo
    for key, value in results.items():
        #get the shortened version to check against dict_name_list
        ticker_final,timeframe_final,strat_final= get_ticker_timeframe_strat(key)
        #if name is in the dicts_name_list
        if (ticker_final, strat_final) in dicts_name_list:
            #if the sub dict has not been initiated then do that
            if f"{ticker_final}_{strat_final}" not in final_dict:
                final_dict[f"{ticker_final}_{strat_final}"] = {}
            #assign correct results to correct name
            final_dict[f"{ticker_final}_{strat_final}"][timeframe_final] = value
    
    print(final_dict)
    return(final_dict)



def visualise_data(results, results_list,sort_metric):
   
    #for every k,v  pair
    final_results = {}
    for name, score in results_list:
         final_results[name] = results[name]#[sort_metric]
         equity_curve = results[name]["_equity_curve"]
         plt.figure(figsize=(10, 6))
         plt.plot(equity_curve.index, equity_curve['Equity'], label='Equity Curve', color='blue')
         plt.title(f'{name} Equity Curve')
         plt.xlabel('Date')
         plt.ylabel('Equity [$]')
         plt.legend()
         plt.grid(True)
         plt.tight_layout()
         plt.show()

def get_ticker_timeframe_strat(string):
        ticker_ = ""
        timeframe_ = ""
        strat_ = ""
        #get the ticker store everything in string until first "_"
        for letter in string:
            if letter == "_":
                break
            else:
                ticker_ += letter
        #get timeframe. store everything in string from first "_" stop at next "_"
        _count = 0
        for letter in string:
            if _count == 1 and not letter == "_":
                timeframe_ += letter
            if letter =="_":
                _count += 1

        #get strategy. store every part of string after 2nd "_"
        _count = 0
        for letter in string:
            if _count >= 2:
                strat_ += letter
            if letter =="_":
                _count += 1

        
        return(ticker_,timeframe_,strat_)
    

if __name__ == "__main__":
    
    main(force_load=False)