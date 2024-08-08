import matplotlib.pyplot as plt
import pandas as pd
import requests
import os
import pickle
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
from passwords import  alpha_v_key_imported
from strategy_classes import SMA_21_55,RSI_70_30,RSI_80_20,SMA_21_89,SMA_9_21

def main(force_load = False):
    #strategy variables
    initial_balance = 1_000_000
    #position size functionality still needs implementing
    position_size = [1]
    #leverage functionality still needs implementing
    leverage = [1]
    fee = 0.0002
    file_path = "raw_data.csv"
    sort_metric = "Return [%]"
    #any strategies without n trades will not be shown
    trade_num_threshold = 1
    #number of results to return
    winners = 5
    #Check if data already downloaded or if forced load
    if not os.path.exists(file_path) or force_load:
        print("Downloading data...")
        collected_data = collector(file_path)
        print("Download Complete")
    else:
        with open(file_path,"rb") as file:
            print("Loading saved data...")
            collected_data = pickle.load(file)
            print("Load complete")
            print(f"Collected Data:\n{collected_data}")
    #convert data to diff timeframes
    aggregated_data = aggregator(collected_data)
    #test different strategies and return the best
    results,final_dict,winner_list = strategy_test(aggregated_data,leverage,position_size,initial_balance,fee,sort_metric,winners,trade_num_threshold)
    #show results
    visualise_data(results, winner_list,sort_metric,final_dict)

def collector(file_path):
    #list of all assets to test
    tickers = ["MSFT","TSLA"]
    #api key
    alpha_v_key = alpha_v_key_imported
    #interval
    interval = "1min"
    #store outputs as a dict
    master_dict = {}
    #months to test
    months = ["2024-01","2024-02","2024-03"]
    #make multiple requests
    for ticker in tickers:
        #initiate empty df for results
        full_single_ticker_data = []
        #for every month
        for month in months:
            #make the request
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval={interval}&month={month}&outputsize=full&apikey={alpha_v_key}"
            #store response
            response = requests.get(url)
            #get response as json
            data = response.json()

            #check if already in data
            if f'Time Series ({interval})' in data:
                df = pd.DataFrame(data[f'Time Series ({interval})']).T
                # add the current month to full single ticker list
                full_single_ticker_data.append(df)
            else:
                print(f"Data for {ticker} in {month} is not available.")
        
        # concatenate all dataframes in the list
        if full_single_ticker_data:
            full_single_ticker_data = pd.concat(full_single_ticker_data)
        else:
            full_single_ticker_data = pd.DataFrame()

        #sort the data by timestamp
        full_single_ticker_data =full_single_ticker_data.sort_index()
        full_single_ticker_data.index = pd.to_datetime(full_single_ticker_data.index)
        full_single_ticker_data.rename(columns={"1. open":"Open","2. high":"High","3. low":"Low","4. close":"Close","5. volume": "Volume"},inplace=True)
        
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
        for col in df.columns:
            df[col] = pd.to_numeric(df[col],errors = "coerce")
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
    #sort the results in order trim to number of winners set
    winner_list =  sorted(results_unsorted, key=lambda x: x[1], reverse=True)[:winners]
    #store dictionaries of the Kpis for graphs
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
    print(results)
    return(results,final_dict,winner_list)



def visualise_data(results, winner_list,sort_metric,final_dict):
    #for every k,v  pair
    winner_results = {}
    for name, score in winner_list:
         winner_results[name] = results[name]#[sort_metric]
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