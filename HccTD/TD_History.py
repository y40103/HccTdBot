import datetime

from tda import auth, client
import json
from typing import Dict, List, Union
import tda
import pytz
import numpy as np
import finnhub


class HccTime():

    @staticmethod
    def convert_us_tzone_from_local(min_TD_history_Dict: Dict):
        data = min_TD_history_Dict["candles"]
        us = pytz.timezone('US/Eastern')

        res = dict()
        res["symbol"] = min_TD_history_Dict["symbol"]
        previous_zone = None

        each_min_data = dict()
        for index in range(len(data)):
            us_zone = datetime.datetime.fromtimestamp(data[index]["datetime"] / 1000).astimezone(us)
            each_min_data[us_zone.strftime("%H%M")] = np.array(
                [data[index]["open"], data[index]["volume"]])  ## array([ price , volume])

            if previous_zone == None:  # 一天
                previous_zone = us_zone
            if previous_zone.day != us_zone.day:  # 兩天以上
                res[previous_zone.strftime("%Y%m%d")] = each_min_data
                each_min_data = dict()
                each_min_data[us_zone.strftime("%H%M")] = np.array(
                    [data[index]["open"], data[index]["volume"]])  # 更換後 補上初項
                # elif previous_zone == None: ## 只有一天
            #     res[us_zone.strftime("%Y%m%d")] = each_min_data

            previous_zone = us_zone

        res[us_zone.strftime("%Y%m%d")] = each_min_data

        return res

    def __init__(self, tda_client: tda.client.Client):
        self.tda_client = tda_client

    def get_min_unit_TD_history(self, symbol: str, start_time: str, end_time: str, extend: bool = False) -> Dict[
        str, Union[List[Dict[str, str]], str]]:
        """
        :param symbol: stock symbol
        :param start_time: format-> YYYYmmdd , e.g.  "20220214"
        :param end_time: format-> YYYYmmdd , e.g.  "20220214"

        """

        if extend == False:
            start = "09:30"
            end = "16:00"
        elif extend == True:
            start = "04:00"
            end = "20:00"

        start = datetime.datetime.strptime(f"{start_time} {start} 3.000012", "%Y%m%d %H:%M %S.%f")
        end = datetime.datetime.strptime(f"{end_time} {end} 3.000012", "%Y%m%d %H:%M %S.%f")

        res = self.tda_client.get_price_history(symbol,
                                                period_type=client.Client.PriceHistory.PeriodType.DAY,
                                                period=client.Client.PriceHistory.Period.ONE_DAY,
                                                frequency_type=client.Client.PriceHistory.FrequencyType.MINUTE,
                                                frequency=client.Client.PriceHistory.Frequency.EVERY_MINUTE,
                                                start_datetime=start,
                                                end_datetime=end,
                                                need_extended_hours_data=extend)

        json_format = json.dumps(res.json(), indent=4)

        return json.loads(json_format)


class HccFinnhub():

    def __init__(self, api_key):
        self.client = finnhub.Client(api_key=api_key)

    def get_min_history(self, symbol: str, start: str, end: str):
        start = datetime.datetime.strptime(start, "%Y%m%d")
        end = datetime.datetime.strptime(end, "%Y%m%d")
        us = pytz.timezone('US/Eastern')
        if start != end:
            start = datetime.datetime(year=start.year, month=start.month, day=start.day, hour=0, minute=0,
                                                    second=0, microsecond=0, tzinfo=us)
            end = datetime.datetime(year=end.year, month=end.month, day=end.day, hour=0, minute=0, second=0,
                                                  microsecond=0, tzinfo=us)

        else:
            start = datetime.datetime(year=start.year, month=start.month, day=start.day, hour=9, minute=0,
                                                    second=0, microsecond=0, tzinfo=us)
            end = datetime.datetime(year=end.year, month=end.month, day=end.day, hour=16, minute=0, second=0,
                                                  microsecond=0, tzinfo=us)

        start = us.normalize(start).replace(hour = 9, minute = 0) + datetime.timedelta(days=1)
        end = us.normalize(end).replace(hour = 16, minute = 0)


        start_date = start
        end_date = end

        start = int(start.timestamp())
        end = int(end.timestamp())
        info = self.client.stock_candles(symbol, 1, start, end)  #
        open_value_set = info["o"]
        time_set = info["t"]
        volume_set = info["v"]
        data_set = []
        res = {}
        for each_index in range(len(info["t"])):

            each_time = datetime.datetime.fromtimestamp(time_set[each_index], tz=us)
            start = each_time.replace(hour=9, minute=30)
            end = each_time.replace(hour=16, minute=0)
            if each_time >= start and each_time <= end:
                res[datetime.datetime.fromtimestamp(time_set[each_index],tz=us)] = {"symbol": symbol,
                                                                              "open": open_value_set[each_index],
                                                                              "volume": volume_set[each_index]}

            if each_time == end:
                data_set.append(res)
                res = {}

        temp_data_set = data_set
        date_None = []

        for each_index in range(len(data_set)):
            each_set = data_set[each_index]

            for each_time in range(391):

                if each_set.get(start_date) is None:
                    temp_data_set[each_index][start_date] = each_set.get(start_date - datetime.timedelta(minutes=1))
                    date_None.append(start_date)

                start_date += datetime.timedelta(minutes=1)


            start_date - datetime.timedelta(hours=8)
            start_date += datetime.timedelta(days=1)

        return temp_data_set


if __name__ == "__main__":
    pass