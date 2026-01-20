import pandas as pd
from FinMind.data import DataLoader
import datetime
import re

# --- 設定 FinMind API Token ---
# 建議去 FinMind 官網申請免費 Token 填入，會穩定很多
API_TOKEN = "" 

# 全域變數
STOCK_MAP_NAME_TO_ID = {}
STOCK_MAP_ID_TO_NAME = {}

def init_stock_list():
    global STOCK_MAP_NAME_TO_ID, STOCK_MAP_ID_TO_NAME
    print("[System] 正在更新台股清單...")
    try:
        dl = DataLoader()
        if API_TOKEN: dl.login_by_token(api_token=API_TOKEN)
        
        df = dl.taiwan_stock_info()
        
        if not df.empty:
            df['stock_name'] = df['stock_name'].astype(str).str.strip()
            df['stock_id'] = df['stock_id'].astype(str).str.strip()
            STOCK_MAP_NAME_TO_ID = dict(zip(df['stock_name'], df['stock_id']))
            STOCK_MAP_ID_TO_NAME = dict(zip(df['stock_id'], df['stock_name']))
            print(f"[System] 已載入 {len(df)} 檔股票資料。")
        else:
            print("[System] 警告：股票清單下載失敗 (Empty)。")
    except Exception as e:
        if "'data'" in str(e): print("[System Error] Token 失效，切換至訪客模式。")
        else: print(f"[System Error] 股票清單初始化失敗: {e}")

# 初始化執行
init_stock_list()

def get_stock_name(input_str):
    input_str = str(input_str).strip()
    clean_code = input_str.replace('.TW', '').replace('.TWO', '').strip()
    
    if clean_code.isdigit():
        name = STOCK_MAP_ID_TO_NAME.get(clean_code, f"台股 {clean_code}")
        return name, clean_code

    if input_str in STOCK_MAP_NAME_TO_ID:
        return input_str, STOCK_MAP_NAME_TO_ID[input_str]
        
    for name, code in STOCK_MAP_NAME_TO_ID.items():
        if input_str in name: return name, code

    return input_str, input_str

def fetch_data(stock_code, days=730):
    """ 抓取股價 (Price) """
    try:
        clean_code = str(stock_code).replace('.TW', '').strip()
        if not clean_code.isdigit():
             match = re.match(r"(\d+)", clean_code)
             clean_code = match.group(1) if match else clean_code

        dl = DataLoader()
        if API_TOKEN: dl.login_by_token(api_token=API_TOKEN)
        
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        print(f"[FinMind] 下載股價: {clean_code} ...")
        
        df = dl.taiwan_stock_daily(stock_id=clean_code, start_date=start_date)
        
        if df.empty: return pd.DataFrame(), 0
            
        df = df.rename(columns={'date': 'Date', 'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'Trading_Volume': 'Volume'})
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df, df['Close'].iloc[-1]

    except Exception as e:
        print(f"[Fetch Price Error] {e}")
        return pd.DataFrame(), 0

def fetch_financials(stock_code):
    """ 抓取財報 (Financial Statements) & 月營收 """
    try:
        clean_code = str(stock_code).replace('.TW', '').strip()
        dl = DataLoader()
        if API_TOKEN: dl.login_by_token(api_token=API_TOKEN)

        start_date = (datetime.datetime.now() - datetime.timedelta(days=450)).strftime('%Y-%m-%d')
        
        print(f"[FinMind] 下載財報: {clean_code} ...")
        
        df_fin = dl.taiwan_stock_financial_statement(stock_id=clean_code, start_date=start_date)
        df_rev = dl.taiwan_stock_month_revenue(stock_id=clean_code, start_date=start_date)
        
        return df_fin, df_rev

    except Exception as e:
        print(f"[Fetch Financial Error] {e}")
        return pd.DataFrame(), pd.DataFrame()

def fetch_institutional_investors(stock_code, days=90):
    """ 抓取三大法人買賣超數據 (Debug版) """
    try:
        clean_code = str(stock_code).replace('.TW', '').strip()
        dl = DataLoader()
        if API_TOKEN: dl.login_by_token(api_token=API_TOKEN)
        
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        print(f"[FinMind] 下載法人籌碼: {clean_code} ...")
        
        # 抓取個股法人買賣超
        df = dl.taiwan_stock_institutional_investors(
            stock_id=clean_code, 
            start_date=start_date
        )
        
        # ★ Debug 資訊：印出到底抓到了幾筆資料
        if df.empty:
            print(f"[Debug] 警告：API 回傳 {clean_code} 的籌碼資料是空的 (Empty DataFrame)。")
            return pd.DataFrame()
        else:
            print(f"[Debug] 成功抓到 {len(df)} 筆籌碼資料。")

        # ★ 強制轉型：確保 buy/sell 是數字，避免字串相減報錯
        # FinMind 有時會回傳字串型態，或是遇到空值
        df['buy'] = pd.to_numeric(df['buy'], errors='coerce').fillna(0)
        df['sell'] = pd.to_numeric(df['sell'], errors='coerce').fillna(0)
        
        # 計算買賣超
        df['net'] = df['buy'] - df['sell']
        df['date'] = pd.to_datetime(df['date'])
        
        return df

    except Exception as e:
        print(f"[Fetch Chips Error] 抓取籌碼發生錯誤: {e}")
        return pd.DataFrame()