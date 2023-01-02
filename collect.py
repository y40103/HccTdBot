import datetime
import time
import websocket
import ujson
import os
import HccTD
from HccTD import JsonLocal,TestBlock,RecordStreamingData,Log,TdTradeTest,open_market,Streaming,CollectStreaming
import random
from HccTD import Quan,Smoker
from typing import Dict
import numpy as np
import shutil
import yaml

WORKDIR = os.path.abspath(os.path.dirname(__file__))


def collect_csv():
    symbol_list = []
    with open(os.path.join(WORKDIR, "config", "collect", "collectConfig.yaml"), "r") as f:
        data = yaml.safe_load(f)["collect"]
        for each in data:
            symbol_list.append({"type": "subscribe", "symbol": each["long"]})
            symbol_list.append({"type": "subscribe", "symbol": each["short"]})

    def on_open(ws):

        for each_symbol in symbol_list:
            ws.send(ujson.dumps(each_symbol))

    print(f"collection task would be started...")
    finn_token = HccTD.get_finn_token_from_yaml("collect")
    for index, each_symbol in enumerate(symbol_list):

        symbol = each_symbol["symbol"]
        print(f"{symbol} will start to run in formal environment")
        if index % 2 == 1:
            print("")

    while True:
        time.sleep(1)
        market_status = open_market()

        if market_status:
            ms = CollectStreaming()

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

    collect_csv()



