import os
import trading
from account import *
import database as db
import time

# Import data from config.json // ดึงข้อมูลจากไฟล์ config.json
dir_path = os.path.dirname(os.path.realpath(__file__))

def read_config():
    with open(dir_path + '/config.json') as json_file:
        return json.load(json_file)

config = read_config()

# Trading Setting
bot_name = config["bot_name"]
pair = config['pair']
asset_name = config['asset_name']
qoute_currency = config["qoute_currency"]
user_id = 1  # รอแก้ให้รับค่าจาก config
bot_id  = 1  # รอแก้ให้รับค่าจาก config

# Grid Setting
up_zone = config["up_zone"]
low_zone = config["low_zone"]
grid_qty = config["grid_qty"]
capital = config["capital"]
leverage = 1
size = float(capital * leverage / grid_qty)
step = float((up_zone - low_zone) / grid_qty)

# Grid Data calculation
grid_data = trading.grid_zone_calculation(up_zone, low_zone, grid_qty, capital, leverage)
a = grid_data[0]
b = grid_data[1]

# Order Type
post_only = True  # Maker or Taker (วางโพซิชั่นเป็น MAKER เท่านั้นหรือไม่ True = ใช่ // Defalut = True)
order_type = "limit" # limit, market

# Time Related Logic
time_sequence = [30]  # Rebalancing Time Sequence (เวลาที่จะใช้ในการ Rebalance ใส่เป็นเวลาเดี่ยว หรือชุดตัวเลขก็ได้)
time_multiplier = 1

Time = int(time.time())
db.log(Time, 1, 'Bot Started')

