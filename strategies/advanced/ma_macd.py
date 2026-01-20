import pandas as pd
# 引用基礎策略
from strategies.basic import ma, macd

def analyze(df):
    """
    策略核心：MA (趨勢) + MACD (動能) 混合計分
    
    條件池 (共 4 分)：
    1. [趨勢] 價格 > 20MA (林恩如生命線)
    2. [短線] 5MA > 10MA (葛蘭碧多頭排列)
    3. [型態] DIF > MACD (朱家泓多頭浪)
    4. [動能] Elder 柱狀體向上 (動能增強)
    
    買進計分 (多頭訊號):
    1分: 試單 (趨勢剛轉強)
    2分: 建倉 (趨勢+動能共振)
    3分: 加碼 (強勢多頭)
    4分: 滿倉 (趨勢/動能/短線全數噴出)
    
    賣出計分 (空頭訊號):
    同理，反向判斷
    """
    try:
        # 1. 取得基礎指標數據
        res_ma = ma.analyze(df)
        res_macd = macd.analyze(df)
        
        # 提取數值 (防呆)
        try:
            # MA 數值
            price = res_ma['vals']['現價']
            ma5 = res_ma['vals']['5MA (短)']
            ma10 = df['Close'].rolling(10).mean().iloc[-1] # 補算 10MA
            ma20 = res_ma['vals']['生命線 (20MA)']
            
            # MACD 數值
            dif = res_macd['vals']['DIF (快線)']
            mac = res_macd['vals']['MACD (慢線)']
            osc = res_macd['vals']['柱狀體 (OSC)']
            # 判斷 Elder 動能 (需要前一天的 OSC)
            # 因為 macd.py 回傳的是文字，這裡我們簡單重算一下斜率
            # 或是直接解析文字 '增強 ↗'
            elder_status = res_macd['vals']['Elder動能']
            
        except:
            return None

        # 2. 計算分數 (Scoring)
        buy_score = 0
        sell_score = 0
        
        # --- 買方加分條件 ---
        # 1. 林恩如：站上生命線
        if price > ma20: buy_score += 1
        # 2. 葛蘭碧：短線多頭排列
        if ma5 > ma10: buy_score += 1
        # 3. 朱家泓：DIF 在 MACD 之上 (金叉狀態)
        if dif > mac: buy_score += 1
        # 4. Elder：動能增強
        if "增強" in elder_status: buy_score += 1
        
        # --- 賣方加分條件 ---
        # 1. 跌破生命線
        if price < ma20: sell_score += 1
        # 2. 短線空頭排列
        if ma5 < ma10: sell_score += 1
        # 3. 死叉狀態
        if dif < mac: sell_score += 1
        # 4. 動能衰退
        if "衰退" in elder_status: sell_score += 1

        # 3. 判定訊號與行動
        sig = "觀望"
        desc = f"多方 {buy_score} 分 / 空方 {sell_score} 分"
        
        # --- 買進邏輯 ---
        if buy_score > 0 and buy_score >= sell_score:
            if buy_score == 1:
                sig = "試單 (1/4)"
                desc = "趨勢或動能轉強，嘗試佈局"
            elif buy_score == 2:
                sig = "小試身手 (2/4)"
                desc = "MA與MACD半數共振，趨勢成形"
            elif buy_score == 3:
                sig = "進場 (3/4)"
                desc = "生命線之上且動能強勁，勝率高"
            elif buy_score == 4:
                sig = "強力買進 (4/4)"
                desc = "林恩如與Elder全數翻多，主升段行情"

        # --- 賣出邏輯 ---
        elif sell_score > 0 and sell_score > buy_score:
            if sell_score == 1:
                sig = "先賣一張 (1/4)"
                desc = "部分動能轉弱，獲利了結"
            elif sell_score == 2:
                sig = "少量出單 (2/4)"
                desc = "趨勢與動能分歧，降低持股"
            elif sell_score == 3:
                sig = "減碼 (3/4)"
                desc = "跌破生命線或動能大減，危險"
            elif sell_score == 4:
                sig = "出清 (4/4)"
                desc = "空頭排列且動能向下的崩盤格局"

        # 4. 回傳結果
        return {
            'title': 'MA + MACD 趨勢動能策略',
            'signal': sig,
            'desc': desc,
            'vals': {
                '現價': price,
                '生命線': ma20,
                'MACD柱': osc,
                'Elder動能': elder_status,
                '多方得分': f"{buy_score} / 4",
                '空方得分': f"{sell_score} / 4"
            }
        }

    except Exception as e:
        print(f"[MA+MACD Error] {e}")
        return {
            'title': '複合策略錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {}
        }