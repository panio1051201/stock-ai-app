import pandas as pd

def calculate_rsi(series, period=6):
    """
    通用 RSI 計算函數
    參數預設為 6 (台股常用短線參數)，也可改為 12 或 14
    """
    try:
        if len(series) < period: return 50
        
        delta = series.diff()
        
        # 分別處理漲跌幅
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        
        # 使用 EMA (指數移動平均) 計算，較為平滑
        ema_up = up.ewm(com=period-1, adjust=False).mean()
        ema_down = down.ewm(com=period-1, adjust=False).mean()
        
        rs = ema_up / ema_down
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi.iloc[-1], 2)
    except:
        return 50.0

def analyze(df):
    """
    RSI 雙重架構分析 (日線 + 週線)
    """
    try:
        # ------------------------------------------------
        # 1. 計算【短線】日線 RSI
        # ------------------------------------------------
        rsi_day = calculate_rsi(df['Close'], period=6)

        # ------------------------------------------------
        # 2. 計算【波段】週線 RSI
        # ------------------------------------------------
        # 將日線 Resample 成週線
        df_weekly = df.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last'
        })
        # 移除空值
        df_weekly.dropna(inplace=True)
        
        rsi_week = calculate_rsi(df_weekly['Close'], period=6)

        # ------------------------------------------------
        # 3. 訊號判斷邏輯 (依照您的指定規則)
        # ------------------------------------------------
        
        # A. 短線狀態 (日)
        st_short = "觀望"
        if rsi_day < 30: st_short = "買進 (短線超賣)"
        elif rsi_day > 80: st_short = "賣出 (短線過熱)"

        # B. 波段狀態 (週)
        st_swing = "觀望"
        if rsi_week < 30: st_swing = "買進 (波段低檔)"
        elif rsi_week > 80: st_swing = "賣出 (波段高檔)"

        # C. 綜合總評 (Signal & Desc)
        final_sig = "觀望"
        desc = f"日({rsi_day}) 週({rsi_week}) 皆在中性區"

        # 邏輯判斷樹
        if rsi_day < 30:
            final_sig = "買進訊號"
            desc = "短線進入超賣區，醞釀反彈"
            if rsi_week < 30:
                final_sig = "強力買進"
                desc = "日週同步超賣，長短線共振買點"
        
        elif rsi_day > 80:
            final_sig = "賣出訊號"
            desc = "短線進入超買區，注意拉回"
            if rsi_week > 80:
                final_sig = "強力賣出"
                desc = "日週同步過熱，長短線共振賣點"
                
        # 補充：背離或反彈邏輯 (週線多頭，日線回檔)
        elif rsi_week < 30 and rsi_day > 30 and rsi_day < 50:
            desc = "波段低檔，短線整理中"

        # ------------------------------------------------
        # 4. 回傳結果
        # ------------------------------------------------
        return {
            'title': 'RSI 強弱指標 (日/週)',
            'signal': final_sig,
            'desc': desc,
            'vals': {
                '短線 (日 RSI)': rsi_day,  # 前端會顯示數值
                '短線訊號': st_short,      # 前端會顯示文字
                '波段 (週 RSI)': rsi_week,
                '波段訊號': st_swing
            }
        }

    except Exception as e:
        print(f"[RSI Error] {e}")
        return {
            'title': 'RSI 計算錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {'日 RSI': 0, '週 RSI': 0}
        }