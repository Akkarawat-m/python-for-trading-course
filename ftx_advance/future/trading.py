from account import *
import time
import database as db
import pandas as pd

def get_time():  # เวลาปัจจุบัน
    named_tuple = time.localtime() # get struct_time
    Time = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    return Time

def get_price(pair):
    price = float(exchange.fetch_ticker(pair)['last'])
    return price

def get_ask_price(pair):
    ask_price = float(exchange.fetch_ticker(pair)['ask'])
    return ask_price

def get_bid_price(pair):
    bid_price = float(exchange.fetch_ticker(pair)['bid'])
    return bid_price

def get_remain_open(id):
    remain = 0
    for i in exchange.private_get_orders()['result']:
        if i['id'] == id:
            remain += float(i['remainingSize'])
    return remain

def get_pending_buy(pair):
    pending_buy = []
    
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'buy':
            pending_buy.append(i['info'])
            
    return pending_buy

def get_pending_sell(pair):
    pending_sell = []
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'sell':
            pending_sell.append(i['info'])
    return pending_sell

def create_buy_order(pair, buy_size, buy_price, order_type="limit", post_only=True):
    # Order Parameter
    types = order_type
    side = 'buy'
    size = buy_size
    price = buy_price
    return exchange.create_order(pair, types, side, size, price, {'postOnly': post_only})

    
def create_sell_order(pair, sell_size, sell_price, order_type="limit", post_only=True):
    # Order Parameter
    types = order_type
    side = 'sell'
    size = sell_size
    price = sell_price
    return exchange.create_order(pair, types, side, size, price, {'postOnly': post_only})
    
def cancel_order(order_id):
    if exchange.cancel_order(order_id):
        print("Order ID : {} Successfully Canceled".format(order_id))

def get_minimum_size(pair):
    minimum_size = float(exchange.fetch_ticker(pair)['info']['minProvideSize'])
    return minimum_size

def get_step_size(pair):
    step_size = float(exchange.fetch_ticker(pair)['info']['sizeIncrement'])
    return step_size

def get_step_price(pair):
    step_price = float(exchange.fetch_ticker(pair)['info']['priceIncrement'])
    return step_price

def get_min_trade_value(pair, price):
    min_trade_value = float(exchange.fetch_ticker(pair)['info']['sizeIncrement']) * price
    return min_trade_value

def get_wallet_details():
    wallet = exchange.privateGetWalletBalances()['result']
    return wallet

def get_total_port_value(qoute_currency, asset_name):
    wallet = exchange.privateGetWalletBalances()['result']
    token_lst = [[item['coin'],item['usdValue']] for item in wallet]
    total_port_value = 0
    
    for token in token_lst:
        if token[0] == qoute_currency or token[0] == asset_name:
            asset_value = round(float(token[1]),2)
            total_port_value += asset_value
    return total_port_value

def get_asset_value(asset_name):
    wallet = exchange.privateGetWalletBalances()['result']
    token_lst = [[item['coin'],item['usdValue']] for item in wallet]
    asset_value = 0
    
    for token in token_lst:
        if token[0] == asset_name:
            value = round(float(token[1]),2)
            asset_value += value
    return float(asset_value)

def get_asset_size(asset_name):
    wallet = exchange.privateGetWalletBalances()['result']
    asset_lst = [[item['coin'],item['availableWithoutBorrow']] for item in wallet]
    asset_size = 0

    for asset in asset_lst:
        if asset[0] == asset_name:
            size = round(float(asset[1]),8)
            asset_size += size
    return float(asset_size)

def get_cash(qoute_currency):
    wallet = exchange.privateGetWalletBalances()['result']
    cash = 0
    
    for t in wallet:
        if t['coin'] == qoute_currency:
            cash += float(t['availableWithoutBorrow'] )
    return cash

def get_position_size(pair):
    positions = exchange.privateGetPositions()['result']
    position_size = 0
    for pos in positions:
        if pos['future'] == pair:
            position_size += float(pos['netSize'])
        
    return float(position_size)

def get_position_value(pair):
    positions = exchange.privateGetPositions()['result']
    position_value = 0
    for pos in positions:
        if pos['future'] == pair:
            position_value += float(pos['cost'])
    
    return float(position_value)

