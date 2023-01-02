import datetime
import time

import ujson
from tda import auth
import tda
from typing import Union, Dict
from tda.orders.common import Duration, Session
import numpy as np
import os

work_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class json_local():
    def __init__(self):
        self.dir_path = os.path.join(work_dir,"account_info")
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


class ClientExtend():
    """ 
    TD 帳號基本操作簡易封裝
    """

    def __init__(self, client: tda.client.Client, account_id: str):
        self.__tda_client = client
        self.account_id = account_id

    def qualified_for_day_trading(self):

        verify_point = np.zeros(2)
        account_info = self.__tda_client.get_account(self.account_id).json()["securitiesAccount"]
        account_type = account_info["type"]
        account_value = account_info["initialBalances"]["accountValue"]

        if account_type == "MARGIN":
            verify_point[0] = 1
        if (account_value - 25000.0) > 0:
            verify_point[1] = 1
        if verify_point.sum() != 2:
            return False

    def get_position_symbol_info(self, symbol: str) -> Union[Dict[str, str], None]:

        account = self.__tda_client.get_account(self.account_id, fields=self.__tda_client.Account.Fields.POSITIONS)
        if account.status_code == 200:
            account_position = account.json()["securitiesAccount"]["positions"]
            for each_symbol in account_position:
                if each_symbol["instrument"]["symbol"] == symbol:

                    if each_symbol["longQuantity"] > 0:
                        return {"Symbol": symbol, "Average_price": each_symbol["averagePrice"],
                                "Quantity": each_symbol["longQuantity"]}
                    elif each_symbol["shortQuantity"] > 0:
                        return {"Symbol": symbol, "Average_price": each_symbol["averagePrice"],
                                "Quantity": each_symbol["shortQuantity"]}
        return None

    def get_cash_balance(self):
        """
        cash 餘額 , 待測試 當沖會不會有
        :return: 帳戶現金
        """
        try:
            account = self.__tda_client.get_account(self.account_id)
            if account.status_code == 200:
                account_info = account.json()["securitiesAccount"]
                account_cash_balance = account_info["currentBalances"]["cashBalance"]
                return account_cash_balance
        except Exception as e:
            print(e)
            time.sleep(3)
            account = self.__tda_client.get_account(self.account_id)
            if account.status_code == 200:
                account_info = account.json()["securitiesAccount"]
                account_cash_balance = account_info["currentBalances"]["cashBalance"]
                return account_cash_balance

    def buy_by_market(self, symbol: str, share_quantities: int):

        self.__tda_client.place_order(
            self.account_id,
            tda.orders.equities.equity_buy_market(symbol, share_quantities).set_duration(
                Duration.DAY).set_session(Session.NORMAL).build())

    def sell_by_market(self, symbol: str, share_quantities: int):

        # position_info = self.get_position_symbol_info(symbol)

        # if position_info and (position_info.get("Quantity", 0) >= share_quantities):

        self.__tda_client.place_order(
            self.account_id,
            tda.orders.equities.equity_sell_market(symbol, share_quantities).set_duration(
                Duration.DAY).set_session(Session.NORMAL).build())

    def buy_by_limit(self, symbol: str, share_quantities: int, price: float):
        self.__tda_client.place_order(
            self.account_id,
            tda.orders.equities.equity_buy_limit(symbol, share_quantities, price).set_duration(
                Duration.DAY).set_session(Session.NORMAL).build())

    def sell_by_limit(self, symbol: str, share_quantities: int, price: float):
        self.__tda_client.place_order(
            self.account_id,
            tda.orders.equities.equity_sell_limit(symbol, share_quantities, price).set_duration(
                Duration.DAY).set_session(Session.NORMAL).build())

    def sell_short_by_market(self, symbol: str, share_quantities: int):
        """ begin short symbol"""

        self.__tda_client.place_order(self.account_id,
                                      tda.orders.equities.equity_sell_short_market(symbol,
                                                                                   share_quantities).set_duration(
                                          Duration.DAY).build())

    def buy_to_cover_by_market(self, symbol: str, share_quantities: int):
        """ finish short symbol """

        self.__tda_client.place_order(self.account_id,
                                      tda.orders.equities.equity_buy_to_cover_market(symbol,
                                                                                     share_quantities).set_duration(
                                          Duration.DAY).set_session(Session.NORMAL).build())


