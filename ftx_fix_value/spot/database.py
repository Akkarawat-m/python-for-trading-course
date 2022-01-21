import account
import pandas as pd
from datetime import datetime
import pytz
import csv
import os

subaccount = account.subaccount
exchange = account.exchange
bot_name = account.bot_name  #ใช้แยกบอทแต่ละตัว

# ดึงตรงเลย
tradelog_file = "tradinglog_{}.csv".format(bot_name)
trading_call_back = 5

def check_db(tradelog_file):
    try:
        tradinglog = pd.read_csv(tradelog_file)
        print('DataBase Exist Loading DataBase....')
    except:
        tradinglog = pd.DataFrame(columns=['id', 'timestamp', 'time', 'pair', 'side', 'price', 'qty', 'fee', 'timeseries', 'bot_name', 'subaccount', 'cost'])
        tradinglog.to_csv(tradelog_file, index=False)
        print("Database Created")
        
    return tradinglog

# Database Setup
print("------------------------------")
print('Checking Database file.....')
tradinglog = check_db(tradelog_file)
print("------------------------------")

def get_trade_history(pair, trading_call_back=5):
    trade_history = pd.DataFrame(exchange.fetchMyTrades(pair, limit=trading_call_back),
                              columns=['id', 'timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'fee'])
    
    # คำนวณ Fee
    cost = []
    for i in range(len(trade_history)):
        fee = trade_history['fee'].iloc[i]['cost'] if trade_history['fee'].iloc[i]['currency'] == 'USD' else trade_history['fee'].iloc[i]['cost'] * trade_history['price'].iloc[i]
        cost.append(fee)  # ใน fee เอาแค่ cost
    
    trade_history['fee'] = cost
    
    return trade_history

def get_last_id(pair, trading_call_back=5):
    trade_history = get_trade_history(pair)
    last_trade_id = (trade_history.iloc[:trading_call_back]['id'])
    
    return last_trade_id

def update_trade_log(pair, tradelog_file=tradelog_file):
    tradinglog = pd.read_csv(tradelog_file)
    last_trade_id = get_last_id(pair)
    trade_history = get_trade_history(pair)
    
    for i in last_trade_id:
        tradinglog = pd.read_csv(tradelog_file)
        trade_history = get_trade_history(pair)
    
        if int(i) not in tradinglog.values:
            print("New Trade Founded")
            last_trade = trade_history.loc[trade_history['id'] == i]
            list_last_trade = last_trade.values.tolist()[0]

            # แปลงวันที่ใน record
            d = datetime.strptime(list_last_trade[2], "%Y-%m-%dT%H:%M:%S.%fZ")
            d = pytz.timezone('Etc/GMT+7').localize(d)
            d = d.astimezone(pytz.utc)
            Date = d.strftime("%Y-%m-%d")
            Time = d.strftime("%H:%M:%S")


            cost = float(list_last_trade[5] * list_last_trade[6])

            # edit & append ข้อมูลก่อน add เข้า database
            list_last_trade[1] = Date
            list_last_trade[2] = Time
            list_last_trade.append(bot_name)
            list_last_trade.append(subaccount)
            list_last_trade.append(cost)

            ## list_last_trade.append(cost)

            with open(tradelog_file, "a+", newline='') as fp:
                wr = csv.writer(fp, dialect='excel')
                wr.writerow(list_last_trade)
            print('Recording Trade ID : {}'.format(i))
        else:
            print('Trade Already record')
            
def log(Time, code, message):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    with open(dir_path + '/log.txt', 'a') as txt_file:
        data = "{} | {} | {} \n".format(Time, code, message)
        txt_file.write(data)
    