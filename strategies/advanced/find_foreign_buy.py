import pandas as pd
from FinMind.data import DataLoader
import datetime

# 設定 Token
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNi0wMS0xMyAxNzoxMzoxNSIsInVzZXJfaWQiOiJQYW5pbzEwNSIsImVtYWlsIjoicGFuZGFwdGNAZ21haWwuY29tIiwiaXAiOiIxMTguMTY1LjgxLjE1MCJ9.oIqSGQ19FahqRVx_b6IPaibwXEhIsLX5_rirgMEQUjA"

def analyze(df_ignored, stock_code_ignored=None):
    """
    策略：外資連買且站上月線
    條件 A: 最新收盤價大於 20MA (月線)
    條件 B: 外資 (Foreign_Investor) 連續三個交易日買超大於 0
    """
    try:
        print("[ForeignBuy Hunter] 啟動外資籌碼掃描...")
        dl = DataLoader()
        dl.login_by_token(api_token=API_TOKEN)
        
        # 1. 取得股票清單
        stocks = dl.taiwan_stock_info()
        stock_list = stocks['stock_id'].tolist()
        
        # ★ 網頁版安全機制：只掃描前 50 檔以免瀏覽器 Timeout
        scan_limit = 50 
        target_list = stock_list[:scan_limit]
        
        print(f"[System] 本次僅掃描前 {len(target_list)} 檔示範。")

        # 設定資料範圍 (抓 2 個月，確保 20MA 與連買天數足夠)
        start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
        
        found_stocks = []
        
        for stock_id in target_list:
            try:
                # 抓取日線資料 (計算 MA)
                df_daily = dl.taiwan_stock_daily(stock_id=stock_id, start_date=start_date)
                if df_daily.empty or len(df_daily) < 20: continue
                
                df_daily['close'] = pd.to_numeric(df_daily['close'], errors='coerce')
                df_daily['date'] = pd.to_datetime(df_daily['date'])
                df_daily.set_index('date', inplace=True)
                df_daily.sort_index(inplace=True)
                
                # 計算 20MA
                df_daily['ma20'] = df_daily['close'].rolling(window=20).mean()
                latest_close = df_daily['close'].iloc[-1]
                latest_ma20 = df_daily['ma20'].iloc[-1]
                
                if pd.isna(latest_ma20) or latest_close <= latest_ma20:
                    continue # 未站上月線，跳過
                    
                # 抓取三大法人資料 (計算外資連買)
                df_inst = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
                if df_inst.empty: continue
                
                # 過濾出外資買賣超
                df_foreign = df_inst[df_inst['name'] == 'Foreign_Investor'].copy()
                if len(df_foreign) < 3: continue
                
                df_foreign['date'] = pd.to_datetime(df_foreign['date'])
                df_foreign.set_index('date', inplace=True)
                df_foreign.sort_index(inplace=True)
                
                # 取最後 3 天外資交易紀錄
                last_3_foreign = df_foreign.tail(3)
                is_3_days_buy = all(last_3_foreign['buy'] - last_3_foreign['sell'] > 0)
                
                if is_3_days_buy:
                    stock_name = stocks[stocks['stock_id'] == stock_id]['stock_name'].values[0]
                    found_stocks.append(f"{stock_name}({stock_id})")
                    print(f"   >>> 符合條件: {stock_name} (站上20MA且外資連買3天)")

            except Exception:
                continue

        # 回傳結果
        if not found_stocks:
            desc = f"在掃描的 {len(target_list)} 檔股票中，未發現符合條件者。"
        else:
            desc = " | ".join(found_stocks)

        return {
            'title': '外資連買月線上 結果',
            'signal': f'發現 {len(found_stocks)} 檔',
            'desc': desc,
            'vals': {
                '掃描範圍': f'前 {len(target_list)} 檔 (網頁限制)',
                '條件A': '收盤價 > 20MA',
                '條件B': '外資連續3天買超',
                '名單': found_stocks if found_stocks else "無"
            }
        }

    except Exception as e:
        return {
            'title': '掃描錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {}
        }