while True:
    try:
        print('Starting Spot Grid Bot...')
        print('You are trading {}'.format(asset_name))
        print("------------------------------")
        print('Validating Trading History')
        db.update_trade_log(pair)
        print("------------------------------")
        print('Validating History Finished')
        print("------------------------------")

        wallet = trading.get_wallet_details()
        cash = trading.get_cash(qoute_currency)
        Time = trading.get_time()
        total_port_value = trading.get_total_port_value(qoute_currency, asset_name)
        asset_value = trading.get_asset_value(asset_name)
        asset_size = trading.get_asset_size(asset_name)
        
        # Check initail Balance
        if cash < 0.1:
            Time = int(time.time())
            db.log(Time, 69, 'Cash Not Enough')
            break;
        
        # Checking Initial Trading Loop
        while asset_value < 0.01 and cash > 0:
            print('Entering Initial Trading Loop')
            print("------------------------------")
            
            wallet = trading.get_wallet_details()
            cash = trading.get_cash(qoute_currency)
            Time = trading.get_time()
            total_port_value = trading.get_total_port_value(qoute_currency, asset_name)
            asset_value = trading.get_asset_value(asset_name)
            asset_size = trading.get_asset_size(asset_name)

            print('Time : {}'.format(Time))
            print('Bot Name : {}'.format(bot_name))
            print('Your Remaining Cash : {} {}'.format(cash, qoute_currency))
            print('Your {} value: {} USD'.format(asset_name, asset_value))
            print('You have {} : {} {}'.format(asset_name, asset_size, asset_name))
            print('Your Total Port Value is : {}'.format(total_port_value))
            print("------------------------------")
            print('{} is missing'.format(asset_name))
    
            # Get price params
            price = trading.get_price(pair)
            ask_price = trading.get_ask_price(pair)
            bid_price = trading.get_bid_price(pair)

            # Innitial asset BUY params
            min_size = trading.get_minimum_size(pair)
            step_price = trading.get_step_price(pair)
            min_trade_value = trading.get_min_trade_value(pair, price)
            cash = trading.get_cash(qoute_currency)
            pending_buy = trading.get_pending_buy(pair)
            
            # grid asset control calculation
            fix_asset_control = (a * price) + b
            
            # Create BUY params
            initial_diff = fix_asset_control - asset_value
            buy_size = initial_diff / price
            buy_price = bid_price

            print('Checking {} Buy Condition ......'.format(format(asset_name)))
            if cash > min_trade_value and buy_size > min_size:
                trading.buy_execute(pair, asset_name, buy_size, buy_price)
            elif cash < min_trade_value:
                print("Not Enough Cash to buy {}".format(asset_name))
                print('Your Cash is {} // Minimum Trade Value is {}'.format(cash, min_trade_value))
            else:    
                print("Buy size is too small")
                print("Your {} order size is {} but minimim size is {}".format(asset_name, buy_size, min_size))
                print("------------------------------")

        # Grid trading loop
        while asset_value > 1 and cash > 0:
            
            print('Entering trading loop')
            print("------------------------------")
            price = trading.get_price(pair)
            
            while price > up_zone:
                asset_size = trading.get_asset_size(asset_name)
                min_size = trading.get_minimum_size(pair)
                if asset_size > min_size:
                    bid_price = trading.get_bid_price(pair)
                    ask_price = trading.get_ask_price(pair)
                    step_price = trading.get_step_price(pair)
                    sell_price = ask_price
                    sell_size = asset_size
                    trading.sell_execute(pair, asset_name, sell_size, sell_price)
                    price = trading.get_price(pair)
                else:
                    print("Out of upper trading zone")                           
                    print("Current {} price > {}".format(asset_name, up_zone))
                    time.sleep(10)
                    price = trading.get_price(pair)
            
            while price < low_zone:
                print("Out of lower trading zone")
                print("Price lower than {}".format(str(low_zone)))
                price = trading.get_price(pair)
                time.sleep(5)
                 
            wallet = trading.get_wallet_details()
            cash = trading.get_cash(qoute_currency)
            Time = trading.get_time()
            total_port_value = trading.get_total_port_value(qoute_currency, asset_name)
            
            # grid trading Parameter check
            price = trading.get_price(pair)
            asset_value = trading.get_asset_value(asset_name)
            asset_size = trading.get_asset_size(asset_name)
            
            fix_asset_control = (a * price) + b
            diff = abs(fix_asset_control - asset_value)
            last_trade_price = trading.get_last_trade_price(pair)
                
            print('Time : {}'.format(Time))
            print('Bot_name: {}'.format(bot_name))
            print('Your Remaining Cash : {} {}'.format(cash, qoute_currency))
            print('Your {} size is {}'.format(asset_name, asset_size))
            print('{} Price is {}'.format(asset_name, price))
            print('Your {} value is {}'.format(asset_name, asset_value))
            print('Grid Fix {} value is {}'.format(asset_name, fix_asset_control))
            print('Diff = {}'.format(str(diff)))
            print('Last trade price is {}'.format(last_trade_price))
            print('Next Buy price : {}'.format(last_trade_price - step))
            print('Next Sell price : {}'.format(last_trade_price + step))    
            
            if asset_value < fix_asset_control and price < last_trade_price - step:
                print("Current {} Value less than grid fix value : trading -- Buy".format(asset_name))
                # Recheck trading params
                price = trading.get_price(pair)
                bid_price = trading.get_bid_price(pair)
                ask_price = trading.get_ask_price(pair)
                min_size = trading.get_minimum_size(pair)
                step_price = trading.get_step_price(pair)
                min_trade_value = trading.get_min_trade_value(pair, price)
                cash = trading.get_cash(qoute_currency)
                asset_value = trading.get_asset_value(asset_name)
                asset_size = trading.get_asset_size(asset_name)
                
                # Grid Parameter
                a = grid_data[0]
                b = grid_data[1]
                fix_asset_control = (a * price) + b
                diff = abs(fix_asset_control - asset_value)
                last_trade_price = trading.get_last_trade_price(pair)
                
                # Create BUY params
                buy_size = diff / price
                buy_price = bid_price
                
                # BUY order execution
                if cash > min_trade_value and buy_size > min_size:
                        trading.buy_execute(pair, asset_name, buy_size, buy_price)
                elif cash < min_trade_value:
                    print("Not Enough Cash to buy {}".format(asset_name))
                    print('Your Cash is {} // Minimum Trade Value is {}'.format(cash, min_trade_value))
                else:
                    print("Buy size is too small")
                    print("Your order size is {} but minimim size is {}".format(str(buy_size, min_size)))
                    print("------------------------------")
                    
            elif asset_value > fix_asset_control and price > last_trade_price + step:
                print("Current {} Value more than fix value : Rebalancing -- Sell".format(asset_name))
                # Recheck trading params
                price = trading.get_price(pair)
                bid_price = trading.get_bid_price(pair)
                ask_price = trading.get_ask_price(pair)
                min_size = trading.get_minimum_size(pair)
                step_price = trading.get_step_price(pair)
                min_trade_value = trading.get_min_trade_value(pair, price)
                cash = trading.get_cash(qoute_currency)
                asset_value = trading.get_asset_value(asset_name)
                asset_size = trading.get_asset_size(asset_name)
                
                # Grid Parameter
                a = grid_data[0]
                b = grid_data[1]
                fix_asset_control = (a * price) + b
                diff = abs(fix_asset_control - asset_value)
                last_trade_price = trading.get_last_trade_price(pair)
                
                # Create SELL params
                sell_size = diff / price
                sell_price = ask_price
                
                # SELL order execution
                if diff > min_size :
                    trading.sell_execute(pair, asset_name, sell_size, sell_price)
                else:
                    print("Not Enough Balance to sell {}".format(asset_name))
                    print('You have {} {} // Minimum Trade Value is {}'.format(asset_name, asset_value, min_trade_value))
                    print("------------------------------")    
                
            else:
                print("Current {} price not trigger yet : Waiting".format(asset_name))
                print("------------------------------")
                time.sleep(5)    

    except Exception as e:
        print('Error : {}'.format(str(e)))
        Time = int(time.time())

        # Check credential
        error_text = str(e)
        if 'permissions' in error_text or 'Not logged in' in error_text:
            print('Bot stopped due to credential error')
            Time = int(time.time())
            code = 401
            db.log(Time, code, 'Bot stopped due to credential error')
            #log permission denied : 400
            break;
        
        if 'No such market:' in error_text:
            print('Bot stopped due to pair error')
            Time = int(time.time())
            code = 400
            db.log(Time, code, 'Bot stopped due to pair error')
            #log pair error 400
            break;

        db.log(Time, 999, error_text)
            
        time.sleep(10)