import json
import ccxt
import os

# รอแก้ให้ดึงจาก API/DB ?
dir_path = os.path.dirname(os.path.realpath(__file__))

def read_config():
    with open(dir_path + '/config.json') as json_file:
        return json.load(json_file)

config = read_config()

# API and Secret setting
api_key = config["api_key"]
api_secret = config["api_secret"]
subaccount = config["subaccount"]
bot_name = config["bot_name"]

exchange = ccxt.ftx({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True}
)
exchange.headers = {'FTX-SUBACCOUNT': subaccount,}

