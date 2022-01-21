from os import access
import trading
from account import *
import database as db
import time
import indicators as indi

# Import data from config.json // ดึงข้อมูลจากไฟล์ config.json
dir_path = os.path.dirname(os.path.realpath(__file__))

def read_config():
    with open(dir_path + '/config.json') as json_file:
        return json.load(json_file)

config = read_config()

#Trading Setting
bot_name = config["bot_name"]
pair = config['pair']
asset_name = config['asset_name']
qoute_currency = config["qoute_currency"]
rebalance_target_value = float(config["rebalance_target_value"])  # ค่า Rebalance ทีอยาก fix ไว้
min_reb_range = float(config["rebalance_minimum_range"]) # ระยะห่างจากค่าที่ Fix ไว้ ขั้นต่ำ ที่จะทำการ Rebalance

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

        print('Starting Future Rebalance Bot...')
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
        free_col = trading.get_free_col()
        total_port_value = trading.get_total_port_value(qoute_currency, asset_name)
        asset_value = trading.get_position_value(pair)
        asset_size = trading.get_position_size(pair)

        if cash < 0.1 or free_col < 0.1:
            Time = int(time.time())
            db.log(Time, 69, 'Cash Not Enough')
            break;
        
        # Checking Initial Rebalance Loop
        while asset_value < 1 and free_col > 0:
            print('Entering Initial Rebalance Loop')
            print("------------------------------")
            wallet = trading.get_wallet_details()
            cash = trading.get_cash(qoute_currency)
            Time = trading.get_time()
            free_col = trading.get_free_col()
            total_port_value = trading.get_total_port_value(qoute_currency, asset_name)
            asset_value = trading.get_position_value(pair)
            asset_size = trading.get_position_size(pair)

            print('Time : {}'.format(Time))
            print('Bot Name : {}'.format(bot_name))
            print('Your Remaining Cash : {} {}'.format(cash, qoute_currency))
            print('Your free collateral is {}'.format(free_col))
            print('Your {} value: {} USD'.format(asset_name, asset_value))
            print('Your {} size: {}'.format(asset_name, asset_size))
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

            # Create BUY params
            initial_diff = rebalance_target_value - asset_value
            buy_size = initial_diff / price
            buy_price = bid_price

            print('Checking {} Buy Condition ......'.format(format(asset_name)))
            if free_col > min_trade_value and buy_size > min_size:
                trading.buy_execute(pair, asset_name, buy_size, buy_price)
            elif free_col < min_trade_value:
                print("Not Enough Cash to buy {}".format(asset_name))
                print('Your Collateral is {} // Minimum Trade Value is {}'.format(free_col, min_trade_value))
            else:    
                print("Buy size is too small")
                print("Your {} order size is {} but minimim size is {}".format(asset_name, buy_size, min_size))
                print("------------------------------")

        # Rebalancing Loop
        while asset_value > 1 and free_col > 0:
            print('Entering Rebalance Loop')
            print("------------------------------")

            for t in time_sequence:
                print('Current Time Sequence is : {}'.format(t))
                print("------------------------------")
                wallet = trading.get_wallet_details()
                cash = trading.get_cash(qoute_currency)
                Time = trading.get_time()
                total_port_value = trading.get_total_port_value(qoute_currency, asset_name)
            
                # Rebalancing Parameter check
                price = trading.get_price(pair)
                asset_value = trading.get_position_value(pair)
                free_col = trading.get_free_col()
                fixed_value = rebalance_target_value  # Just for the sake of understanding
                diff = abs(fixed_value - asset_value)
                liq_price = trading.get_liquidation_price(pair)
                last_trade_price = trading.get_last_trade_price(pair)

                print('Time : {}'.format(Time))
                print('Bot Name : {}'.format(bot_name))
                print('Portfolio NAV = {}'.format(total_port_value))
                print('Your Remaining Cash : {} {}'.format(cash, qoute_currency))
                print('Your free collateral is {}'.format(free_col))
                print('Your Liquidation Price is : {}'.format(liq_price))
                print('{} Price is {}'.format(asset_name, price))
                print('Your {} Value is {}'.format(asset_name, asset_value))
                print('Diff = {}'.format(str(diff)))
                print('Last trade price is {}'.format(last_trade_price))
                
        
                if asset_value < fixed_value - min_reb_range and price < last_trade_price:
                    print("Current {} Value less than fix value : Rebalancing -- Buy".format(asset_name))

                    # Recheck trading params
                    price = trading.get_price(pair)
                    bid_price = trading.get_bid_price(pair)
                    ask_price = trading.get_ask_price(pair)
                    min_size = trading.get_minimum_size(pair)
                    step_price = trading.get_step_price(pair)
                    min_trade_value = trading.get_min_trade_value(pair, price)
                    cash = trading.get_cash(qoute_currency)
                    asset_value = trading.get_position_value(pair)
                    diff = abs(fixed_value - asset_value)
                    pending_buy = trading.get_pending_buy(pair)

                    # Create BUY params
                    buy_size = diff / price
                    buy_price = bid_price
            
                    # BUY order execution
                    if free_col > min_trade_value and buy_size > min_size:
                        trading.buy_execute(pair, asset_name, buy_size, buy_price)
                    elif free_col < min_trade_value:
                        print("Not Enough Cash to buy {}".format(asset_name))
                        print('Your Collateral is {} // Minimum Trade Value is {}'.format(cash, min_trade_value))
                    else:
                        print("Buy size is too small")
                        print("Your order size is {} but minimim size is {}".format(str(buy_size, min_size)))
                        print("------------------------------")
                
                elif asset_value > fixed_value + min_reb_range and price > last_trade_price:
                    print("Current {} Value more than fix value : Rebalancing -- Sell".format(asset_name))
                                
                    # Recheck trading params
                    price = trading.get_price(pair)
                    bid_price = trading.get_bid_price(pair)
                    ask_price = trading.get_ask_price(pair)
                    min_size = trading.get_minimum_size(pair)
                    step_price = trading.get_step_price(pair)
                    min_trade_value = trading.get_min_trade_value(pair, price)
                    cash = trading.get_cash(qoute_currency)
                    asset_value = trading.get_position_value(pair)
                    diff = abs(fixed_value - asset_value)
                    pending_sell = trading.get_pending_sell(pair)
                                        
                    # Create SELL params
                    sell_size = diff / price
                    sell_price = ask_price
                                
                    # SELL order execution
                    if diff > min_trade_value and sell_size > min_size:
                        trading.sell_execute(pair, asset_name, sell_size, sell_price)
                    else:
                        print("Not Enough Balance to sell {}".format(asset_name))
                        print('You have {} {} // Minimum Trade Value is {}'.format(asset_name, asset_value, min_trade_value))
                        print("------------------------------")
                                
                else:
                    print("Current {} value = fix rebalance value, Waiting for value changed".format(asset_name))
                    print("------------------------------")
                    time.sleep(5)

                # Rebalancing Time Sequence
                time.sleep(t * time_multiplier)

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
            #log permission denied : 401
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