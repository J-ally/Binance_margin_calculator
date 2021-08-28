# -*- coding: utf-8 -*-

"""
Created on Sat 21 august 2021
@author: Jaly
"""

import os
from binance.client import Client
import pandas as pd

api_key = os.getenv('binance_api_key')
api_secret = os.getenv('binance_private_key')
client = Client(api_key, api_secret)

### FUNCTIONS

def get_account_balances (client_keys = client) :
    """
    in : client connexion key for binance API
    out : returns a list of dict containing for each coin holded on binance the amount of free and locked coins
    """
    detail = client_keys.get_account()
    detail_balances = detail["balances"]
    balances = []
    for i in range (len (detail_balances)) :
        if float(detail_balances[i]['free']) != 0.0 or  float(detail_balances[i]['locked']) != 0.0 :
            balances.append (detail_balances[i])
    return pd.DataFrame(balances)
#print(get_account_balances())

def get_tradable_symbols (client_keys = client) :
    """
    in : client connexion key for binance API
    out : all the tradable cyrptopairs available on binance
    """
    exchange_info = client_keys.get_exchange_info()
    tradable_symbols = []
    for s in exchange_info['symbols']:
        tradable_symbols.append(s['symbol'])
    return tradable_symbols
#print(get_tradable_symbols())
    
def get_trades_info (pair:str, client_key = client) :
    """
    in : pair : the pair in question, client connexion key for binance API
    out : returns the dataframe of all the orders of the cryptopair or an empty dataframe
    """
    try : 
        orders = client_key.get_all_orders(symbol= pair , limit=20)
    except :
        df_empty = pd.DataFrame({'A' : []})
        return ( df_empty )
    return pd.DataFrame(orders)
#print(get_trades_info('ADABNB'))

def is_pair_traded (crypto : str) :
    """
    in : crypto : the name of the crypto,client connexion key for binance API
    out : returns a list of the traded crpto/pair traded by the account
    """
    crypto_pairs = [crypto+'BNB', crypto+'BTC', crypto+'USDT',crypto+'EUR']
    traded_pairs = []
    for i in range (len(crypto_pairs)) :
        # print(i, get_trades_info(crypto_pairs[i]))
        trade_info = get_trades_info(crypto_pairs[i])
        if trade_info.empty :
            pass
        else :
            traded_pairs.append(crypto_pairs[i])
    return (traded_pairs)
#print(is_pair_traded('ALGO'))

def get_market_price (pair:str, time:int, client_key = client) :
    """
    in : pair : the pair in question, time in unix valor, and client connexion key for binance API
    out : returns the value of the price of the cryptopair when the kline opened at
    """
    historic_price = client_key.get_historical_klines (pair, interval = '1m', start_str = time, end_str = time + 60000, limit = 5 )
    return historic_price[0][1]  #selects the open value of the first kline
#print(get_market_price('ETHUSDT',1620389209157))

def trade_infos_filled (pair:str, client_key = client) :
    """
    in : pair : the pair in question, client connexion key for binance API
    out : returns the dataframe of only the filled orders of the cryptopair 
    """
    trade = get_trades_info(pair)
    drop_indexes = []
    for lab, row in trade.iterrows () :
        if trade["status"][lab] != 'FILLED' :
            drop_indexes.append(lab)
    trade_dropped = trade.drop(drop_indexes, axis = 0)
    return trade_dropped
#print(trade_infos_filled('ADABNB'))

def add_price_market_orders (pair:str, client_key = client) :
    """
    in : pair : the pair in question, client connexion key for binance API
    out : returns the dataframe of only the filled orders of the cryptopair 
    """
    orders = trade_infos_filled (pair)
    for row, lab in orders.iterrows() :
        if orders["type"][row] == 'MARKET' :
            orders.loc[row, ('price')] = get_market_price(pair, int(orders['time'][row]))
    return orders
#print(add_price_market_orders('SANDUSDT'))

def compounded_average_sell_buy (pair:str, client_key = client) :
    """
    in : pair : the pair in question, client connexion key for binance API
    out : returns the compounded average buy in and sell out price in a list ([avg_sell, avg_buy])
    """
    trades = add_price_market_orders (pair)
    #print(trades)
    avg_sell, total_sell = 0 , 0
    avg_buy, total_buy  = 0 , 0
    
    for row, lab in trades.iterrows() :
        if trades["side"][row] == 'SELL' :
            avg_sell += float(trades['price'][row])*float(trades['executedQty'][row])
            total_sell += float(trades['executedQty'][row])
        else :
            avg_buy += float(trades['price'][row])*float(trades['executedQty'][row])
            total_buy += float(trades['executedQty'][row])
        
    try : 
        compounded_average_sell = avg_sell/total_sell
    except ZeroDivisionError: 
        compounded_average_sell = 0

    try : 
        compounded_average_buy = avg_buy/total_buy
    except ZeroDivisionError: 
        compounded_average_buy = 0

    return ([compounded_average_sell, compounded_average_buy])
#print(compounded_average_sell_buy('ETHUSDT'))

def margin_calculation (pair:str, client_key = client) :
    """
    in : pair : the pair in question, client connexion key for binance API
    out : returns the margin made on the cryptopair so far
    """
    averages = compounded_average_sell_buy(pair)
    avg_buy = averages[1]
    current_price_dict = client_key.get_avg_price (symbol = pair)
    current_price = float(current_price_dict["price"])
    try : 
        marges = round ((current_price*100/avg_buy)-100,3)
    except ZeroDivisionError: 
        return ("No buy-in price available for this crypto")        
    return marges
#print(margin_calculation('MANAUSDT'))

### PROGRAMME PRINCIPAL

account_balances = get_account_balances()
coins_holded = list(account_balances["asset"])  #list of the coins holded in the wallet actually
print("the holded coins = ",coins_holded)  
for i in range (len(coins_holded)) :
    crypto_pairs = is_pair_traded(coins_holded[i])   #list of the crypto/pairs traded on the account
    print("the cryptopair traded = ",crypto_pairs)
    for i in range (len(crypto_pairs)) :
        print("the margin for this crypto_pair : ",margin_calculation(crypto_pairs[i]))

        