def get_free_col():
    free_col = float(exchange.privateGetAccount()['result']['freeCollateral'])
    return free_col

def get_liquidation_price(pair):
    positions = exchange.privateGetPositions()['result']
    liq_price = 0
    for pos in positions:
        if pos['future'] == pair:
            liq_price += float(pos['estimatedLiquidationPrice'])
    return liq_price

def grid_zone_calculation(up_zone, low_zone, grid_qty, capital, leverage):
    lev_capital = capital * leverage
    size = float(lev_capital/grid_qty)
    step = float((up_zone - low_zone) / grid_qty)
    total_zone = grid_qty

    cumu_coins = 0
    grid_price = []
    grid_asset = []

    for i in range(total_zone + 1):
        price = round(up_zone - (step * i), 4)
        if price < up_zone:
            cumu_coins += size / price
            grid_price.append(price)
            grid_asset.append(cumu_coins)
        elif price == up_zone:
            cumu_coins += 0
            grid_price.append(price)
            grid_asset.append(cumu_coins)

    x_point = [up_zone, low_zone]
    y_point = [grid_asset[0], grid_asset[-1]]

    a = (y_point[1] - y_point[0]) / (x_point[1] - x_point[0])
    b = y_point[1] - (a * (x_point[1]))

    return a, b

def buy_execute(pair, asset_name, buy_size, buy_price):
    # check pending buy order
    pending_buy = get_pending_buy(pair)
    
    if pending_buy == []:
        print('Buying {} Size = {}'.format(asset_name, buy_size))
        order = create_buy_order(pair, buy_size, buy_price, order_type="limit", post_only=True)
        order_id = order['id']
        created_order = exchange.fetch_order(order_id)
        
        if created_order['status'] == 'open':
            print('Buy Order Created Success, Order ID: {}'.format(order_id))
            time.sleep(5)
            
            # update order status
            created_order = exchange.fetch_order(order_id) 
            remain = created_order['remaining']
            price = get_price(pair)
            step = get_step_price(pair)
            
            while remain > 0 and abs(price - buy_price) < (3 * step) :
                print('Waiting For Buy Order {} To be filled'.format(order_id))
                time.sleep(10)
                
                # update order status
                created_order = exchange.fetch_order(order_id) 
                remain = created_order['remaining']
                price = get_price(pair)
            
            if created_order['remaining'] == 0 and created_order['status'] == 'closed':
                print("Buy order Matched")
                print("Updating Trade Log")
                db.update_trade_log(pair)
                print("------------------------------")
                
            elif remain > 0 and remain < created_order['amount']:
                print("Order partially matched but price is moving : sending new order")
                db.update_trade_log(pair)
                cancel_order(order_id)
            else:
                print('Buy Order is not Matched or Cancelled, Retrying')
                cancel_order(order_id)
                print("------------------------------")
                
        elif created_order['status'] == 'canceled':
            print('Buy order create failed Order ID: {}'.format(order_id))
        else:
            print("Error Check_2")
            
    else:
        pending_buy_id = get_pending_buy(pair)[0]['id']
        pending_buy_order = exchange.fetch_order(pending_buy_id)
        print("Pending Buy Order Founded ID: {}".format(pending_buy_id))
        print('Waiting For Buy Order To be filled')
        time.sleep(10)
        
        # update order status
        pending_buy_order = exchange.fetch_order(pending_buy_id) 
        remain = pending_buy_order['remaining']
        price = get_price(pair)
        step = get_step_price(pair)
        
        while remain > 0 and abs(price - buy_price) < (3 * step) :
            print('Waiting For Buy Order {} To be filled'.format(pending_buy_id))
            time.sleep(10)
            
            # update order status
            pending_buy_order = exchange.fetch_order(pending_buy_id) 
            remain = pending_buy_order['remaining']
            price = get_price(pair)
        
        if pending_buy_order['status'] == 'closed':
            print("Buy order Matched")
            print("Updating Trade Log")
            db.update_trade_log(pair)
            print("------------------------------")
            
        elif remain > 0 and remain < pending_buy_order['amount']:
            print("Order partially matched but price is moving : sending new order")
            print("Updating Trade Log")
            db.update_trade_log(pair)
            print("Canceling Order")
            cancel_order(pending_buy_id)
            time.sleep(5)
            pending_buy_order = exchange.fetch_order(pending_buy_id)

            if pending_buy_order['status'] == 'canceled':
                print('Buy Order Cancelled')
            else:
                print('Buy Order is not Matched or Cancelled, Retrying')
        else:
            print('Buy Order is not Matched or Cancelled, Retrying')
            cancel_order(pending_buy_id)
                       
    print("------------------------------")

