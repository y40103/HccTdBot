# HccTdBot
基於TD的交易機器人   
謹慎參考   
不對任何造成的損失進行賠償   


基於 tdameritrade 的日內交易機器人, 主要有自動交易, 收集交易資訊,  利用收集的資訊進行回測   

針對2X - 3X槓桿標的的交易機器人   
藉由websocket串流交易訊息的分鐘級交易機器人   
主要流程為   

收集每分鐘交易價格 > 針對交易資訊進行決策 > 對帳戶進行操作   

關盤前3分鐘會賣出所有標的   



交易決策部份需於 HccTD/utils.py  Quan中的judge_direction方法中修改   
每分鐘會有最新的交易價格傳入 val1,  針對val1 進行處理   
交易輸出為 self.smoker.direction = 1 or -1 or 0

self.smoker.direction|意義
--|--
1| 檢視有無持有short, yes: 賣出short,買入long no: 買入long
-1|檢視有無持有long, yes > 賣出long,買入short no: 買入short
0 | 檢視有無持有, yes > 全部賣出 no: 不操作





Td Token 逾期或不存在 需藉由selenium開啟chrome  進行登錄產生   
需先確認本地需有安裝 chrome   

確認chrome安裝後   
chrome瀏覽器直接輸入 chrome://version   
可查看版本   

[根據版本查找driver](https://chromedriver.chromium.org/)   
放置於/usr/bin/   

需從td 申請 api key  (用於 TD API auth)   
[申請](https://developer.tdameritrade.com/)   



## 佈署環境   

```
git clone git@github.com:y40103/HccTdBot.git
```


python3.10   

```
pip install -r requirements.txt
```


 填入基本資訊   
 
 config/tradingBot   
```yaml
bot:  
  account_id: "63515882X"   # TD帳戶ID
  api_key: "YE67VWSF21AHLXIRWEJ22PGZYREQNGAX"  #TD API KEY
  long_symbol: "TQQQ" # long symbol
  short_symbol: "SQQQ" # short symbol
  budget: 100 #交易金額 (單位: 美金)

```


即時交易資料串是使用   
finnhub   
需先申請帳戶 這邊需要2組 一組用於交易 一組用於收集資料   
[申請](https://finnhub.io/)   


```yaml
email_set:  
  -  
    - 12234@outlook.com  
    - passwd1 
  -  
    - 5678@gmail.com  
    - passwd2 
  
  
symbol_set:  
  - collect  #這組為固定 用於收集資料
  - TQQQ     # long symbol 用於交易
```



## QuickStart


1. 產生TD帳戶操作用 token (需確認自己是否為margin account, 否則日內多次交易會被鎖住)   
第一次使用需要產生帳戶操作用 token   
之後若逾期或是失效 才需再執行   

```bash
python HccTD/TD_AccountOperation.py
```

會於目錄產生 token.json   


2. 獲取finnhub websocket token
會利用finnhub帳戶去取得token
token 有時會失效 建議一周執行一次 , 有設定delay time , 大概需2-3分鐘
```bash
python HccTD/finn_token_process.py
```



3. 啟動tradingbot

有設定實際開始串流時間, 開市前幾分鐘才會開始串流交易訊息, 開市後 才會開始進行交易    

```
python formal.py
```



## 其他功能


- #### 收集串流交易資料

若不需交易 只需收集標的每分鐘資訊   

1. 設定收集標的資訊 (若有開啟自動交易 需注意標的不能重複, 自動交易也會將交易資訊進行保留)   

config/collect/collectConfig.yaml   

```
collect:  
  -  
    long: NRGU  
    short: DRIP  
  -  
    long: GDXU  
    short: GDXD

```


2. 啟動收集   

```
python collect.py
```


輸出目錄為 streaming_history_csv/   
e.g.   
TQQQ&SQQQ   
streaming_history_csv/TQQQ_SQQQ/YYYYmmdd.csv   



- #### 回測

之前bot交易或collect 收集的資料進行回測   

直接修改 backtesting.py 下的變數資訊   

```

if __name__ == "__main__":  
    date_set = ["2022-06-30","2022-07-01"]  # streaming_history_csv/XXX_XXX/
    csv日期
    long_symbol = "TQQQ"  # long symbol
    short_symbol = "SQQQ"  # short symbol
    offline_test_from_own_csv(date_set=date_set,long_symbol=long_symbol,short_symbol=short_symbol)

```

```
python backtesting.py
```


output   
```
budget 10000 per day # 預設每日用於交易金額 10000
Long 167.7682191874792, long times: 5 # 做多標的收入
short -149.62691108876606, short times: 4 # 放空標的收入
win_rate 50.0 % # 日為單位的總勝率  e.g. 回測兩天 一勝一負 = 50%
P/D 0.09070654049356562 % # 平均每日效益
income 18.141308098713125 #  總收入

```







