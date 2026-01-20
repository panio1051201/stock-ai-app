import pandas as pd
from FinMind.data import DataLoader
import datetime

# 設定 Token
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNi0wMS0xMyAxNzoxMzoxNSIsInVzZXJfaWQiOiJQYW5pbzEwNSIsImVtYWlsIjoicGFuZGFwdGNAZ21haWwuY29tIiwiaXAiOiIxMTguMTY1LjgxLjE1MCJ9.oIqSGQ19FahqRVx_b6IPaibwXEhIsLX5_rirgMEQUjA"

def analyze(df_ignored, stock_code_ignored=None):
    """
    策略：妖股獵手 v2 (Demon Stock Hunter)
    條件 A: 近一個月週 K 線連五紅 (每週收盤 > 開盤)
    條件 B: 日 K 線連續 3 天漲停 (漲幅 > 9.5%)
    """
    try:
        print("[Demon Hunter] 啟動妖股掃描 v2...")
        dl = DataLoader()
        dl.login_by_token(api_token=API_TOKEN)
        
        # 1. 取得股票清單
        stocks = dl.taiwan_stock_info()
        stock_list = stocks['stock_id'].tolist()
        
        # ★ 網頁版安全機制：只掃描前 50 檔以免瀏覽器 Timeout
        # 如果您想在黑色視窗跑全市場，請把這行註解掉
        scan_limit = 50 
        target_list = stock_list[:scan_limit]
        
        print(f"[System] 為了防止網頁斷線，本次僅掃描前 {len(target_list)} 檔示範。")
        print("[System] 若要掃描全市場，請使用獨立腳本執行。")

        # 設定資料範圍 (抓 3 個月，確保週線資料足夠)
        start_date = (datetime.datetime.now() - datetime.timedelta(days=100)).strftime('%Y-%m-%d')
        
        found_stocks = []
        
        for stock_id in target_list:
            try:
                # 抓取日線資料
                df = dl.taiwan_stock_daily(stock_id=stock_id, start_date=start_date)
                if df.empty or len(df) < 10: continue

                # 整理數據
                df['close'] = pd.to_numeric(df['close'], errors='coerce')
                df['open'] = pd.to_numeric(df['open'], errors='coerce')
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)

                # --- 條件 1: 日 K 連續 3 根漲停 ---
                # 計算漲跌幅
                df['pct_change'] = df['close'].pct_change()
                # 取最後 3 天
                last_3_days = df.tail(3)
                # 漲停定義：漲幅 > 9.4% (寬容值，避免 9.9% 沒算到)
                is_3_limit_up = all(last_3_days['pct_change'] > 0.094)

                # --- 條件 2: 週 K 連 5 紅 ---
                # 轉換為週線 (W-FRI 代表每週五結算)
                df_weekly = df.resample('W-FRI').agg({
                    'open': 'first',
                    'close': 'last',
                    'max': 'max',
                    'min': 'min'
                })
                # 判斷是否收紅 (收盤 > 開盤)
                df_weekly['is_red'] = df_weekly['close'] > df_weekly['open']
                # 取最後 5 週
                last_5_weeks = df_weekly.tail(5)
                # 檢查資料是否足夠 5 週，且全部收紅
                is_5_week_red = (len(last_5_weeks) >= 5) and all(last_5_weeks['is_red'])

                # --- 綜合判斷 ---
                match_reason = ""
                if is_3_limit_up:
                    match_reason += "🔥 日K連三漲停 "
                if is_5_week_red:
                    match_reason += "📈 週K連五紅 "

                if match_reason:
                    stock_name = stocks[stocks['stock_id'] == stock_id]['stock_name'].values[0]
                    found_stocks.append(f"{stock_name}({stock_id}): {match_reason}")
                    print(f"   >>> 找到妖股: {stock_name} ({match_reason})")

            except Exception:
                continue

        # 回傳結果
        if not found_stocks:
            desc = f"在掃描的 {len(target_list)} 檔股票中，未發現符合條件者。"
        else:
            desc = " | ".join(found_stocks)

        return {
            'title': '妖股獵手 v2 結果',
            'signal': f'發現 {len(found_stocks)} 檔',
            'desc': desc,
            'vals': {
                '掃描範圍': f'前 {len(target_list)} 檔 (網頁限制)',
                '條件A': '日K連3漲停',
                '條件B': '週K連5紅',
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