def sell_execute(pair, asset_name, sell_size, sell_price):
    # check pending sell order
    pending_sell = get_pending_sell(pair)
    
    if pending_sell == []:
        print('Selling {} Size = {}'.format(asset_name, sell_size))
        order = create_sell_order(pair, sell_size, sell_price)
        order_id = order['id']
        created_order = exchange.fetch_order(order_id)
        
        if created_order['status'] == 'open':
            print('Sell Order Created Success, Order ID: {}'.format(order_id))
            print('Waiting For sell order {} To be filled'.format(order_id))
            time.sleep(10)
            
            # update order status
            created_order = exchange.fetch_order(order_id) 
            remain = created_order['remaining']
            price = get_price(pair)
            step = get_step_price(pair)
            
            while remain > 0 and abs(price - sell_price) < (3 * step) :
                print('Waiting For Sell Order {} To be filled'.format(order_id))
                time.sleep(10)
                
                # update order status
                created_order = exchange.fetch_order(order_id) 
                remain = created_order['remaining']
                price = get_price(pair)
            
            if created_order['remaining'] == 0 and created_order['status'] == 'closed':
                print("Sell order Matched")
                print("Updating Trade Log")
                db.update_trade_log(pair)
                print("------------------------------")
                
            elif remain > 0 and remain < created_order['amount']:
                print("Order partially matched but price is moving : sending new order")
                db.update_trade_log(pair)
                cancel_order(order_id)
            else:
                print('Sell Order is not Matched or Cancelled, Retrying')
                cancel_order(order_id)
                print("------------------------------")
                
        elif created_order['status'] == 'canceled':
            print('Sell order create failed Order ID: {}'.format(order_id))
        else:
            print("Error Check_2")
            
    else:
        pending_sell_id = get_pending_sell(pair)[0]['id']
        pending_sell_order = exchange.fetch_order(pending_sell_id)
        print("Pending Sell Order Founded ID: {}".format(pending_sell_id))
        print('Waiting For Sell Order To be filled')
        time.sleep(10)
        
        # update order status
        pending_sell_order = exchange.fetch_order(pending_sell_id)
        remain = pending_sell_order['remaining']
        price = get_price(pair)
        step = get_step_price(pair)
        
        while remain > 0 and abs(price - sell_price) < (3 * step) :
            print('Waiting For sell Order {} To be filled'.format(pending_sell_id))
            time.sleep(10)
            
            # update order status
            pending_sell_order = exchange.fetch_order(pending_sell_id)
            remain = pending_sell_order['remaining']
            price = get_price(pair)
        
        if pending_sell_order['status'] == 'closed':
            print("Sell order matched")
            print("Updating Trade Log")
            db.update_trade_log(pair)
            print("------------------------------")
            
        elif remain > 0 and remain < pending_sell_order['amount']:
            print("Order partially matched but price is moving : sending new order")
            print("Updating Trade Log")
            db.update_trade_log(pair)
            print("Canceling Order")
            cancel_order(pending_sell_order)
            time.sleep(5)
            pending_sell_order = exchange.fetch_order(pending_sell_id)

            if pending_sell_order['status'] == 'canceled':
                print('Sell Order Cancelled')
            else:
                print('Sell Order is not Matched or Cancelled, Retrying')
        else:
            print('Sell Order is not Matched or Cancelled, Retrying')
            cancel_order(pending_sell_id)
    print("------------------------------")
    
def get_last_trade_price(pair):
    pair = pair
    trade_history = pd.DataFrame(exchange.fetchMyTrades(pair, limit = 1),
                            columns=['id', 'timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee'])
    last_trade_price = trade_history['price']
    
    return float(last_trade_price)    