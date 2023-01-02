import datetime
import time
import websocket
import ujson
import os

import yaml

import HccTD
from HccTD import JsonLocal,TestBlock,RecordStreamingData,Log,TdTradeTest,open_market,Streaming,CollectStreaming
import random
from HccTD import Quan,Smoker
from typing import Dict
import numpy as np
import shutil

WORKDIR = os.path.abspath(os.path.dirname(__file__))


def formal_run():

    with open(os.path.join(WORKDIR,"config","tradingBot","botConfig.yaml"),"r") as f1:
        collect_symbol = []
        with open(os.path.join(WORKDIR, "config", "collect", "collectConfig.yaml"), "r") as f2:
            collect_data = yaml.safe_load(f2)["collect"]
            for each_set in collect_data:
                collect_symbol.append(each_set["long"])
                collect_symbol.append(each_set["short"])
        data = yaml.safe_load(f1)["bot"]
        account_id = data["account_id"]
        long_symbol = data["long_symbol"]
        short_symbol = data["short_symbol"]
        if long_symbol in collect_symbol or short_symbol in collect_symbol:
            raise "can't try trading and collecting same symbol in the same time"
        api_key = data["api_key"]
        budget = data["budget"]


    token_path = os.path.join(WORKDIR, "token.json")

    redirect_uri = "https://localhost:8080"

    finn_token = HccTD.get_finn_token_from_yaml(long_symbol)

    tda_client = HccTD.get_tda_client(
        token_path=token_path,
        api_key=api_key,
        redirect_uri=redirect_uri
    )
    client = HccTD.ClientExtend(client=tda_client, account_id=account_id)

    log_sys = Log(long_symbol, short_symbol)

    account_cash_info = client.get_cash_balance()
    if account_cash_info < budget:
        raise "budget is larger than your balance"

    print(f"{long_symbol} {short_symbol} Start...")
    print(f"budget {budget}")

    now = (datetime.datetime.now() - datetime.timedelta(hours=13))
    close_process_time = (datetime.datetime.now() - datetime.timedelta(hours=13)).replace(hour=16, minute=10)

    def on_open(ws):

        symbol1 = {"type": "subscribe", "symbol": long_symbol}
        symbol2 = {"type": "subscribe", "symbol": short_symbol}
        ws.send(ujson.dumps(symbol1))
        ws.send(ujson.dumps(symbol2))

    while now < close_process_time:
        now = (datetime.datetime.now() - datetime.timedelta(hours=13))
        close_process_time = (datetime.datetime.now() - datetime.timedelta(hours=13)).replace(hour=16,
                                                                                              minute=10)  # 期望關閉市場後 關閉process
        time.sleep(random.randint(0, 15))
        market_status = open_market()

        if market_status:

            td_accoubt_middle = HccTD.TdAccount_middle(budget, client, long_symbol,
                                                       short_symbol)  # 將原始td操作封裝成 跟之前測試件 同樣接口 可以直接使用
            smoker = Smoker(period=15, frequency=1, log_sys=log_sys)
            quan = Quan(trade=td_accoubt_middle, smoker=smoker, log_sys=log_sys, formal=True)
            csv_sys = RecordStreamingData(long_symbol=long_symbol, short_symbol=short_symbol)
            ms = Streaming(quan=quan, streaming_csv_log=csv_sys, log_sys=log_sys, formal=True)

            websocket.enableTrace(True)

            ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={finn_token}",
                                        on_message=ms.on_message,
                                        on_error=ms.on_error,
                                        on_close=ms.on_close)

            while market_status:
                ws.on_open = on_open
                ws.run_forever()
                market_status = open_market()


if __name__ == "__main__":

    formal_run()





