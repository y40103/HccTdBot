import datetime
import time
import websocket
import ujson
import os
import HccTD
from HccTD import JsonLocal, TestBlock, RecordStreamingData, Log, TdTradeTest, open_market, Streaming, CollectStreaming
import random
from HccTD import Quan, Smoker
from typing import Dict
import numpy as np
import shutil
from typing import List

WORKDIR = os.path.abspath(os.path.dirname(__file__))


def offline_test_from_own_csv(date_set: List[str] = None, long_symbol: str = None, short_symbol: str = None,
                              symbol_para: Dict[str, float] = None):
    if not long_symbol or not short_symbol:
        date_set = ["2022-06-30"]  # UVIX TQQQ SOXL

        long_symbol = "TQQQ"
        short_symbol = "SQQQ"

    long_time, short_time = 0, 0
    win, loss = 0, 0
    win_income, loss_income = 0, 0
    budget = 10000
    worst_loss = []
    log_sys = Log("TEST", "TEST")

    loss_rate_per_day = {

        "WEBL": 0.05,  # 可能樣本太少 待確認
        "WEBS": 0.5,  # 最爛

        "LABU": 0.05,  # 最糟0.1 最佳是賺 取個爛 偏爛那側
        "LABD": 0.15,  # 最遭0.1 最佳 0.03

        "URTY": 0.05,  # 多為負的
        "SRTY": 0.11,  # 大部分都極小 0.03之類 這最糟

        "BULZ": 0.1,
        "BERZ": 0.1,  # 很大 是真的
        "FNGD": 0.1,

        "HIBL": 0.09,  # 樣本太少 需繼續追蹤
        "HIBS": 0.15,  # 樣本太少

        "BOIL": 0.07,  # 樣本太少 需繼續追蹤
        "KOLD": 0.22,  # 樣本太少 需繼續追蹤

        "NRGU": 0.16,  # 樣本太少 需繼續追蹤
        "DRIP": 0.1,  # 樣本太少 需繼續追蹤

        "SOXL": 0.15,  # 樣本太少 需繼續追蹤
        "SOXS": 0.05,  # 樣本太少 需繼續追蹤

        "GDXU": 0.15,
        "JDST": 0.12,

        "TQQQ": 0.05,
        "SQQQ": 0.08,

        "UVIX": 0.05,
        "SVIX": 0.1,

        "UCO": 0.05,
        "SCO": 0.1,

        "AGQ": 0.1,
        "ZSL": 0.13,
        "DUST": 0.1,
    }

    TdTradeTest.long_res, TdTradeTest.short_res = 0, 0
    all_date_performace_res = 0
    all_day_long_performace, all_day_short_performace = 0, 0
    all_each_date_performace = np.zeros(len(date_set))
    for index, date in enumerate(date_set):
        td_trade = TdTradeTest(budget=budget, long_symbol=long_symbol, short_symbol=short_symbol, log_sys=log_sys)
        smoker = Smoker(15, 1, log_sys=log_sys)
        quan = Quan(trade=td_trade, smoker=smoker, symbol_para=symbol_para, log_sys=log_sys)
        test = TestBlock(quan=quan, log_sys=log_sys, date=date)
        test.streaming_data_from_own_csv(date)
        TdTradeTest.long_res += sum(TdTradeTest.performance_Long)
        TdTradeTest.short_res += sum(TdTradeTest.performance_Short)
        long_time += len(TdTradeTest.performance_Long)
        short_time += len(TdTradeTest.performance_Short)

        day_long_performance = sum(TdTradeTest.performance_Long) - loss_rate_per_day.get(long_symbol,0) * (
            len(TdTradeTest.performance_Long)) * budget * 1 / 100
        day_short_performance = sum(TdTradeTest.performance_Short) - loss_rate_per_day.get(short_symbol,0) * len(
            TdTradeTest.performance_Short) * budget * 1 / 100

        day_performance = day_long_performance + day_short_performance

        all_day_long_performace += day_long_performance
        all_day_short_performace += day_short_performance

        all_date_performace_res += day_performance

        if (day_performance) >= 0:
            win += 1
            win_income += (100 * day_performance / budget)
            all_each_date_performace[index] = 100 * day_performance / budget
        elif (day_performance) < 0:
            loss += 1
            loss_income += (100 * day_performance / budget)
            all_each_date_performace[index] = 100 * day_performance / budget
        if day_performance < budget * -0.03:
            worst_loss.append({"data": date, "loss": str(
                100 * (day_performance) / budget) + " %"})

    if loss == 0:
        day_avg_loss = 0
    else:
        day_avg_loss = (loss_income / loss)
    if win == 0:
        day_avg_win = 0
    else:
        day_avg_win = (win_income / win)

    print("\n\n")
    print(f"budget {budget} per day")
    print(f"Long {all_day_long_performace}, long times: {long_time}")
    print(f"short {all_day_short_performace}, short times: {short_time}")
    print(
        f"win_rate {100 * win / (win + loss)} %")
    print(f"P/D {100 * ((all_date_performace_res) / len(date_set)) / budget} %")
    print(f"income {all_day_long_performace + all_day_short_performace}")


    shutil.rmtree(os.path.join(WORKDIR, "log/TEST_TEST"))  # 回測log 保留?

    return 100 * ((all_date_performace_res) / len(date_set)) / budget, (
            100 * win / (win + loss)), (len(worst_loss) / len(date_set)) * 100, (long_time + short_time) / len(
        date_set), [long_time, short_time], worst_loss, [day_avg_win,
                                                         day_avg_loss], all_each_date_performace  # 回傳單日效益(%),win_rate,極值虧損出現機率,平均單日交易次數,總交易次數(long,short),爆倉機率,正/負平均收益



if __name__ == "__main__":
    date_set = ["2022-06-30","2022-07-01"]
    long_symbol = "TQQQ"
    short_symbol = "SQQQ"
    offline_test_from_own_csv(date_set=date_set,long_symbol=long_symbol,short_symbol=short_symbol)
