import pandas as pd

def analyze(df):
    """
    策略核心：葛蘭碧八大法則 (Granville) + 林恩如均線戰法 (20MA Lifecycle)
    """
    try:
        # 1. 準備數據
        close = df['Close']
        if len(close) < 65: return None

        # 計算均線
        ma5 = close.rolling(5).mean()    # 短線攻擊
        ma10 = close.rolling(10).mean()  # 短線防守
        ma20 = close.rolling(20).mean()  # 林恩如生命線 (關鍵)
        ma60 = close.rolling(60).mean()  # 季線 (長線趨勢)

        # 取得 當前 與 前一日 數值 (用於判斷斜率與交叉)
        c_price = close.iloc[-1]
        p_price = close.iloc[-2]
        
        c_ma5, p_ma5 = ma5.iloc[-1], ma5.iloc[-2]
        c_ma10, p_ma10 = ma10.iloc[-1], ma10.iloc[-2]
        c_ma20, p_ma20 = ma20.iloc[-1], ma20.iloc[-2]
        c_ma60, p_ma60 = ma60.iloc[-1], ma60.iloc[-2]

        # 計算 20MA 斜率 (林恩如核心：均線必須翻揚)
        ma20_slope = c_ma20 - p_ma20
        ma60_slope = c_ma60 - p_ma60

        # ========================================================
        # A. 波段分析 (林恩如 20MA 生命線戰法)
        # 邏輯：站上 20MA + 20MA 上彎 = 多頭； 跌破 = 停損/空頭
        # ========================================================
        swing_sig = "觀望"
        swing_desc = "股價於生命線附近整理"
        
        # 判斷多頭
        if c_price > c_ma20:
            if ma20_slope > 0:
                swing_sig = "波段持有 (多)"
                swing_desc = "站上20週均線且翻揚 (林恩如多頭)"
                
                # 葛蘭碧買點 2: 回測不破 (價格跌到 MA 附近又彈起來)
                if df['Low'].iloc[-1] <= c_ma20 * 1.01 and c_price > c_ma20:
                    swing_sig = "加碼買進"
                    swing_desc = "葛蘭碧：回測生命線有撐"
                
                # 葛蘭碧買點 1: 剛突破
                if p_price < p_ma20:
                    swing_sig = "波段起漲"
                    swing_desc = "葛蘭碧：帶量突破生命線"

            else:
                swing_sig = "觀望 (盤整)"
                swing_desc = "雖站上20MA但均線走平，動能不足"
        
        # 判斷空頭
        elif c_price < c_ma20:
            if ma20_slope < 0:
                swing_sig = "波段賣出 (空)"
                swing_desc = "跌破20週均線且下彎 (林恩如停損)"
            else:
                swing_sig = "警戒 (轉弱)"
                swing_desc = "跌破生命線，等待確認"

        # ========================================================
        # B. 短線分析 (葛蘭碧 5MA/10MA 乖離與交叉)
        # ========================================================
        short_sig = "觀望"
        short_desc = "短線無明顯訊號"

        # 多頭排列
        if c_ma5 > c_ma10 and c_price > c_ma5:
            short_sig = "強勢買進"
            short_desc = "沿5日線攻擊 (強勢股)"
            
            # 葛蘭碧賣點 4: 乖離過大 (正乖離)
            bias = (c_price - c_ma20) / c_ma20 * 100
            if bias > 20: # 乖離率 > 20%
                short_sig = "獲利了結"
                short_desc = "葛蘭碧：正乖離過大，隨時拉回"

        # 黃金交叉 (5 穿過 10)
        elif c_ma5 > c_ma10 and p_ma5 <= p_ma10:
            short_sig = "短線買進"
            short_desc = "5日線金叉10日線"

        # 空頭排列 / 死亡交叉
        elif c_ma5 < c_ma10:
            if c_price < c_ma5:
                short_sig = "短線賣出"
                short_desc = "被5日線壓著打"
            
            # 葛蘭碧買點 4: 乖離過大 (負乖離) - 搶反彈
            bias = (c_price - c_ma20) / c_ma20 * 100
            if bias < -20:
                short_sig = "搶反彈 (險)"
                short_desc = "葛蘭碧：負乖離過大，可能反彈"

        # ========================================================
        # C. 綜合總結
        # ========================================================
        final_sig = swing_sig # 以波段為主
        
        # 如果短線有強烈訊號，覆蓋波段訊號 (例如過熱要賣)
        if "獲利" in short_sig or "搶反彈" in short_sig:
            final_sig = short_sig
        
        # 描述整合
        final_desc = f"{swing_desc}。{short_desc}"

        return {
            'title': 'MA 戰法 (葛蘭碧 + 林恩如)',
            'signal': final_sig,
            'desc': final_desc,
            'vals': {
                '現價': round(c_price, 2),
                '5MA (短)': round(c_ma5, 2),
                '生命線 (20MA)': round(c_ma20, 2),
                '趨勢 (60MA)': round(c_ma60, 2),
                '波段狀態': swing_sig,
                '短線狀態': short_sig
            }
        }

    except Exception as e:
        print(f"[MA Error] {e}")
        return {
            'title': 'MA 分析錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {'MA': 0}
        }