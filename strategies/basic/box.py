import pandas as pd

def analyze(df):
    """
    策略核心：尼可拉斯·達華斯 (Darvas Box) + 台灣廖崧漪 (箱波均 N字戰法)
    
    兩位大師的結合：
    1. 達華斯 (主攻)：看「突破」，股價衝出箱頂，代表新趨勢開始 -> 追價買進。
    2. 廖崧漪 (防守/佈局)：看「支撐」，股價回測箱底不破，且出現止跌訊號 -> 低接買進。
    """
    try:
        # 設定箱型週期 (通常為 20~60 天，這裡取 20 天約一個月)
        period = 20
        if len(df) < period + 5: return None

        close = df['Close']
        high = df['High']
        low = df['Low']
        vol = df['Volume']
        
        # 取得當前數據
        c_price = close.iloc[-1]
        c_vol = vol.iloc[-1]
        avg_vol = vol.tail(5).mean() # 5日均量
        
        # 1. 定義箱型 (Box Definition)
        # 達華斯定義：過去一段時間的最高點為箱頂，最低點為箱底
        # 我們取過去 20 天 (不含今天) 的極值
        past_highs = high.iloc[-period-1:-1]
        past_lows = low.iloc[-period-1:-1]
        
        box_top = past_highs.max()    # 壓力區 (箱頂)
        box_bottom = past_lows.min()  # 支撐區 (箱底)
        
        # 計算目前價格在箱子裡的位置 (0% = 箱底, 100% = 箱頂)
        # 這是廖崧漪老師強調的「位階」概念
        box_height = box_top - box_bottom
        if box_height == 0: position = 50
        else: position = (c_price - box_bottom) / box_height * 100

        # ------------------------------------------------
        # 訊號判斷邏輯
        # ------------------------------------------------
        sig = "觀望"
        desc = f"股價於箱型內整理 (位階: {int(position)}%)"
        
        # === 情況 A: 達華斯突破 (動能派) ===
        # 邏輯：收盤價站上箱頂，且出量
        if c_price > box_top:
            sig = "買進 (達華斯突破)"
            desc = "股價創新高，突破箱頂壓力"
            
            # 濾網：成交量確認
            if c_vol > avg_vol * 1.3:
                sig = "強力買進 (突破)"
                desc += "，且爆量表態 (真突破機率高)"
        
        # === 情況 B: 廖崧漪回測支撐 (佈局派) ===
        # 邏輯：股價跌到箱底附近 (0% ~ 20% 位置)，但沒有跌破，且收紅 K (止跌)
        elif position < 20 and c_price > box_bottom:
            # 檢查是否收紅 K (收盤 > 開盤) 或是 下影線
            is_red_k = close.iloc[-1] > df['Open'].iloc[-1]
            
            if is_red_k:
                sig = "買進 (箱底佈局)"
                desc = "廖崧漪：回測箱底有撐，出現止跌訊號"
            else:
                desc = "接近箱底，觀察是否止跌"

        # === 情況 C: 跌破箱底 (停損) ===
        elif c_price < box_bottom:
            sig = "賣出 (破底)"
            desc = "達華斯：跌破箱底，支撐瓦解，趨勢轉空"

        # === 情況 D: 箱頂不過 (壓力) ===
        elif position > 80 and c_price < box_top:
            # 如果在箱頂附近收黑 K，可能是假突破或壓力過大
            is_black_k = close.iloc[-1] < df['Open'].iloc[-1]
            if is_black_k:
                sig = "賣出 (箱頂遇壓)"
                desc = "廖崧漪：來到箱頂無法突破，短線獲利了結"

        # ------------------------------------------------
        # 回傳結果
        # ------------------------------------------------
        return {
            'title': '箱型理論 (達華斯 x 廖崧漪)',
            'signal': sig,
            'desc': desc,
            'vals': {
                '現價': round(c_price, 2),
                '箱頂 (壓力)': round(box_top, 2),
                '箱底 (支撐)': round(box_bottom, 2),
                '箱內位階': f"{int(position)}%"
            }
        }

    except Exception as e:
        print(f"[Box Error] {e}")
        return {
            'title': '箱型分析錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {'箱頂': 0, '箱底': 0}
        }