class TdAccount_middle():
    """
    多包一層的middleware , 可以直接替代原本的 模擬交易code
    """
    keep1 = 0
    keep2 = 0
    performance_Long = []
    performance_Short = []

    predict_performance_Long = []
    predict_performance_Short = []

    def __init__(self, budget: float, td_account: ClientExtend, long_symbol: str, short_symbol: str):
        self.budget = budget

        self.cost1 = 0
        self.income1 = 0

        self.cost2 = 0
        self.income2 = 0

        self.predict_cost1 = 0
        self.predict_cost2 = 0

        self.description = []

        self.last_direction = None
        self.last_hold = 0

        self.client = td_account

        self.long_symbol = long_symbol
        self.short_symbol = short_symbol

        self.log_sys = []
        self.json_sys = json_local()

        self.account_cash = None

        self.account_cash = self.get_account_cash_from_local()

        self.last_price = None
        self.best_price = None

    def update_account_status_after_operating(self, symobl: str, operator: str) -> Union[Dict, None]:
        """
        :param symobl: stock symbol
        :param operator: selling or buying
        :return: account_symbol_info or None
        """

        if operator == "selling":

            print(f"wait to update account information after {operator} or holding {symobl} symbols")
            account_symbol_info = self.client.get_position_symbol_info(symobl)
            return account_symbol_info  # None

        elif operator == "buying":

            print(f"wait to update account information after {operator} or holding {symobl} symbols")
            account_symbol_info = self.client.get_position_symbol_info(symobl)

            return account_symbol_info  # symbol info

        else:
            raise "update_account_status_after_operating something wrong happened"

    def verify_local_and_online_symbols_holding(self, long_or_short: str):

        if long_or_short == "long":
            symbols = self.long_symbol
            hold_quantities = TdAccount_middle.keep1
        elif long_or_short == "short":
            symbols = self.short_symbol
            hold_quantities = TdAccount_middle.keep2
        else:
            raise "Please choose long or short"

        for each in range(2):
            time.sleep(1.5)
            account_symbol_info = self.client.get_position_symbol_info(symbols)
            if account_symbol_info:
                break
            time.sleep(1)

        if account_symbol_info:
            real_hold_shares = int(account_symbol_info["Quantity"])
        else:
            real_hold_shares = 0

        if real_hold_shares == hold_quantities:
            print("Verification result : SUCCESS")
            self.log_sys.append("Verification result : SUCCESS")
        else:
            print("Verification result : FAIL")
            self.log_sys.append("Verification result : FAIL")

        if long_or_short == "long":
            TdAccount_middle.keep1 = real_hold_shares
            if TdAccount_middle.keep1 == 0:
                self.last_hold = 0

        elif long_or_short == "short":
            TdAccount_middle.keep2 = real_hold_shares
            if TdAccount_middle.keep2 == 0:
                self.last_hold = 0

    def get_account_cash_from_local(self):

        if not self.account_cash:
            account_info = {}
            self.account_cash = self.client.get_cash_balance()
            account_info["account_cash"] = self.account_cash
            self.json_sys.write(account_info)

        account_cash = self.json_sys.read()["account_cash"]

        return account_cash

    def update_account_cash_to_json(self):
        if self.account_cash:
            json_content = self.json_sys.read()
            json_content["account_cash"] = self.account_cash
            self.json_sys.write(json_content)

    def buy(self, price1):

        t1 = time.time()
        account_symbol_info = None
        count = 3

        if (TdAccount_middle.keep1 == 0) and (price1 != 0):

            TdAccount_middle.keep1 = self.budget // price1  ## 現有價格粗略計算要買多少

            if TdAccount_middle.keep1 > 0:

                self.client.buy_by_market(self.long_symbol, TdAccount_middle.keep1)  # 下單

                while (account_symbol_info is None) and (count > 0):
                    count -= 1
                    time.sleep(3)
                    print(f"準備驗證buy {count}")
                    account_symbol_info = self.update_account_status_after_operating(self.long_symbol, "buying")
                    print("check buy long status")

                if account_symbol_info:  # 確認買到
                    self.cost1 = TdAccount_middle.keep1 * account_symbol_info["Average_price"]

                    self.predict_cost1 = TdAccount_middle.keep1 * price1

                    avg_price1 = account_symbol_info["Average_price"]

                    self.account_cash = self.get_account_cash_from_local()
                    self.account_cash -= self.cost1
                    self.update_account_cash_to_json()

                    ms1 = f"buy Long {avg_price1} * {TdAccount_middle.keep1} = {self.cost1}"
                    ms2 = f"buy expect price : {price1} , actual price: {avg_price1} , diff: {price1 - avg_price1}, {(price1 - avg_price1) / avg_price1} %"

                    print(ms1)
                    print(ms2)

                    self.log_sys.append(ms1)
                    self.log_sys.append(ms2)

                    self.last_price = price1
                    self.best_price = price1

                else:
                    TdAccount_middle.keep1 = 0
                    print("預估要買 long, 但沒買到 timeout")
                    self.log_sys.append("預估要買 long, 但沒買到 timeout")
                    self.last_hold = 0


            else:
                self.last_hold = 0
                print(f"budget // price1 <> {self.budget} // {price1}")
                self.log_sys.append(f"budget // price1 <> {self.budget} // {price1}")
                raise "wrong budget"  ## 預算不足


        else:  # 本來就持有 不需再買入的情況 , 驗證一下實際線上帳戶與本地情況

            self.verify_local_and_online_symbols_holding(long_or_short="long")

        t2 = time.time()
        self.last_hold += 1
        print(f"buy process time {t2 - t1} s")
        self.log_sys.append(f"buy process time {t2 - t1} s")

    def sell(self, price1):
        t1 = time.time()
        count = 3
        if TdAccount_middle.keep1:
            print("檢查帳戶馬尼")
            self.account_cash = self.get_account_cash_from_local()

            while count > 0:
                count -= 1
                print("sell long...")
                self.client.sell_by_market(self.long_symbol, TdAccount_middle.keep1)
                time.sleep(3)
                print(f"準備驗證sell {count}")
                account_symbol_info = self.update_account_status_after_operating(self.long_symbol, "selling")
                print("驗證結束")
                if account_symbol_info is None:
                    break

                print("finish long again")
                self.log_sys.append("finish long again")

            if account_symbol_info is None:  # 確認已賣掉

                update_account_cash = self.client.get_cash_balance()

                self.income1 = update_account_cash - self.account_cash
                self.account_cash = update_account_cash
                self.update_account_cash_to_json()

                avg_price1 = self.income1 / TdAccount_middle.keep1

                performance = self.income1 - self.cost1
                predict_performance = (TdAccount_middle.keep1 * price1) - self.cost1

                ms1 = f"sell Long  {self.income1}"
                ms2 = f"Long earns {self.income1} - {self.cost1} = {performance}"
                ms3 = f"sell expect price : {price1} , actual price: {avg_price1} , diff: {avg_price1 - price1}, {(avg_price1 - price1) / avg_price1} %"

                if abs(performance) > self.budget * 0.05:
                    performance = predict_performance

                TdAccount_middle.performance_Long.append(performance)
                TdAccount_middle.predict_performance_Long.append(predict_performance)

                self.log_sys.append(ms1)
                self.log_sys.append(ms2)
                self.log_sys.append(ms3)

                print(ms1)
                print(ms2)
                print(ms3)

                # self.budget += performance
                self.income1, self.cost1 = 0, 0
                self.predict_cost1 = 0
                TdAccount_middle.keep1 = 0
                self.last_hold = 0
                self.last_price = None
                self.best_price = None
            else:
                self.log_sys.append(f"賣出long失敗 {datetime.datetime.now()}")
                return

        t2 = time.time()
        print(f"sell process time {t2 - t1} s")
        self.log_sys.append(f"sell process time {t2 - t1} s")

    def buy_n(self, price2,price1=None):
        t1 = time.time()
        account_symbol_info = None
        count = 3
        if (TdAccount_middle.keep2 == 0) and (price2 != 0):

            TdAccount_middle.keep2 = self.budget // price2  ## 現有價格粗略計算要買多少

            if TdAccount_middle.keep2 > 0:

                if self.long_symbol == self.short_symbol:
                    self.client.sell_short_by_market(self.short_symbol, TdAccount_middle.keep2)
                    # 回補賣空, 本來比較貴的時候賣掉, 現在比較低 買回還它
                else:
                    self.client.buy_by_market(self.short_symbol, TdAccount_middle.keep2)  # 反向標的

                while (account_symbol_info is None) and (count > 0):
                    count -= 1
                    time.sleep(3)
                    print(f"準備驗證n buy {count}")
                    account_symbol_info = self.update_account_status_after_operating(self.short_symbol, "buying")
                    print("check buy short status")

                if account_symbol_info:
                    self.cost2 = TdAccount_middle.keep2 * account_symbol_info["Average_price"]
                    self.predict_cost2 = TdAccount_middle.keep2 * price2

                    avg_price2 = account_symbol_info["Average_price"]

                    self.account_cash = self.get_account_cash_from_local()
                    self.account_cash -= self.cost2
                    self.update_account_cash_to_json()

                    ms1 = f"buy Short {avg_price2} * {TdAccount_middle.keep2} = {self.cost2}"
                    ms2 = f"buy expect price : {price2} , actual price: {avg_price2} , diff: {price2 - avg_price2}, {(price2 - avg_price2) / avg_price2} %"

                    print(ms1)
                    print(ms2)

                    self.log_sys.append(ms1)
                    self.log_sys.append(ms2)

                    self.best_price = price1
                    self.last_price = price1


                else:
                    TdAccount_middle.keep2 = 0
                    print("預估要買 short, 但沒買到, timeout")
                    self.log_sys.append("預估要買 short, 但沒買到 timeout")
                    self.last_hold = 0


            else:
                self.last_hold = 0
                print(f"budget // price2 <> {self.budget} // {price2}")
                self.log_sys.append(f"budget // price2 <> {self.budget} // {price2}")
                raise "wrong budget"  ## 預算不足



        else:  # 本來就持有 不需再買入的情況 , 驗證一下實際線上帳戶與本地情況

            self.verify_local_and_online_symbols_holding(long_or_short="short")

        t2 = time.time()
        self.last_hold -= 1
        print(f"buy_n process time {t2 - t1} s")
        self.log_sys.append(f"buy_n process time {t2 - t1} s")

    def sell_n(self, price2):

        t1 = time.time()
        count = 3
        if TdAccount_middle.keep2:
            print("檢查帳戶馬尼")
            self.account_cash = self.get_account_cash_from_local()

            while count > 0:

                count -= 1

                if self.long_symbol == self.short_symbol:
                    self.client.buy_to_cover_by_market(self.short_symbol,
                                                       TdAccount_middle.keep2)  # 放空同標的
                else:
                    print("sell short...")
                    self.client.sell_by_market(self.short_symbol, TdAccount_middle.keep2)

                time.sleep(3)
                print(f"準備驗證n sell {count}")
                account_symbol_info = self.update_account_status_after_operating(self.short_symbol, "selling")
                print("驗證結束")
                if account_symbol_info is None:
                    break

                print("finish short again")

            if account_symbol_info is None:
                update_account_cash = self.client.get_cash_balance()
                self.income2 = update_account_cash - self.account_cash
                self.account_cash = update_account_cash
                self.update_account_cash_to_json()

                avg_price2 = self.income2 / TdAccount_middle.keep2

                performance = self.income2 - self.cost2
                predict_performance = (TdAccount_middle.keep2 * price2) - self.predict_cost2

                ms1 = f"sell Short  {self.income2}"
                ms2 = f"Short earns {self.income2} - {self.cost2} = {performance}"
                ms3 = f"sell expect price : {price2} , actual price: {avg_price2} , diff: {avg_price2 - price2}, {(avg_price2 - price2) / avg_price2} %"

                if abs(performance) > self.budget * 0.05:
                    performance = predict_performance

                TdAccount_middle.performance_Short.append(performance)
                if self.short_symbol == self.long_symbol:
                    predict_performance = -predict_performance
                    TdAccount_middle.predict_performance_Short.append(-predict_performance)
                else:
                    TdAccount_middle.predict_performance_Short.append(predict_performance)

                self.log_sys.append(ms1)
                self.log_sys.append(ms2)
                self.log_sys.append(ms3)

                print(ms1)
                print(ms2)
                print(ms3)

                # self.budget += performance
                self.income2, self.cost2 = 0, 0
                self.predict_cost2 = 0
                TdAccount_middle.keep2 = 0
                self.last_hold = 0
                self.last_price = None
                self.best_price = None

            else:
                self.log_sys.append(f"賣出short失敗 {datetime.datetime.now()}")
                return

        t2 = time.time()
        print(f"sell_n process time {t2 - t1} s")
        self.log_sys.append(f"sell_n process time {t2 - t1} s")

    def announce(self):
        if TdAccount_middle.keep1:
            print(f"hold Long {TdAccount_middle.keep1} shares")
            self.log_sys.append(f"hold Long {TdAccount_middle.keep1} shares")
        elif TdAccount_middle.keep2:
            print(f"hold Short {TdAccount_middle.keep2} shares")
            self.log_sys.append(f"hold Short {TdAccount_middle.keep2} shares")
        else:
            print(f"No hold")
            self.log_sys.append(f"No hold")

        temp_log = self.log_sys

        self.log_sys = []

        return temp_log


def get_tda_client(token_path: str, api_key: str, redirect_uri: str) -> tda.client:
    try:
        tda_client = auth.client_from_token_file(token_path, api_key)

    except FileNotFoundError:

        from selenium import webdriver

        with webdriver.Chrome() as driver:
            tda_client = auth.client_from_login_flow(
                driver, api_key, redirect_uri, token_path)

    return tda_client


if __name__ == "__main__":
    import yaml
    with open(os.path.join(work_dir,"config","tradingBot","botConfig.yaml"),"r") as f1:
        data = yaml.safe_load(f1)["bot"]
        account_id = data["account_id"]
        api_key = data["api_key"]

    token_path = os.path.join(work_dir,"token.json")
    redirect_uri = "https://localhost:8080"
    print(api_key)
    print(account_id)

    tda_client = get_tda_client(
        token_path=token_path,
        api_key=api_key,
        redirect_uri=redirect_uri
    )

    client = ClientExtend(client=tda_client, account_id=account_id)
    print("show balance")
    print(client.get_cash_balance())
    print("test successful")

