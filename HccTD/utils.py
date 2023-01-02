import datetime
import time

import ujson
import pytz

import numpy as np
import pandas as pd
import os
import csv
import numpy as np
from typing import Dict, Union, Tuple
import yaml



WORKDIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class JsonLocal():
    def __init__(self):

        self.dir_path = os.path.join(WORKDIR, "account_info")
        self.file_path = os.path.join(self.dir_path, "info.json")
        self.check_dir_exists()

    def check_dir_exists(self):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

    def check_file_exists(self):
        if not os.path.exists(os.path.join(self.file_path)):
            with open(self.file_path, "w") as f:
                pass

    def write(self, dict_info: Dict):
        with open(self.file_path, "w") as json_file:
            ujson.dump(dict_info, json_file)
            json_file.close()

    def read(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as json_file:
                content = ujson.load(json_file)
                json_file.close()

        return content


class ParseJsonHistory():

    def __init__(self):
        self.history_directory = os.path.join(WORKDIR, "streaming_history_csv")
        self.df = None

    def parse_history_to_ndarray(self, filename: str, element_name: str) -> np.array:
        """
        :param filename: e.g. 2022-03-10.csv

        :param element_name:
        datetime,
        pos_average_price,
        pos_latest_price,
        pos_unit_volume,
        inv_average_price,
        inv_latest_price,
        inv_unit_volume

        :return: pd.Series
        """

        target = os.path.join(self.history_directory, filename)

        self.df = pd.read_csv(target, sep=",", header=0)

        return self.df[element_name].to_numpy()


## 目標 , 減少小波動損失(盡量持平) , 賺大波動

class RecordStreamingData():

    def __init__(self, long_symbol: str, short_symbol: str):
        self.long_symbol = long_symbol
        self.long_symbol = short_symbol
        self.dirname = long_symbol + "_" + short_symbol
        self.fold = os.path.join(WORKDIR, "streaming_history_csv")
        self.path = os.path.join(self.fold, self.dirname)

    def __check_directory_exists(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def __get_record_moment(self) -> str:
        us = pytz.timezone('US/Eastern')
        us_now = datetime.datetime.now(us)
        time_format = "%Y-%m-%d-%H:%M:%S"
        us_now = us_now.strftime(time_format)
        return us_now

    def __get_file_name(self) -> str:
        us = pytz.timezone('US/Eastern')
        us_now = datetime.datetime.now(us)
        time_format = "%Y-%m-%d"
        us_now = us_now.strftime(time_format)
        return us_now + ".csv"

    def __init_create(self):
        self.__check_directory_exists()
        file_name = self.__get_file_name()

        if not os.path.exists(os.path.join(self.path, file_name)):
            with open(os.path.join(self.path, file_name), 'w', newline='') as csvfile:
                fieldnames = ["datetime", 'pos_latest_price', 'pos_unit_volume',
                              'inv_latest_price', 'inv_unit_volume']
                writer = csv.writer(csvfile)
                writer.writerow(fieldnames)

    def write(self, latest_pos: float, latest_inv: float, unit_pos_volume: int,
              unit_inv_volume: int):
        record_time = self.__get_record_moment()
        file_name = self.__get_file_name()
        self.__init_create()
        with open(os.path.join(self.path, file_name), 'a+', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([record_time, latest_pos, unit_pos_volume, latest_inv, unit_inv_volume])


class Log():

    def __init__(self, long_symbol: str, short_symbol: str):
        self.long_symbol = long_symbol
        self.short_symbol = short_symbol
        self.fold = os.path.join(WORKDIR, "log")
        self.dirpath = os.path.join(self.fold, self.long_symbol + "_" + self.short_symbol)
        self.file_path = None
        self.existensce_check()
        self.text = []

    def existensce_check(self):
        us = pytz.timezone('US/Eastern')
        now_us = datetime.datetime.now(us)
        time_format = "%Y-%m-%d"
        now_str = now_us.strftime(time_format)

        dir_res = os.path.exists(self.dirpath)
        if not dir_res:
            os.makedirs(self.dirpath)

        res = os.path.exists(f"{self.dirpath}/{now_str}" + ".log")
        self.file_path = f"{self.dirpath}/{now_str}" + ".log"

        if not res:
            with open(self.file_path, "w") as f:
                pass

    def write_time(self):
        self.existensce_check()
        us = pytz.timezone('US/Eastern')
        with open(self.file_path, "a") as f:
            f.write("TW " + datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
            f.write("\n")
            f.write("US/Eastern " + datetime.datetime.now(us).strftime("%Y-%m-%d-%H:%M:%S"))
            f.write("\n")

    def write_log(self):
        self.existensce_check()
        with open(self.file_path, "a") as f:
            for each_line in self.text:
                f.write(each_line + "\n")
            f.write("\n\n\n")

        self.text = []

    def continue_write_log(self):
        self.existensce_check()
        with open(self.file_path, "a") as f:
            for each_line in self.text:
                f.write(each_line + "\n")

        self.text = []


def open_market():
    us = pytz.timezone('US/Eastern')
    us_now = datetime.datetime.now(us)
    start = us_now.replace(hour=9, minute=29, second=0, microsecond=0)
    end = us_now.replace(hour=15, minute=58, second=0, microsecond=0)
    if start.isoweekday() >= 1 and start.isoweekday() <= 5:
        if us_now >= start and us_now <= end:
            return True
        else:
            if us_now.minute % 10 == 0:
                print(f"now: {us_now}")
                print(f"open market: {start} - {end}")
                time.sleep(100)
            elif us_now < end:
                pass
            return False



class Smoker:
    # 用於決策的自定義資料結構 可自訂
    # 類似一個queue , index 0 最新  最尾為最舊  > self.__all_update_min
    # self.smoke 是紀錄 新一項與後一項的差距.
    # self.direction 表示方向

    def __init__(self, period: int, frequency: int, log_sys: Log):
        ## period 為 適用幾分鐘的smoker , frequency 為 每分鐘的頻率
        self.period = period
        self.frequency = frequency
        self.size = period * frequency
        self.index = 0
        self.__all_min_cup = np.zeros(self.size)
        self.__all_update_min = np.zeros(self.size)
        self.smoke = None
        self.part_smoke = None
        self.direction = None

        self.rsi_long = None
        self.rsi_15_long = None
        self.gradient = None

        self.log_sys = log_sys

    def write_log(self):
        self.log_sys.text.append(f"last: {self.__all_min_cup[0:6]}")
        self.log_sys.text.append(f"latest: {self.__all_update_min[0:6]}")

    def add(self, val):
        self.index += 1
        self.__all_min_cup = np.copy(self.__all_update_min)
        self.__all_update_min[1:] = self.__all_min_cup[:self.size - 1]
        self.__all_update_min[0] = val
        self.all_val = self.__all_update_min

        self.write_log()

        if self.index >= (self.size):
            self.smoke = self.__all_update_min[:self.size - 1] - self.__all_min_cup[:self.size - 1]
            self.part_smoke = self.smoke[:self.size // 3]
            self.wave_status(val)

    def wave_status(self, val):
        rsi_15_all = abs(self.smoke).sum()
        rsi_15_long = self.smoke[self.smoke > 0].sum()

        rsi_all = abs(self.smoke[:5]).sum()
        rsi_long = self.smoke[:5][self.smoke[:5] > 0].sum()
        rsi_short = self.smoke[:5][self.smoke[:5] > 0].sum()
        self.gradient = 100 * (self.smoke[0] - self.smoke[1]) / val

        # rsi_all = abs(self.smoke).sum()
        # rsi_long = self.smoke[self.smoke > 0].sum()
        # rsi_short = self.smoke[self.smoke > 0].sum()
        if rsi_all == 0:
            rsi_all = 0.1
        if rsi_15_all == 0:
            rsi_all = 0.1

        self.rsi_long = (rsi_long / rsi_all) * 100

        self.rsi_15_long = (rsi_15_long / rsi_15_all) * 100

        self.log_sys.text.append(f"RSI {self.rsi_long} % RSI_15 {self.rsi_15_long}")
        self.log_sys.text.append(f'gradient {self.gradient}')


class Quan:
    # 處理交易邏輯

    def __init__(self, trade, smoker: Smoker, log_sys: Log, symbol_para: Dict[str, float] = None, formal: bool = False):
        self.smoker = smoker
        self.trade = trade
        self.formal = formal
        self.predict_earns = 0
        self.predict_historial_max_earns = 0
        self.symbol_para = symbol_para

        self.board_count = 0
        self.log_sys = log_sys

    def dynamic_parameter(self) -> Tuple[Union[float, int], Union[float, int]]:

        if self.formal:

            long_parameter = (
                                     sum(self.trade.predict_performance_Long) / self.trade.budget) * 100 / 0.5  # 0.5％的收益或損失 為一個單位
            short_parameter = (
                                      sum(self.trade.predict_performance_Short) / self.trade.budget) * 100 / 0.5  # 0.5％的收益或損失 為一個單位

            # 一方的收益愈大 增加 另一方的上車困難度
        else:
            # long_parameter = (sum(self.trade.performance_Short) / self.trade.budget) * 100 / 0.5  # 0.5％的收益或損失 為一個單位
            # short_parameter = (sum(self.trade.performance_Long) / self.trade.budget) * 100 / 0.5  # 0.5％的收益或損失 為一個單位
            # 一方的收益愈大 增加 另一方的上車困難度
            #
            long_parameter = (sum(self.trade.performance_Long) / self.trade.budget) * 100 / 0.5  # 0.5％的收益或損失 為一個單位
            short_parameter = (sum(self.trade.performance_Short) / self.trade.budget) * 100 / 0.5  # 0.5％的收益或損失 為一個單位
            # 原始想法 合理的

        if long_parameter > 0 and short_parameter > 0:  # 表現好 都不動
            long_parameter = 0
            short_parameter = 0
        elif (long_parameter >= 0 and short_parameter <= 0) and (
                abs(long_parameter) - abs(short_parameter) > 0):  # 多特別突出 參數不動, 空表現不好 減低敏感
            short_parameter = 0
        elif (short_parameter >= 0 and long_parameter <= 0) and (
                abs(short_parameter) - abs(long_parameter) > 0):  # 空特別突出 參數不動, 多表現不好 減低敏感
            long_parameter = 0
        elif (long_parameter >= 0 and short_parameter <= 0) and (abs(long_parameter) - abs(short_parameter) < 0):
            long_parameter = -short_parameter
            # 多的正收益很小 用空的負收益很大(應該是市場多 只是波動很劇烈) 用空的負收益來減少多的靈敏度, 空負收益減少靈敏度

        elif (short_parameter >= 0 and long_parameter <= 0) and (abs(short_parameter) - abs(long_parameter) < 0):
            short_parameter = -long_parameter
            # 空的正收益很小 用多的負收益很大(應該是市場空 只是波動很劇烈) 用多的負收益來減少空的靈敏度, 多負收益減少靈敏度

        elif (long_parameter < 0 and short_parameter < 0) and (abs(long_parameter) - abs(short_parameter) > 0):
            # 兩個表現都不佳 只求虧少
            # long 負收益更大 , 用負收益大的來減少數值 減少 long,short 靈敏度
            short_parameter = -long_parameter
            long_parameter = -long_parameter
        elif (long_parameter < 0 and short_parameter < 0) and (abs(short_parameter) - abs(long_parameter) > 0):
            # 兩個表現都不佳 只求虧少
            # short 負收益更大 , 用負收益大的來減少數值 減少 long,short 靈敏度
            long_parameter = -short_parameter
            short_parameter = -short_parameter

        return long_parameter, short_parameter

    def display_hold_status(self, val1):

        if abs(self.trade.last_hold) > 0:
            self.log_sys.text.append(f"hold {self.trade.last_hold} tunes")

    def entropy(self, array):

        size = len(array)
        abs_val = abs(array[1:] - array[:size - 1]).sum()
        val = (array[1:] - array[:size - 1]).sum()

        return abs_val, val

    def judge_direction(self, val1):
        """
        交易決策 可自定義

        :param val1: long price
        交易基準輸出為 self.smoker.direction = 1,-1,0
        1: 檢視有無持有short, yes: 賣出short,買入long no: 買入long
        -1: 檢視有無持有long, yes > 賣出long,買入short no: 買入short
        0: 檢視有無持有, yes > 全部賣出 no: 不操作
        """

        long_parameter, short_parameter = self.dynamic_parameter()
        # long_parameter, short_parameter =0,0

        if self.smoker.index >= (self.smoker.size):

            part_avg_mo = self.smoker.part_smoke.sum()  # 15分鐘為基準 , 若縮為3分鐘 該數值需*5 (時間縮短1/5 , 基準值需放大5倍)
            all_avg_mo = self.smoker.smoke.sum()
            all_contrast = abs(all_avg_mo / val1) * 100
            part_contrast = abs(part_avg_mo / val1) * 100  # 短期動能表現

            self.display_hold_status(val1)

            act_var = 0.25
            act_var_scalar = 0.05

            # 啟動參數
            if self.trade.long_symbol == "LABU":
                all_contrast_ratio = 0.1
                all_avg_mo_long_rate = 7
                all_avg_mo_short_rate = 2
            elif self.trade.long_symbol == "GDXU":
                all_contrast_ratio = 0.1
                all_avg_mo_long_rate = 5
                all_avg_mo_short_rate = 4
            elif self.trade.long_symbol == "SOXL":
                all_contrast_ratio = 0.2
                all_avg_mo_long_rate = 5
                all_avg_mo_short_rate = 2
            elif self.trade.long_symbol == "BOIL":
                all_contrast_ratio = 0.2
                all_avg_mo_long_rate = 5
                all_avg_mo_short_rate = 2
            elif self.trade.long_symbol == "NRGU":
                all_contrast_ratio = 0.2
                all_avg_mo_long_rate = 4
                all_avg_mo_short_rate = 2
            elif self.trade.long_symbol == "HIBL":
                all_contrast_ratio = 0.1
                all_avg_mo_long_rate = 5
                all_avg_mo_short_rate = 2
            else:  # default
                all_contrast_ratio = 0.1
                all_avg_mo_long_rate = 4
                all_avg_mo_short_rate = 2

            if (part_avg_mo * all_avg_mo > 0 and (
                    all_contrast > all_contrast_ratio)):  ## and self.smoker.all_val.max()==self.smoker.all_val[0]

                if ((part_avg_mo >= 0) and (
                        part_avg_mo > all_avg_mo / all_avg_mo_long_rate)):  # 4 # 如果強 更強 繼續hold  #  保留 and (part_avg_mo < all_avg_mo / 2.5) 此段為強弱轉換時, 給一點buffer 緩衝, 防止平盤時 一直 頻繁多空轉換
                    # 目前需保持 all_avg 25% 以上, 緩漲機率比較高 可以貪婪一點

                    if (
                            part_contrast > (
                            act_var + short_parameter * act_var_scalar)):  # 防止雖然同向 但是短期動能不明顯 , 此時大機率 all_avg 會低於 part_avg (正在走弱) 或是 all_avg也很小 (剛進此區 動能不明確)

                        self.smoker.direction = 1
                        self.log_sys.text.append("上車入口0")
                        self.log_sys.text.append(
                            f"part_contrast > (0.25 + short_parameter * 0.05) {part_contrast} > {(0.25 + short_parameter * 0.05)} ")


                    else:

                        self.smoker.direction = 0  # 符合條件 但是 動能太小
                        self.log_sys.text.append("待機0")
                        self.log_sys.text.append(
                            f"part_contrast < (0.25 + short_parameter * 0.05) {part_contrast} < {(0.25 + short_parameter * 0.05)} ")



                elif ((part_avg_mo < 0) and (
                        part_avg_mo < all_avg_mo / all_avg_mo_short_rate)):  # 2.5 # 若更弱 繼續hold  #  保留 and (part_avg_mo < all_avg_mo / 2.5) 此段為強弱轉換時, 給一點buffer 緩衝, 防止平盤時 一直 頻繁多空轉換
                    # 目前需保持 all_avg 40% 以上, 股票有急跌特性 因此需比較敏感

                    if (part_contrast > (
                            act_var + long_parameter * act_var_scalar)):  # 防止雖然同向 但是短期動能不明顯 , 此時大機率 all_avg 會低於 part_avg (正在走弱) 或是 all_avg也很小 (剛進此區 動能不明確)

                        self.smoker.direction = -1
                        self.log_sys.text.append("上車入口1")
                        self.log_sys.text.append(
                            f"part_contrast > (0.25 + long_parameter * 0.05) {part_contrast} >0.25 + {long_parameter * 0.05}")

                    else:
                        self.smoker.direction = 0
                        self.log_sys.text.append("待機1")
                        self.log_sys.text.append(
                            f"part_contrast < (0.25 + long_parameter * 0.05) , {part_contrast} <0.25 + {long_parameter * 0.05}")



                else:
                    self.smoker.direction = 0  # 其餘情況賣掉
                    self.log_sys.text.append("待機2")



            else:
                self.smoker.direction = 0

            self.lock = 1

            if self.lock == True:


                if self.trade.long_symbol == "LABU":  #機器 823 21min & 15min
                    get_cash_threshold = 0.02
                    tolerance = 0.3
                    rsi_long_ratio = 40
                    rsi_short_ratio = 60
                    self.long_max_lost = 0.02
                    self.short_max_lost = 0.02
                elif self.trade.long_symbol == "NRGU":  # 0814 機器
                    get_cash_threshold = 0.03
                    tolerance = 0.7
                    rsi_long_ratio = 5
                    rsi_short_ratio = 95
                    self.long_max_lost = 0.015
                    self.short_max_lost = 0.015
                elif self.trade.long_symbol == "GDXU":  # 0821 21min
                    get_cash_threshold = 0.035
                    tolerance = 0.7
                    rsi_long_ratio = 40
                    rsi_short_ratio = 60
                    self.long_max_lost = 0.02
                    self.short_max_lost = 0.02
                elif self.trade.long_symbol == "URTY":  # 0710 機器
                    get_cash_threshold = 0.015
                    tolerance = 0.7
                    rsi_long_ratio = 10
                    rsi_short_ratio = 90
                    self.long_max_lost = 0.01
                    self.short_max_lost = 0.01
                elif self.trade.long_symbol == "WEBL":  # 0814 機器
                    get_cash_threshold = 0.0325
                    tolerance = 0.6
                    rsi_long_ratio = 40
                    rsi_short_ratio = 60
                    self.long_max_lost = 0.0125
                    self.short_max_lost = 0.0125
                elif self.trade.long_symbol == "HIBL":  # 0807
                    get_cash_threshold = 0.0175
                    tolerance = 0.7
                    rsi_long_ratio = 15
                    rsi_short_ratio = 85
                    self.long_max_lost = 0.0175
                    self.short_max_lost = 0.0175
                elif self.trade.long_symbol == "BULZ":  # 0807機器找
                    get_cash_threshold = 0.04
                    tolerance = 0.5
                    rsi_long_ratio = 60
                    rsi_short_ratio = 40
                    self.long_max_lost = 0.0175
                    self.short_max_lost = 0.0175
                elif self.trade.long_symbol == "BOIL":  # 機器 0821 21min
                    get_cash_threshold = 0.015
                    tolerance = 0.3
                    rsi_long_ratio = 15
                    rsi_short_ratio = 85
                    self.long_max_lost = 0.0175
                    self.short_max_lost = 0.0175
                elif self.trade.long_symbol == "SOXL":  # 機器找的 一個月 0823 21n
                    get_cash_threshold = 0.0275
                    tolerance = 0.3
                    rsi_long_ratio = 5
                    rsi_short_ratio = 95
                    self.long_max_lost = 0.0175
                    self.short_max_lost = 0.0175
                elif self.trade.long_symbol == "UVIX":  # 815 0701
                    get_cash_threshold = 0.0225
                    tolerance = 0.7
                    rsi_long_ratio = 30
                    rsi_short_ratio = 70
                    self.long_max_lost = 0.0125  # 0.01 - 0.02
                    self.short_max_lost = 0.0125
                elif self.trade.long_symbol == "TQQQ":  # 0804
                    get_cash_threshold = 0.03
                    tolerance = 0.7
                    rsi_long_ratio = 20
                    rsi_short_ratio = 80
                    self.long_max_lost = 0.01
                    self.short_max_lost = 0.01
                elif self.trade.long_symbol == "UCO":  # 0807
                    get_cash_threshold = 0.0125
                    tolerance = 0.55
                    rsi_long_ratio = 30
                    rsi_short_ratio = 70
                    self.long_max_lost = 0.01
                    self.short_max_lost = 0.01
                elif self.trade.long_symbol == "AGQ":  # 0728-
                    get_cash_threshold = 0.0175
                    tolerance = 0.6
                    rsi_long_ratio = 25
                    rsi_short_ratio = 75
                    self.long_max_lost = 0.0125
                    self.short_max_lost = 0.0125
                else:
                    raise "can't get default parapmeter"

                if self.symbol_para:
                    get_cash_threshold = self.symbol_para["threshold"]
                    tolerance = self.symbol_para["tolerance"]
                    rsi_long_ratio = self.symbol_para["rsi_long"]
                    rsi_short_ratio = self.symbol_para["rsi_short"]
                    self.long_max_lost = self.symbol_para["long_max_lost"]
                    self.short_max_lost = self.symbol_para["short_max_lost"]

                if self.trade.last_hold > 0 and self.trade.last_price:  # 鎖住

                    if (val1 < self.trade.last_price and (
                            self.smoker.rsi_long <= rsi_long_ratio)):  # or self.smoker.gradient>-0.5
                        # or ((self.smoker.gradient > -0.1 and (self.smoker.smoke[0]<0)) and val1 < self.trade.last_price)
                        # 負-負 > -0.1  捕捉 正轉負 瞬間 , 後者比前者 還小 -3- -5 = 2

                        self.smoker.direction = -1

                        if self.trade.long_symbol in ["LABU"]:
                            if all_contrast < 0.15 and part_contrast < 0.1:  # LABU GDXU
                                self.smoker.direction = 1
                                self.log_sys.text.append(f" {all_contrast} < 0.15 % and {part_contrast}< 0.1 % 準備下車")

                            elif (100 * abs(
                                    val1 - self.trade.last_price) / self.trade.last_price < 0.003 and self.smoker.rsi_long > rsi_long_ratio * 0.33):
                                self.smoker.direction = 1

                            else:
                                self.log_sys.text.append(
                                    f"lastest price {val1} < hold price {self.trade.last_price} ,rsi long {self.smoker.rsi_long} < limit rsi {rsi_short_ratio}")
                    else:
                        self.log_sys.text.append("still keep long...")
                        self.smoker.direction = 1

                elif self.trade.last_hold < 0 and self.trade.last_price:

                    if (val1 > self.trade.last_price and (
                            self.smoker.rsi_long >= rsi_short_ratio)):  # or self.smoker.gradient<0.5
                        # or ((self.smoker.gradient < 0.1 and (self.smoker.smoke[0]>0)) and val1 > self.trade.last_price)
                        # 正-正 < 0.1 捕捉 負轉正 瞬間 , 後者比前者大 3-5 = -2

                        self.smoker.direction = 1

                        if self.trade.long_symbol in ["LABU"]:
                            if all_contrast < 0.15 and part_contrast < 0.1:  # LABU GDXU
                                self.smoker.direction = -1
                                self.log_sys.text.append(f" {all_contrast} < 0.15 % and {part_contrast}< 0.1 % 準備下車")

                            elif (100 * abs(
                                    val1 - self.trade.last_price) / self.trade.last_price < 0.003 and self.smoker.rsi_long > rsi_long_ratio * 0.33):
                                self.smoker.direction = -1
                            else:
                                self.log_sys.text.append(
                                    f"lastest price {val1} > hold price {self.trade.last_price} ,rsi long {self.smoker.rsi_long} >= limit rsi {rsi_short_ratio}")

                    else:
                        self.log_sys.text.append("still keep short...")
                        self.smoker.direction = -1

                if self.trade.last_hold != 0 and (
                        self.smoker.direction == 1 and (val1 > self.trade.best_price)):  # 二次之後 更新最大值
                    self.trade.best_price = val1
                elif self.trade.last_hold != 0 and self.smoker.direction == -1 and (val1 < self.trade.best_price):
                    self.trade.best_price = val1

                if self.trade.best_price and self.trade.last_price:  # 階段回收

                    if (abs((
                                    self.trade.best_price - self.trade.last_price) / self.trade.last_price) > get_cash_threshold) and (
                            abs(val1 - self.trade.last_price)) / abs(
                        self.trade.best_price - self.trade.last_price) < tolerance:
                        self.log_sys.text.append(
                            f">{get_cash_threshold} {abs((self.trade.best_price - self.trade.last_price) / self.trade.last_price)},>{tolerance} {(abs(val1 - self.trade.last_price)) / abs(self.trade.best_price - self.trade.last_price)}")
                        self.smoker.direction = 0
                        self.board_count = 0

            if self.formal:
                long_performace = self.trade.predict_performance_Long
                short_performace = self.trade.predict_performance_Short
            else:
                long_performace = self.trade.performance_Long
                short_performace = self.trade.performance_Short

            if sum(long_performace) < -self.trade.budget * self.long_max_lost and self.smoker.direction == 1:
                self.log_sys.text.append(
                    f"long performance {sum(long_performace)} < - {self.trade.budget * self.long_max_lost}, lock 0")
                self.smoker.direction = 0
            if sum(short_performace) < -self.trade.budget * self.short_max_lost and self.smoker.direction == -1:
                self.log_sys.text.append(
                    f"long performance {sum(short_performace)} < - {self.trade.budget * self.short_max_lost}, lock 0")
                self.smoker.direction = 0

            if self.trade.long_symbol == "GDXU":  # 特殊止盈 #0814版本
                # if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 1.5: # 0814 15m
                #     self.smoker.direction = 0
                # if 100 * (sum(short_performace) + sum(
                #         long_performace)) / self.trade.budget < -1.05 * 100 * self.long_max_lost:  # 整體止損
                #     self.smoker.direction = 0
                if self.trade.long_symbol == "GDXU":  # 0821 21min
                    if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 1.25:
                        self.smoker.direction = 0
                    if 100 * (sum(short_performace) + sum(
                            long_performace)) / self.trade.budget < -1.25 * 100 * self.long_max_lost:  # 整體止損
                        self.smoker.direction = 0
            elif self.trade.long_symbol == "LABU":  # 特殊止盈
                # if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 5.25:  # 0802
                #     self.smoker.direction = 0
                # if 100 * (sum(short_performace) + sum(
                #         long_performace)) / self.trade.budget < -1.6 * 100 * self.long_max_lost:  # 整體止損
                #     self.smoker.direction = 0
                # if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 2.25:  #  # 機器 822 0.04 30/70  21min & 15min
                #     self.smoker.direction = 0
                # if 100 * (sum(short_performace) + sum(
                #         long_performace)) / self.trade.budget < -1.6 * 100 * self.long_max_lost:  # 整體止損
                #     self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 0.2:  #  # 機器 822 0.04 30/70  21min & 15min
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -1.6 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0

            elif self.trade.long_symbol == "NRGU":
                # if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 3.5:
                #     self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 2.5:
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "BOIL":
                # if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 1.25:
                #     self.smoker.direction = 0
                # if 100 * (sum(short_performace) + sum(
                #         long_performace)) / self.trade.budget < -1.8 * 100 * self.long_max_lost:  # 整體止損
                #     self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 0.2:  # 08/21 21min
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -1.8 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "TQQQ":
                # if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 1.25:
                #     self.smoker.direction = 0
                # if 100 * (sum(short_performace) + sum(
                #         long_performace)) / self.trade.budget < -1.25 * 100 * self.long_max_lost:  # 整體止損
                #     self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 1.25:
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -1.25 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "SOXL":
                # if 100 * (
                #         sum(short_performace) + sum(long_performace)) / self.trade.budget > 0.8:  # 整體止盈 # 0.0375 0.0125
                #     self.smoker.direction = 0
                # if 100 * (sum(short_performace) + sum(
                #         long_performace)) / self.trade.budget < -1.8 * 100 * self.long_max_lost:  # 整體止損
                #     self.smoker.direction = 0
                if 100 * (
                        sum(short_performace) + sum(long_performace)) / self.trade.budget > 0.5:  # 整體止盈 # 0823 21m
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -1.8 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "HIBL":
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 3:  # 整體止盈
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -2 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "URTY":
                # if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 0.6:  # 整體止盈
                #     self.smoker.direction = 0
                # if 100 * (sum(short_performace) + sum(
                #         long_performace)) / self.trade.budget < -1.5 * 100 * self.long_max_lost:  # 整體止損
                #     self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 1:  # 整體止盈 0.15
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -1.3 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "UCO":
                # if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 1.2:  # 整體止盈
                #     self.smoker.direction = 0
                # if 100 * (sum(short_performace) + sum(
                #         long_performace)) / self.trade.budget < -1.5 * 100 * self.long_max_lost:  # 整體止損
                #     self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 0.8:  # 整體止盈
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -1.5 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "AGQ":
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 1:
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "BULZ":
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 2:
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -1.8 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "WEBL":
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 0.8:
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -1.2 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0
            elif self.trade.long_symbol == "UVIX":
                if 100 * (sum(short_performace) + sum(long_performace)) / self.trade.budget > 1.25:
                    self.smoker.direction = 0
                if 100 * (sum(short_performace) + sum(
                        long_performace)) / self.trade.budget < -1.2 * 100 * self.long_max_lost:  # 整體止損
                    self.smoker.direction = 0

            self.announce(val1)

    def announce(self, val1):


        self.log_sys.text.append(
            f"avg_acc_all: {100 * self.smoker.smoke.sum() / val1} %, avg_acc_part: {100 * self.smoker.part_smoke.sum() / val1} %")
        self.log_sys.text.append(
            f"smoke: {self.smoker.smoke}, direction {self.smoker.direction}")

        self.log_sys.text.append(f"current hold price {self.trade.last_price}, latest {val1}")
        if self.trade.best_price:
            self.log_sys.text.append(
                f"best price {self.trade.best_price}, max {abs(self.trade.best_price - self.trade.last_price) / self.trade.last_price} , actual {abs(val1 - self.trade.last_price) / self.trade.last_price}")

    def streaming(self, real_val1, real_val2, real_volume1=None, last=None):
        """
        :param real_val1: pos_lastest_mo
        :param real_val2: inv_lastest_mo
        :param last: last_date will be true, default is None
        :return:
        """

        self.smoker.add(val=real_val1)
        self.judge_direction(real_val1)

        if last:
            self.smoker.direction = 0

        if self.smoker.direction is not None:

            if self.smoker.direction == 1:

                self.trade.sell_n(real_val2)
                self.trade.buy(real_val1)




            elif self.smoker.direction == -1:

                self.trade.sell(real_val1)
                self.trade.buy_n(real_val2, real_val1)



            elif self.smoker.direction == 0:
                self.trade.sell_n(real_val2)
                self.trade.sell(real_val1)

        res = self.trade.announce()

        if res:
            self.log_sys.text += res



# 動能判斷買賣後 , trade 處理買賣邏輯 , trade 再call 某券商的執行模塊


class TdTradeTest:
    keep1 = 0
    keep2 = 0
    performance_Long = []
    performance_Short = []

    long_res = 0
    short_res = 0

    def __init__(self, budget: float, long_symbol: str, short_symbol: str, log_sys: Log):
        self.budget = budget
        self.long_symbol = long_symbol
        self.short_symbol = short_symbol

        self.cost1 = 0
        self.income1 = 0

        self.cost2 = 0
        self.income2 = 0

        self.description = []

        self.last_direction = None
        self.last_hold = 0

        TdTradeTest.performance_Long = []
        TdTradeTest.performance_Short = []

        self.last_price = None
        self.best_price = None

        self.second_last_price = None

        self.log_sys = log_sys

    def buy(self, price):

        if TdTradeTest.keep1 == 0:
            TdTradeTest.keep1 = self.budget // price

            self.cost1 = self.keep1 * price

            ms = f"buy Long {price} * {TdTradeTest.keep1} = {self.cost1}"

            self.log_sys.text.append(ms)
            self.last_price = price
            self.best_price = price

        self.last_hold += 1

    def sell(self, price):
        if TdTradeTest.keep1:
            self.income1 = TdTradeTest.keep1 * price

            TdTradeTest.performance_Long.append(self.income1 - self.cost1)

            ms1 = f"sell Long {price} * {TdTradeTest.keep1} = {self.income1}"
            self.log_sys.text.append(ms1)
            ms2 = f"Long earns {self.income1} - {self.cost1} = {self.income1 - self.cost1}"
            self.log_sys.text.append(ms2)


            self.budget += (self.income1 - self.cost1)
            self.income1, self.cost1 = 0, 0
            TdTradeTest.keep1 = 0
            self.last_hold = 0
            self.best_price = None
            self.last_price = None

    def buy_n(self, price2, price=None):

        if TdTradeTest.keep2 == 0:
            TdTradeTest.keep2 = self.budget // price2

            self.cost2 = self.keep2 * price2


            self.log_sys.text.append(f"buy Short {price2} * {TdTradeTest.keep2} = {self.cost2}")
            self.best_price = price
            self.last_price = price

        self.last_hold -= 1

    def sell_n(self, price2, price1=None):
        if TdTradeTest.keep2:
            self.income2 = TdTradeTest.keep2 * price2

            TdTradeTest.performance_Short.append(self.income2 - self.cost2)


            self.log_sys.text.append(f"sell Short {price2} * {TdTradeTest.keep2} = {self.income2}")
            self.log_sys.text.append(f"Short earns {self.income2} - {self.cost2} = {self.income2 - self.cost2}")

            self.budget += (self.income2 - self.cost2)
            self.income2, self.cost2 = 0, 0
            TdTradeTest.keep2 = 0
            self.last_hold = 0
            self.best_price = None
            self.last_price = None

    def announce(self):
        if TdTradeTest.keep1:

            self.log_sys.text.append(f"hold Long {TdTradeTest.keep1} shares")
        elif TdTradeTest.keep2:

            self.log_sys.text.append(f"hold Short {TdTradeTest.keep2} shares")
        else:
            self.log_sys.text.append(f"No hold")




class EntryPoint():
    """  if time in time range , it will return True and each condition will only be activated once every circle"""
    lock = 0

    temp_minute = None

    def __init__(self):

        self.time_range = [[5, 59]]  # 0-10秒 , 30-40秒 各處發一次

    def check(self, second):
        if len(self.time_range) > 1:
            if self.lock in range(len(self.time_range)):

                if (second >= self.time_range[self.lock][0]) and (second < self.time_range[self.lock][1]):

                    EntryPoint.lock += 1

                    if self.lock == len(self.time_range):  # 最後一組 回到預設值
                        EntryPoint.lock = 0

                    return True

                return False

        else:

            if EntryPoint.temp_minute != datetime.datetime.now().minute or EntryPoint.temp_minute is None:

                if (second >= self.time_range[0][0]) and (second < self.time_range[0][1]):
                    EntryPoint.temp_minute = datetime.datetime.now().minute

                    return True

            return False


class Streaming():

    @staticmethod
    def get_miner_time(start: datetime.datetime, end: datetime.datetime) -> int:
        gap = end - start

        return gap.seconds // 60

    ## 資料串流

    def __init__(self, quan: Quan, streaming_csv_log: RecordStreamingData, log_sys: Log, formal: bool = False):
        self.Q = quan
        self.time_sec = None

        self.long_latest = None
        self.short_latest = None

        self.pos_unit_volume = 0  # 單位時間內的 交易量總和
        self.inv_unit_volume = 0

        self.formal = formal

        self.streaming_csv_log = streaming_csv_log

        self.entry_point = EntryPoint()

        self.log_sys = log_sys

    def get_price_vol_from_jsonDict(self, data):

        long_dalta_v = 0
        long_dalta_p = 0
        short_dalta_v = 0
        short_dalta_p = 0
        for each in data:
            symbol_ = each["s"]
            if symbol_ == self.Q.trade.long_symbol:
                long_vol = each["v"]
                long_price = each["p"]
                long_dalta_p += (long_price * long_vol)
                long_dalta_v += long_vol
            elif symbol_ == self.Q.trade.short_symbol:
                short_vol = each["v"]
                short_price = each["p"]
                short_dalta_p += (short_price * short_vol)
                short_dalta_v += short_vol

        return symbol_, long_dalta_v, long_dalta_p, short_dalta_v, short_dalta_p

    def write_log(self):
        self.log_sys.write_time()

        self.log_sys.text.append(f"budget {self.Q.trade.budget}")

        self.log_sys.text.append(f"Long symbol: {self.Q.trade.long_symbol}, Short symbol: {self.Q.trade.short_symbol}")
        self.log_sys.text.append(f"Long latest {self.long_latest}, Short latest {self.short_latest}")

        self.log_sys.text.append(f"Long volume {self.pos_unit_volume}, short volume {self.inv_unit_volume}")
        self.log_sys.text.append(f"Long_performance_list = {self.Q.trade.performance_Long}")
        self.log_sys.text.append(f"Long_performance = {sum(self.Q.trade.performance_Long)}")
        self.log_sys.text.append(f"Short_performance_list = {self.Q.trade.performance_Short}")
        self.log_sys.text.append(f"Short_performance = {sum(self.Q.trade.performance_Short)}")

        if self.formal:

            size = len(self.Q.trade.predict_performance_Long)
            if size == 0:
                size = 1

            self.log_sys.text.append(f"predict_Long_performance_list = {self.Q.trade.predict_performance_Long}")
            self.log_sys.text.append(f"predict_Long_performance = {sum(self.Q.trade.predict_performance_Long)}")
            self.log_sys.text.append(f"predict_Short_performance_list = {self.Q.trade.predict_performance_Short}")
            self.log_sys.text.append(f"predict_Short_performance = {sum(self.Q.trade.predict_performance_Short)}")
            self.log_sys.text.append(
                f"predict_Long_loss = {100 * (sum(self.Q.trade.predict_performance_Long) - sum(self.Q.trade.performance_Long)) / self.Q.trade.budget} %, avg_loss_per_trade = {100 * ((sum(self.Q.trade.predict_performance_Long) - sum(self.Q.trade.performance_Long)) / self.Q.trade.budget) / size} %")
            self.log_sys.text.append(
                f"predict_Short_loss = {100 * (sum(self.Q.trade.predict_performance_Short) - sum(self.Q.trade.performance_Short)) / self.Q.trade.budget} %, avg_loss_per_trade = {100 * ((sum(self.Q.trade.predict_performance_Short) - sum(self.Q.trade.performance_Short)) / self.Q.trade.budget) / size} %")

        self.log_sys.write_log()

    def on_close(self, ws):
        pass
    def on_error(self, ws, error):
        pass

    def on_message(self, ws, message):

        self.time_sec = datetime.datetime.now().second

        dict_data = ujson.loads(message)
        data = dict_data.get("data", None)

        if data:
            symbol, long_dalta_v, long_dalta_p, short_dalta_v, short_dalta_p = self.get_price_vol_from_jsonDict(data)

            if symbol == self.Q.trade.long_symbol and (long_dalta_v and long_dalta_p):
                self.long_latest = long_dalta_p / long_dalta_v
                self.pos_unit_volume += long_dalta_v
            elif symbol == self.Q.trade.short_symbol and (short_dalta_v, short_dalta_p):
                self.short_latest = short_dalta_p / short_dalta_v
                self.inv_unit_volume += short_dalta_v
            else:
                return

            non_nan = ((self.short_latest == self.short_latest) and (self.long_latest == self.long_latest))

            if self.Q.trade.long_symbol == self.Q.trade.short_symbol:
                self.short_latest = self.long_latest
                self.inv_unit_volume = self.pos_unit_volume

            if (self.long_latest and self.short_latest) and non_nan:

                if self.entry_point.check(self.time_sec):
                    self.Q.streaming(self.long_latest, self.short_latest)

                    self.write_log()
                    self.streaming_csv_log.write(latest_pos=self.long_latest, latest_inv=self.short_latest,
                                                 unit_pos_volume=self.pos_unit_volume,
                                                 unit_inv_volume=self.inv_unit_volume)

                    self.pos_unit_volume, self.inv_unit_volume = 0, 0


        else:
            if dict_data.get("type", None) == "ping":
                ws.close()

        if not open_market():
            self.Q.streaming(self.long_latest, self.short_latest, last=True)
            self.write_log()

            ws.close()


class CsvCollect():
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.delta_volume = 0
        self.unit_volume = 0
        self.delta_price = 0
        self.latest_price = None

    def settle(self):
        if self.delta_price and self.delta_volume:
            self.latest_price = self.delta_price / self.delta_volume
            self.unit_volume += self.delta_volume
            self.delta_price, self.delta_volume = 0, 0

    def reset(self):
        self.latest_price = None
        self.unit_volume = 0
        self.delta_price, self.delta_volume = 0, 0


class CollectStreaming():


    ## 資料串流

    def __init__(self):
        self.time_sec = None
        self.group = []
        self.csv_instance_set = {}
        self.__parse_symbol_from_config()

        self.entry_point = EntryPoint()
        self.time_sec = None

    def __parse_symbol_from_config(self):

        with open(os.path.join(WORKDIR,"config","collect","collectConfig.yaml"),"r") as f:
            data = yaml.safe_load(f)["collect"]
            for each in data:
                self.group.append([each["long"],each["short"]])
                self.csv_instance_set[each["long"]] = CsvCollect(each["long"])
                self.csv_instance_set[each["short"]] = CsvCollect(each["short"])


    def get_price_vol_from_jsonDict(self, data):

        symbol_set = []
        for each in data:
            symbol_ = each["s"]
            symbol_set.append(symbol_)
            vol = each["v"]
            price = each["p"]
            self.csv_instance_set[symbol_].delta_price += (price * vol)
            self.csv_instance_set[symbol_].delta_volume += vol

        for each_symbol in set(symbol_set):
            self.csv_instance_set[each_symbol].settle()

        return set(symbol_set)

    def on_close(self, ws):
        print("clear all shares")

    def on_error(self, ws, error):
        print(error)

    def on_message(self, ws, message):

        self.time_sec = datetime.datetime.now().second

        dict_data = ujson.loads(message)
        data = dict_data.get("data", None)

        if data:
            self.get_price_vol_from_jsonDict(data)

            if self.entry_point.check(self.time_sec):
                for each_group in self.group:

                    long = self.csv_instance_set[each_group[0]]
                    short = self.csv_instance_set[each_group[1]]

                    if long.latest_price and short.latest_price:
                        streaming_csv_log = RecordStreamingData(long_symbol=long.symbol, short_symbol=short.symbol)
                        streaming_csv_log.write(latest_pos=long.latest_price, latest_inv=short.latest_price,
                                                unit_pos_volume=long.unit_volume,
                                                unit_inv_volume=short.unit_volume)
                        long.reset()
                        short.reset()




        else:
            if dict_data.get("type", None) == "ping":
                ws.close()

        if not open_market():
            ws.close()


class TestBlock():

    def __init__(self, quan: Quan, log_sys: Log, date: str = None, ):  # period: times/min
        self.quan = quan
        self.date = date

        self.td_history_temp_pos = None
        self.td_history_temp_inv = None

        self.log_sys = log_sys

    def write_log(self):

        self.log_sys.text.append(f"Long_performance_list = {self.quan.trade.performance_Long}")
        self.log_sys.text.append(f"Long_performance = {sum(self.quan.trade.performance_Long)}")
        self.log_sys.text.append(f"Short_performance_list = {self.quan.trade.performance_Short}")
        self.log_sys.text.append(f"Short_performance = {sum(self.quan.trade.performance_Short)}")

        self.log_sys.write_log()

    def streaming_data_from_own_csv(self, date: str):
        """
        :param date:  e.g  2022-03-10
        """

        filename = date + ".csv"

        csv_parser = ParseJsonHistory()

        filename = f"{self.quan.trade.long_symbol}_{self.quan.trade.short_symbol}/" + filename

        moment = csv_parser.parse_history_to_ndarray(filename=filename,
                                                     element_name="datetime")
        pos_latest_price = csv_parser.parse_history_to_ndarray(filename=filename,
                                                               element_name="pos_latest_price")
        inv_latest_price = csv_parser.parse_history_to_ndarray(filename=filename,
                                                               element_name="inv_latest_price")
        pos_latest_volume = csv_parser.parse_history_to_ndarray(filename=filename, element_name="pos_unit_volume")

        size = len(pos_latest_price)

        last_status = False

        for each_scale_index in range(size):

            # if each_scale_index % 2 ==1: # 30秒資料 套1分鐘
            #     continue

            if each_scale_index == (size - 1):
                last_status = True

            if (pos_latest_price[each_scale_index] == pos_latest_price[each_scale_index]) and (
                    inv_latest_price[each_scale_index] == inv_latest_price[each_scale_index]):  ## 防止載入 nan

                self.log_sys.text.append(moment[each_scale_index])
                self.quan.streaming(real_val1=pos_latest_price[each_scale_index],
                                    real_val2=inv_latest_price[each_scale_index], last=last_status)

            self.write_log()



