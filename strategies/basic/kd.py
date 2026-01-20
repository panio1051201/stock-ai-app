import pandas as pd

def calculate_kd(series_close, series_high, series_low):
    """
    通用 KD 核心算法
    """
    try:
        # 參數 (9, 3, 3)
        period = 9
        if len(series_close) < period:
            return 50, 50

        # 1. 計算 RSV
        low_min = series_low.rolling(window=period).min()
        high_max = series_high.rolling(window=period).max()
        
        # 避免分母為 0 (當最高價等於最低價時)
        rsv = (series_close - low_min) / (high_max - low_min) * 100
        rsv = rsv.fillna(50)
        
        # 2. 計算 K, D (平滑移動平均)
        k, d = 50, 50
        k_list, d_list = [], []
        
        for val in rsv:
            k = (2/3) * k + (1/3) * val
            d = (2/3) * d + (1/3) * k
            k_list.append(k)
            d_list.append(d)
            
        return round(k_list[-1], 2), round(d_list[-1], 2)
    except Exception as e:
        print(f"[KD Calc Error] {e}")
        return 50, 50

def analyze(df):
    """
    KD 策略主程式 (日線 + 週線)
    """
    print("--- 開始執行 KD 分析 ---")
    try:
        # 1. 計算【日線】KD
        day_k, day_d = calculate_kd(df['Close'], df['High'], df['Low'])
        print(f"[Debug] 日線 KD: {day_k}, {day_d}")

        # 2. 計算【週線】KD
        # 重取樣：日 -> 週
        df_weekly = df.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
        df_weekly.dropna(inplace=True)
        
        week_k, week_d = calculate_kd(df_weekly['Close'], df_weekly['High'], df_weekly['Low'])
        print(f"[Debug] 週線 KD: {week_k}, {week_d}")

        # 3. 訊號判斷邏輯
        # 規則：< 30 買進, > 80 賣出, 30-80 觀望
        signal = "觀望"
        action = "hold" # 前端變色用
        desc = "指標位於中性區間"

        # 判斷日線
        if day_k < 30:
            signal = "買進訊號"
            action = "buy"
            desc = f"日K ({day_k}) 進入低檔超賣區"
            # 如果週線也低檔，加強語氣
            if week_k < 30:
                signal = "強力買進"
                action = "buy-strong"
                desc += "，且週K同步低檔共振"
            elif week_k > day_k: # 週線還在上面，可能是反彈
                desc += " (搶反彈)"

        elif day_k > 80:
            signal = "賣出訊號"
            action = "sell"
            desc = f"日K ({day_k}) 進入高檔過熱區"
            # 如果週線也高檔
            if week_k > 80:
                signal = "強力賣出"
                action = "sell-strong"
                desc += "，且週K同步過熱"

        # 4. 回傳格式 (對應前端 index.html 的渲染邏輯)
        return {
            'title': 'KD 隨機指標 (日/週)',
            'signal': signal,
            'desc': desc,
            'vals': {
                '日 K': day_k,
                '日 D': day_d,
                '週 K': week_k,
                '週 D': week_d
            }
        }

    except Exception as e:
        print(f"[Critical Error] KD 分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return {
            'title': 'KD 分析錯誤',
            'signal': 'ERROR',
            'desc': '計算過程發生錯誤',
            'vals': {'日 K': 0, '日 D': 0}
        }