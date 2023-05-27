import pandas as pd
from termcolor import cprint
import yaml
import datetime
from datetime import timedelta
from tabulate import tabulate
import matplotlib.pyplot as plt
import math

#read in settings from yaml file
with open("new_version/config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

#read in data from file
file = cfg["settings"]["data_location"]
# file = "Data/GBPUSD_M5_202301160005_202302142350.csv"
df = pd.read_csv(file, low_memory=False)
df["Gmt time"] = df["Gmt"] + " " + df["time"] + ".000"
# df["Gmt time"] = df["Gmt time"] + ".000"

#find date range
date_range = [df["Gmt time"].iloc[0], df["Gmt time"].iloc[-1]]
date_format = cfg["settings"]["timestamp_format"]

for i in range(len(df)):
    if isinstance(df["Gmt time"].iloc[0], str) and isinstance(df["Open"].iloc[0], float) and df["Open"].iloc[0] > 0 and isinstance(df["High"].iloc[0], float) and df["High"].iloc[0] > 0 and isinstance(df["Low"].iloc[0], float) and df["Low"].iloc[0] > 0 and isinstance(df["Close"].iloc[0], float) and df["Close"].iloc[0] > 0:
        pass
    else:
        cprint("Data not suitable - exiting program...","red")
        quit()
    try:
        temp_timestamp = datetime.datetime.strptime(str(df["Gmt time"].iloc[i]), date_format)
    except Exception as e:
        cprint("Timestamp data does not match provided format - exiting program...","red")
        quit()
cprint("Data good", "green")

if isinstance(cfg["settings"]["account_spread"], float) and cfg["settings"]["account_spread"] >= 0 and isinstance(cfg["settings"]["risk_free_rate"], float) and cfg["settings"]["risk_free_rate"] >= 0 and isinstance(cfg["settings"]["minimum_FVG_size"], float) and cfg["settings"]["minimum_FVG_size"] >= 0:
    pass
else:
    cprint("Configuration error - check account_spread, risk_free_rate, minimum_FVG_size", "red")
    quit()
    
if isinstance(cfg["settings"]["data_location"], str) and isinstance(cfg["settings"]["timestamp_format"], str) and isinstance(cfg["settings"]["london_session_start"], str) and isinstance(cfg["settings"]["london_session_end"], str) and isinstance(cfg["settings"]["new_york_session_start"], str) and isinstance(cfg["settings"]["new_york_session_end"], str):
    pass
else:
    cprint("Configuration error - check data_location, timestamp_format, london_session_start, london_session_end, new_york_session_start, new_york_session_end", "red")
    quit()

if isinstance(cfg["settings"]["slow_sma_period"], int) and isinstance(cfg["settings"]["fast_sma_period"], int) and cfg["settings"]["slow_sma_period"] > 0 and cfg["settings"]["fast_sma_period"] > 0:
    pass
else:
    cprint("Configuration error - check sma_period configuration", "red")
    quit()

if (isinstance(cfg["settings"]["account_balance"], int) or isinstance(cfg["settings"]["account_balance"], float)) and (isinstance(cfg["settings"]["risk_percentage"], int) or isinstance(cfg["settings"]["risk_percentage"], float)) and (isinstance(cfg["settings"]["account_comission"], int) or isinstance(cfg["settings"]["account_comission"], float)) and cfg["settings"]["account_balance"] > 0 and cfg["settings"]["risk_percentage"] > 0 and cfg["settings"]["account_comission"] >= 0:
    pass
else:
    cprint("Configuraition error check account_balance, risk_percentage, account_comission", "red")
    quit()
    
cprint("Configuration good", "green")
    
#find date range
date_range = [df["Gmt time"].iloc[0], df["Gmt time"].iloc[-1]]

#account object to input initial cash balance (in base currency), spread (in pips) and comissions (in base currency)
class account:
    def __init__(self):
        self.balance = cfg["settings"]["account_balance"]
        self.initial_balance = self.balance
        self.spread = cfg["settings"]["account_spread"]
        self.comission = cfg["settings"]["account_comission"]
        self.risk_balance = cfg["settings"]["risk_percentage"]*self.balance/100
        self.wins = 0
        self.losses = 0
        self.total_loss = 0
        self.total_profit = 0
        self.running_equity = []
        self.running_pnl = []
        
    def update_balance(self, amount):
        if amount > 0:
            self.wins += 1
            self.total_profit += amount
        elif amount < 0:
            self.losses += 1
            self.total_loss += amount
        self.balance = round(self.balance + amount, 2)
        self.running_pnl.append(amount)
        
    def calculate_avg_win(self):
        if self.wins == 0:
            return 0
        return round(self.total_profit/self.wins, 2)
    def calculate_avg_loss(self):
        return round(abs(self.total_loss/self.losses), 2)
    
    def calculate_win_rate(self):
        return round((account.wins)*100/(account.wins + account.losses), 2)
    
    def account_tick(self):
        self.running_equity.append(self.balance)
        
    def calculate_roi(self):
        return round((self.balance - self.initial_balance)*100/self.initial_balance, 2)
    
    def calculate_absolute_drawdown(self):
        minimum = self.initial_balance
        for i in self.running_equity:
            if i < minimum:
                minimum = i
        return round((self.initial_balance - minimum)*100/self.initial_balance, 2)
    
    def calculate_relative_drawdown(self):
        local_high = self.initial_balance
        max_dd = 0
        for i in self.running_equity:
            if i > local_high:
                local_high = i
            if local_high - i > max_dd:
                max_dd = local_high - i
        return round(max_dd*100/self.initial_balance, 2)
    
    def length_of_backtest(self):
        f_date = datetime.datetime.strptime(temp_data[0][0], date_format)
        l_date = datetime.datetime.strptime(temp_data[-1][0], date_format)
        delta = l_date - f_date
        days_delta = delta.days
        return days_delta
    
    def calculate_sharpe_ratio(self):
        returns_sum = 0
        for i in range(len(self.running_pnl)):
            returns_sum += self.running_pnl[i]
        returns_mean = returns_sum/len(self.running_pnl)
        variance = sum([((x - returns_mean) ** 2) for x in self.running_pnl]) / len(self.running_pnl)
        std_dev = variance ** 0.5
        risk_free_rate = cfg["settings"]["risk_free_rate"]
        days_delta = self.length_of_backtest()
        normalised_risk_free_rate = risk_free_rate * (days_delta/252)
        unanualised_sharpe = (self.calculate_roi() - normalised_risk_free_rate)/std_dev
        anualised_sharpe = unanualised_sharpe*math.sqrt((252/days_delta))
        return round(anualised_sharpe, 4)
        
account = account()

#A class to store the FVG data for each instance
class FVG:
    def __init__(self, start_price, end_price, start_date, end_date, direction, half, fvg_id, previous_candle):
        self.start_price = start_price
        self.end_price = end_price
        self.start_date = start_date
        self.end_date = end_date
        self.direction = direction
        self.fvg_id = fvg_id
        self.half = half
        self.previous_candle = previous_candle
        
class limit_order:
    def __init__(self):
        self.placed = False
        self.entry_price = 0
        self.stop_level = None
        self.profit_level = None
        self.direction = None
    
    def create_order(self, entry_price, stop_level, profit_level, direction):
        self.entry_price = entry_price
        self.stop_level = stop_level
        self.profit_level = profit_level
        self.direction = direction
        self.placed = True
            
    def close_order(self):
        self.placed = False
        self.entry_price = 0
        self.stop_level = None
        self.profit_level = None
        self.direction = None

    def get_entry(self):
        return self.entry_price

limit_order = limit_order()
        
class trade():
    def __init__(self):
        self.direction = 0
        self.open = False
        self.stop_level = 0
        self.entry_price = 0
        self.profit_level = 0
        self.risk_reward = 0
        self.lot_size = 0
        
    def place_trade(self, stop_level, entry_price, profit_level, direction):
        self.direction = direction
        self.open = True
        self.stop_level = stop_level
        self.entry_price = entry_price
        self.profit_level = profit_level
        self.risk_reward = abs(entry_price-profit_level)/abs(entry_price-stop_level)
        self.lot_size = 100/(10000*abs(entry_price-stop_level))
    
    def close_trade(self):
        self.direction = 0
        self.open = False
        self.stop_level = 0
        self.entry_price = 0
        self.profit_level = 0
        self.risk_reward = 0
        self.lot_size = 0

trade = trade() 
#A function to check for a bullish candle
def check_bullish(candle):
    if candle[1] < candle[4]:
        return True
    else:
        return False
    
def fvg_gap(fvg_object):
    if abs(fvg_object.start_price - fvg_object.end_price) >= cfg["settings"]["minimum_FVG_size"]:
        return True
    else:
        return False
    

#A function to find FVGs from a list of three OHLC data points
def find_fvg(price_array):
    if len(price_array) != 3:
        cprint(f"ERROR - find_fvg takes 3 OHLC candles, but {len(price_array)} were provided")
        return
    
    # if check_bullish(price_array[0]) and check_bullish(price_array[1]) and check_bullish(price_array[2]):
    if check_bullish(price_array[1]):
        if price_array[0][2] < price_array[2][3]: #check if the high of the first candle is lower than the low of the last candle, thus a fair value gap
            temp_fvg = FVG(price_array[0][2], price_array[2][2], price_array[0][0], price_array[2][0], 1, (price_array[0][2] + price_array[2][3])/2, 0, price_array[0][3])
            if fvg_gap(temp_fvg):
                cprint("Fvg gap: ", "red", end = " ")
                cprint(abs(temp_fvg.start_price - temp_fvg.end_price), "blue")
                cprint(temp_fvg.start_price, "green")
                cprint(temp_fvg.end_price, "green")
                fvg_below.append(temp_fvg)
            return
        return
    
    elif (not check_bullish(price_array[1])):
        if price_array[0][3] > price_array[2][2]: #check if the low of the first candle is higher than the high of the last candle, thus a fair value gap
            temp_fvg = FVG(price_array[0][3], price_array[2][2], price_array[0][0], price_array[2][0], -1, (price_array[0][3] + price_array[2][2])/2, 0, price_array[0][2])
            if fvg_gap(temp_fvg):
                fvg_above.append(temp_fvg)
        return

        
#A function to check for mitigated fair value gaps
def check_mitigation(fvg_object, candle):
    if fvg_object.direction == 1 and candle[3] < ((fvg_object.start_price + fvg_object.end_price)/2):
        # cprint(f"Mitigated bullish {fvg_object.start_price} {fvg_object.start_date}  at  {candle[0]}")
        return fvg_object
    elif fvg_object.direction == -1 and candle[2] > ((fvg_object.start_price + fvg_object.end_price)/2):
        # cprint((f"Mitigated bearish {fvg_object.start_price} {fvg_object.start_date}  at  {candle[0]}"))
        return fvg_object
        
#a function to calculate the simple moving average
def calculate_sma(price_array, sma_period):
    if len(price_array) != sma_period:
        return None
    price_array_sum = 0
    for i in range(len(price_array)):
        try:
            price_array_sum += price_array[i][4]
        except Exception as e:
            cprint(e, "red")
            print(price_array)
    sma = price_array_sum/len(price_array)
    return sma
        
def find_extremity(price_array, timestamp, direction):
    if direction == 1:
        i = -1
        highest_high = 0    
        hh_date = None
        while timestamp != price_array[i][0]:
            if price_array[i][2] > highest_high:
                highest_high = price_array[i][2]
                hh_date = price_array[i][0]
            i -= 1
        return highest_high
    
    elif direction == -1:
        i = -1
        lowest_low = 999999999
        ll_date = None
        while timestamp != price_array[i][0]:
            if price_array[i][3] < lowest_low:
                lowest_low = price_array[i][3]
                ll_date = price_array[i][0]
            i -= 1
        return lowest_low
        
        
#MAIN PROGRAM
temp_data = [] #the array which holds the data to avoid leakage

#arrays to hold FVGs
fvg_above = []
fvg_below = []

#arrays to hold SMAs
slow_sma_period, medium_sma_period, fast_sma_period = int(cfg["settings"]["slow_sma_period"]), int(cfg["settings"]["medium_sma_period"]), int(cfg["settings"]["fast_sma_period"])
sma_slow = []
sma_medium = []
sma_fast = []

#session times
london_start_hours = int(cfg["settings"]["london_session_start"][:2])
london_start_minutes = int(cfg["settings"]["london_session_start"][3:5])
london_end_hours = int(cfg["settings"]["london_session_end"][:2])    
london_end_minutes = int(cfg["settings"]["london_session_end"][3:5])

new_york_start_hours = int(cfg["settings"]["new_york_session_start"][:2])
new_york_start_minutes = int(cfg["settings"]["new_york_session_start"][3:5])
new_york_end_hours = int(cfg["settings"]["new_york_session_end"][:2])    
new_york_end_minutes = int(cfg["settings"]["new_york_session_end"][3:5])

london_session = [datetime.datetime(2000, 1, 1, london_start_hours, london_start_minutes, 0).time(), datetime.datetime(2000, 1, 1, london_end_hours, london_end_minutes, 0).time()]
newyork_session = [datetime.datetime(2000, 1, 1, new_york_start_hours, new_york_start_minutes, 0).time(), datetime.datetime(2000, 1, 1, new_york_end_hours, new_york_end_minutes, 0).time()]

for i in range(len(df)):
    temp_data.append([df["Gmt time"].iloc[i], df["Open"].iloc[i], df["High"].iloc[i], df["Low"].iloc[i], df["Close"].iloc[i], df["Volume"].iloc[i]]) #adds the current price candle to the array. Note: It is only permitted to place market orders at the close price of the candle, however limit orders will be executed at the price specified, provided they are placed in the previous candle and triggered in a future candle
    current_timestamp = datetime.datetime.strptime(str(temp_data[-1][0]), date_format)
    account.account_tick()
    
    if account.balance <= 0:
        cprint("ACCOUNT BALANCE DEPLETED", "red")
        break
    
    print()
    cprint(current_timestamp, "yellow")
    
    ####INDICATORS
    #find FVGs as new candles are inputted
    find_fvg(temp_data[-4:-1])

    #calculate the SMAs as new candles are inputted
    sma_slow.append(calculate_sma(temp_data[-slow_sma_period:], slow_sma_period))
    sma_medium.append(calculate_sma(temp_data[-medium_sma_period:], medium_sma_period))
    sma_fast.append(calculate_sma(temp_data[-fast_sma_period:], fast_sma_period))
    
    #if the current array is too short to calculate the following indicators, skip over this part of the backtest
    if (sma_slow[-1] == None) or (sma_fast[-1] == None) or (sma_medium[-1] == None):
        continue

    #check for FVG mitigation every new candle
    for fvg_object in fvg_below:
        if check_mitigation(fvg_object, temp_data[-1]):
            fvg_below.remove(fvg_object)
            
    for fvg_object in fvg_above:
        if check_mitigation(fvg_object, temp_data[-1]):
            fvg_above.remove(fvg_object)
            
    if limit_order.placed == True and (limit_order.get_entry() != 0) and (temp_data[-1][3] - account.spread/2 <= limit_order.entry_price) and limit_order.direction == 1:
        cprint("BUY LIMIT ENTERED", "green", end = " ")
        trade.place_trade(limit_order.stop_level, limit_order.entry_price, limit_order.profit_level, 1) 
        cprint(trade.lot_size, "blue", end = " ")
        cprint(abs(trade.stop_level - trade.entry_price)*10000, "red")
        limit_order.close_order()
        cprint(f"Trade entered {trade.stop_level, trade.entry_price, trade.profit_level} BUY", "green")
        
    if limit_order.placed == True and (limit_order.get_entry() != 0) and (temp_data[-1][2] >= limit_order.entry_price) and limit_order.direction == -1:
        cprint("SELL LIMIT ENTERED", "green", end = " ")
        trade.place_trade(limit_order.stop_level, limit_order.entry_price, limit_order.profit_level, -1) 
        cprint(trade.lot_size, "blue", end = " ")
        cprint(abs(trade.stop_level - trade.entry_price)*10000, "red")
        limit_order.close_order()
        cprint(f"Trade entered {trade.stop_level, trade.entry_price, trade.profit_level} SELL", "red")


    if trade.open == True:
        cprint(trade.lot_size, "blue")
        if trade.direction == 1: #buy trade
            if temp_data[-1][3] < trade.stop_level and temp_data[-1][2] > trade.profit_level:
                cprint("INVALID PnL CALCULATION (counted as loss)", "blue")
                account.update_balance(-account.risk_balance-trade.lot_size*2*account.comission)
                trade.close_trade()

            elif temp_data[-1][3] - account.spread/2 < trade.stop_level:
                cprint("STOP LOSS", "red")
                account.update_balance(-account.risk_balance-trade.lot_size*2*account.comission)
                trade.close_trade()

            elif temp_data[-1][2] > trade.profit_level:
                cprint("TAKE PROFIT", "green")
                account.update_balance(account.risk_balance*trade.risk_reward-trade.lot_size*2*account.comission)
                trade.close_trade()
                
        if trade.direction == -1: #sell trade
            if temp_data[-1][2] > trade.stop_level and temp_data[-1][3] < trade.profit_level:
                cprint("INVALID PnL CALCULATION (counted as loss)", "blue")
                account.update_balance(-account.risk_balance-trade.lot_size*2*account.comission)
                trade.close_trade()
                
            elif temp_data[-1][2] > trade.stop_level:
                cprint("STOP LOSS", "red")
                account.update_balance(-account.risk_balance-trade.lot_size*2*account.comission)
                trade.close_trade()

            elif temp_data[-1][3] < trade.profit_level:
                cprint("TAKE PROFIT", "green")
                account.update_balance(account.risk_balance*trade.risk_reward-trade.lot_size*2*account.comission)
                trade.close_trade()
        continue
            
    #Find an entry matching the criteria 
    if (0 <= current_timestamp.weekday() <=4) and (((london_session[0] <= current_timestamp.time() <= london_session[1])) or (newyork_session[0] <= current_timestamp.time() <= newyork_session[1])):       
        if sma_fast[-1] > sma_medium[-1] > sma_slow[-1] and len(fvg_below) != 0: #Case where general trend is bullish
            closest_FVG = None
            #find closest FVG below
            try:
                closest_FVG = fvg_below[-1]
            except Exception:
                cprint(f"{temp_data[-1][0]}: No FVG below", "green")
            
            #find closest bullish FVG and place pending order, take profit at the highest high between the FVG and current price, stop loss at the lowest point between the start candle of the fvg and the previous candle's low
            highest_high = find_extremity(temp_data, fvg_below[-1].start_date, 1)
            limit_order.create_order(fvg_below[-1].half, fvg_below[-1].previous_candle, highest_high, 1)
         
        elif sma_fast[-1] < sma_medium[-1] < sma_slow[-1] and len(fvg_above) != 0: #Case where general trend is bearish
            closest_FVG = None
            try:
                closest_FVG = fvg_above[-1]
                pass
            except Exception:
                cprint(f"{temp_data[-1][0]}: No FVG above", "red")
            lowest_low = find_extremity(temp_data, fvg_above[-1].start_date, -1)
            limit_order.create_order(fvg_above[-1].half, fvg_above[-1].previous_candle, lowest_low, -1)
    else:
        pass
    
table = [["Start date", temp_data[0][0]], ["End date", temp_data[-1][0]], ["Days of backtest", account.length_of_backtest()], [" ", " "], ["Initial deposit", account.initial_balance], ["Final balance", account.balance], ["Total net profit", account.balance-account.initial_balance], ["Account growth %", account.calculate_roi()], ["Underlying asset change %", (round((temp_data[-1][4] - temp_data[0][1])*100/(temp_data[-1][4]),2))], [" ", " "], ["Win rate %", account.calculate_win_rate()], ["Number of trades", account.wins + account.losses], ["Avg number of trades a day", round((account.wins + account.losses)/account.length_of_backtest(), 2)], [" ", " "], ["Gross profit", account.total_profit], ["Gross loss", account.total_loss], ["Average win", account.calculate_avg_win()], ["Average loss", account.calculate_avg_loss()], ["Max. absolute drawdown", account.calculate_absolute_drawdown()], ["Max. relative drawdown", account.calculate_relative_drawdown()], [" ", " "], ["Sharpe ratio", account.calculate_sharpe_ratio()]]
table_html = (tabulate(table, tablefmt="html"))

html_obj = open(f"development/src/report{datetime.datetime.now()}.html", "w")
html_obj.write('<!DOCTYPE html> <html lang="en"> <head> <meta charset="utf-8"> <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"> <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no"> <title>Tearsheet (generated by QuantStats)</title> <meta name="robots" content="noindex, nofollow"> <link rel="shortcut icon" href="https://qtpylib.io/favicon.ico" type="image/x-icon"> <style> body{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;margin:30px}body,p,table,td,th{font:13px/1.4 Arial,sans-serif}.container{max-width:960px;margin:auto}img,svg{width:100%}h1,h2,h3,h4{font-weight:400;margin:0}h1 dt{display:inline;margin-left:10px;font-size:14px}h3{margin-bottom:10px;font-weight:700}h4{color:grey}h4 a{color:#09c;text-decoration:none}h4 a:hover{color:#069;text-decoration:underline}hr{margin:25px 0 40px;height:0;border:0;border-top:1px solid #ccc}#left{width:620px;margin-right:18px;margin-top:-1.2rem;float:left}#right{width:320px;float:right}#left svg{margin:-1.5rem 0}#monthly_heatmap{overflow:hidden}#monthly_heatmap svg{margin:-1.5rem 0}table{margin:0 0 40px;border:0;border-spacing:0;width:100%}table td,table th{text-align:right;padding:4px 5px 3px 5px}table th{text-align:right;padding:6px 5px 5px 5px}table td:first-of-type,table th:first-of-type{text-align:left;padding-left:2px}table td:last-of-type,table th:last-of-type{text-align:right;padding-right:2px}td hr{margin:5px 0}table th{font-weight:400}table thead th{font-weight:700;background:#eee}#eoy table td:after{content:"%"}#eoy table td:first-of-type:after,#eoy table td:last-of-type:after,#eoy table td:nth-of-type(4):after{content:""}#eoy table th{text-align:right}#eoy table th:first-of-type{text-align:left}#eoy table td:after{content:"%"}#eoy table td:first-of-type:after,#eoy table td:last-of-type:after{content:""}#ddinfo table td:nth-of-type(3):after{content:"%"}#ddinfo table th{text-align:right}#ddinfo table td:first-of-type,#ddinfo table td:nth-of-type(2),#ddinfo table th:first-of-type,#ddinfo table th:nth-of-type(2){text-align:left}#ddinfo table td:nth-of-type(3):after{content:"%"} @media print{hr{margin:25px 0}body{margin:0}.container{max-width:100%;margin:0}#left{width:55%;margin:0}#left svg{margin:0 0 -10%}#left svg:first-of-type{margin-top:-30%}#right{margin:0;width:45%}} </style> </head> <body onload="save()"> <div class="container"> <h1>' + file[5:11] + '<dt>' + temp_data[0][0] + ' - ' + temp_data[-1][0] + '</dt></h1> <hr> <div id="left"> <div> <img src="/Users/kevinkavaliauskas/Documents/GitHub/nea2022-kevinkavaliauskas/development/src/equity.png" alt="Equity"> </div> <div id="vol_returns"><img src="/Users/kevinkavaliauskas/Documents/GitHub/nea2022-kevinkavaliauskas/development/src/asset.png" alt="Asset"></div> </div> <div id="right"> <h3>Key Performance Metrics</h3> ' + table_html + ' </div> </div> <style>*{white-space:auto !important;}</style> </body> </html>')

def plot_equity():
    indexes = []
    for i in range(len(temp_data)):
        indexes.append(i)
    plt.figure(1)
    plt.plot(indexes, account.running_equity)
    plt.xlabel("Candle")
    plt.ylabel("Balance")
    plt.savefig("development/src/equity.png")
    
def plot_assett():
    closes = []
    indexes = []
    for i in range(len(temp_data)):
        indexes.append(i)
    for i in range(len(temp_data)):
        closes.append(temp_data[i][4])
    plt.figure(2)
    plt.plot(indexes, closes)
    plt.xlabel("Candle")
    plt.ylabel("Price")
    plt.savefig("development/src/asset.png")
    # plt.savefig("asset.png")
        
plot_equity()
plot_assett()
        
        
