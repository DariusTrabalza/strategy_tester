#This program will take trading strategies and test them on every asset in a list and on every timeframe.

#Features
#import all data one at a time
#have functions that are trading strategies
#take each assets many datasets of different timeframes and check the how it performs.
#be able to do within a certain time span such as monday to friday or 9am to 5pm


#graphs should show different timespans e.g how it performed in the last week, last month, this year, 2 years ago, 5 years to today.


#pick up notes
#reset the data set with both tickers and more months back
#plot top N strategies onto one graph with benchmarks such as S and P and BTC already on there to compare


#need to figure out the final sorting and the visualisation
#then add more strategies 
#how do i store all of the results in a digestable way?
#maybe a dataframe each for strategy with timeframe x axis and metrics on the y axis
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
    results,results_list = strategy_test(aggregated_data,leverage,position_size,initial_balance,fee,sort_metric,winners)
    
    visualise_data(results,results_list,sort_metric)

def collector(file_path):

    #list of all assets/here can we fetch a request of all available tickers or do we jusjt copy and paste a list
    tickers = ["MSFT"]#,"TSLA"]
    #api key
    alpha_v_key = "QJDF8ZZZBBQBTOS9"
    #interval
    interval = "1min"
   
    #store outputs as a dict
    master_dict = {}

    #initiate empty df for results
    full_single_ticker_data = pd.DataFrame()

    #set months of last 2 years/Eventually this will use a function that generates to a specific amount of data
    months = ["2023-03","2023-04"]#,"2023-05","2023-06","2023-07","2023-08","2023-09","2023-10","2023-11","2023-12"]}

    #make multiple requests. Let us aim to have 1 year of data initially
    for ticker in tickers:
        #for every month
        for month in months:
            #make the request
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval={interval}&month={month}&outputsize=full&apikey={alpha_v_key}"
            #store response
            response = requests.get(url)
            #get response as json
            data = response.json()
            print(f"This is the json file\n{data}")

            #change json to df
            df = pd.DataFrame(data[f'Time Series ({interval})']).T
            print(f"df after change json line: {df}")
            #add the current month to full single ticker df
            full_single_ticker_data = full_single_ticker_data.append(df)

        #sort the data by timestamp
        full_single_ticker_data =full_single_ticker_data.sort_index()
        full_single_ticker_data.index = pd.to_datetime(full_single_ticker_data.index)
        full_single_ticker_data.rename(columns={"1. open":"Open","2. high":"High","3. low":"Low","4. close":"Close","5. volume": "Volume"},inplace=True)
        print(f"full single ticker data\n{full_single_ticker_data}")
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



def strategy_test(aggregated_data,leverage,position_size,initial_balance,fee,sort_metric,winners):
    
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
            #print(single_result)
            #convert result to dictionary
            result_dict = single_result.to_dict()
            #add name of df and strategy as key and results as value
            results_key = f"{df_key}_{strat.__name__}"
            results[results_key] = result_dict

        #NOTE this is how to refer to a specific result
        #print(results[results_key]["Return [%]"])
            
    results_unsorted = [(k,v[sort_metric]) for k, v in results.items()]

    results_list =  sorted(results_unsorted, key=lambda x: x[1], reverse=True)[:winners]
    #print(results_list)
  
    return results,results_list



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



    #print(final_results)
        #what do i want to do here?
         # i have name and dict of results within a dict
         #do i need to plot a graph
         #should i show/save the trading graph of them?
         # i guess i want to plot the equity curves of all of them?
    '''
         plt.plot(final_results[name]["_equity_curve"].dropna())
         plt.title(f"{name} Equity Curve")
         plt.xlabel("Time")
         plt.ylabel("Equity")
         plt.legend()
         plt.show()

        '''
    '''
    plt.title("Top 3 Strategies by Sharpe Ratio - Equity Curve")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.legend()
    plt.show()
    '''
    #list of timespanss

    #for every dict in results list of dictionaries:
        #for every element of the dict:
            #for every time span in list of timespans:
                #if ordered == true:
                    #sort(#plot the results of the asset on the timespan)
                
                
                #else:
                    #plot the results of the asset on the timespan
    
if __name__ == "__main__":
    
    main(force_load=False)