import pandas as pd
from FinMind.data import DataLoader
import datetime
import time

# Token
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNi0wMS0xMyAxNzoxMzoxNSIsInVzZXJfaWQiOiJQYW5pbzEwNSIsImVtYWlsIjoicGFuZGFwdGNAZ21haWwuY29tIiwiaXAiOiIxMTguMTY1LjgxLjE1MCJ9.oIqSGQ19FahqRVx_b6IPaibwXEhIsLX5_rirgMEQUjA"

def main():
    print("=========================================")
    print("🚀 妖股獵手 v2 - 全市場掃描工具")
    print("條件：週K連五紅 OR 日K連三漲停")
    print("=========================================")
    
    dl = DataLoader()
    dl.login_by_token(api_token=API_TOKEN)
    
    # 1. 取得全清單
    print("正在下載股票清單...")
    stocks = dl.taiwan_stock_info()
    # 過濾掉太長的代碼 (權證等)，只留個股
    target_stocks = stocks[stocks['stock_id'].astype(str).str.len() == 4]
    stock_list = target_stocks['stock_id'].tolist()
    
    total = len(stock_list)
    print(f"共 {total} 檔股票，開始掃描 (預計耗時 3-5 分鐘)...")
    
    start_date = (datetime.datetime.now() - datetime.timedelta(days=100)).strftime('%Y-%m-%d')
    
    hits = []
    
    for i, stock_id in enumerate(stock_list):
        # 顯示進度
        if i % 50 == 0:
            print(f"進度: {i}/{total} ({i/total*100:.1f}%) ...")
            
        try:
            df = dl.taiwan_stock_daily(stock_id=stock_id, start_date=start_date)
            if df.empty or len(df) < 10: continue

            # 轉數值
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

            # 條件 1: 日 K 連 3 漲停
            df['pct'] = df['close'].pct_change()
            is_3_up = all(df['pct'].tail(3) > 0.094)

            # 條件 2: 週 K 連 5 紅
            df_w = df.resample('W-FRI').agg({'open':'first', 'close':'last'})
            df_w['is_red'] = df_w['close'] > df_w['open']
            is_5_red = (len(df_w) >= 5) and all(df_w['is_red'].tail(5))

            if is_3_up or is_5_red:
                name = target_stocks[target_stocks['stock_id'] == stock_id]['stock_name'].values[0]
                reason = []
                if is_3_up: reason.append("🔥日K連三漲停")
                if is_5_red: reason.append("📈週K連五紅")
                
                msg = f"[{stock_id} {name}] {' '.join(reason)}"
                print(f"\n🎯 抓到了! {msg}\n")
                hits.append(msg)

        except Exception:
            continue

    print("\n=========================================")
    print("掃描完成！結果如下：")
    for h in hits:
        print(h)
    print("=========================================")

if __name__ == '__main__':
    main()