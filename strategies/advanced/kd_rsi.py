import pandas as pd
# 引用基礎策略，確保數據源一致
from strategies.basic import kd, rsi

def analyze(df):
    """
    策略核心：KD + RSI 多因子計分模型
    
    邏輯：
    同時監控 [日K, 週K, 日RSI, 週RSI] 共 4 個指標。
    
    買進計分 (< 30):
    1分: 試單 | 2分: 小試身手 | 3分: 進場 | 4分: 抄底
    
    賣出計分 (> 80):
    1分: 先賣一張 | 2分: 少量出單 | 3分: 減碼 | 4分: 出清
    """
    try:
        # 1. 取得基礎指標數據 (日/週)
        res_kd = kd.analyze(df)
        res_rsi = rsi.analyze(df)
        
        # 提取數值 (若計算失敗給予中性值 50)
        try:
            day_k = res_kd['vals'].get('日 K', 50)
            week_k = res_kd['vals'].get('週 K', 50)
            day_rsi = res_rsi['vals'].get('日 RSI', 50)
            week_rsi = res_rsi['vals'].get('週 RSI', 50)
        except:
            return None

        # 2. 計算分數
        buy_score = 0
        sell_score = 0
        
        # 檢查 4 個因子
        factors = [day_k, week_k, day_rsi, week_rsi]
        
        for val in factors:
            if val < 30: buy_score += 1
            if val > 80: sell_score += 1

        # 3. 判定訊號與行動
        sig = "觀望"
        desc = f"買方 {buy_score} 分 / 賣方 {sell_score} 分"
        
        # --- 買進邏輯 ---
        if buy_score > 0 and buy_score >= sell_score:
            if buy_score == 1:
                sig = "試單 (1/4)"
                desc = "滿足 1 個低檔條件，輕倉嘗試"
            elif buy_score == 2:
                sig = "小試身手 (2/4)"
                desc = "半數指標共振，可建立基本部位"
            elif buy_score == 3:
                sig = "進場 (3/4)"
                desc = "多數指標超賣，勝率顯著提高"
            elif buy_score == 4:
                sig = "抄底 (4/4)"
                desc = "日週全數落底，強烈買進訊號"

        # --- 賣出邏輯 ---
        elif sell_score > 0 and sell_score > buy_score:
            if sell_score == 1:
                sig = "先賣一張 (1/4)"
                desc = "滿足 1 個過熱條件，獲利了結一小部分"
            elif sell_score == 2:
                sig = "少量出單 (2/4)"
                desc = "半數指標過熱，注意風險"
            elif sell_score == 3:
                sig = "減碼 (3/4)"
                desc = "多數指標過熱，建議大幅減碼"
            elif sell_score == 4:
                sig = "出清 (4/4)"
                desc = "日週全數過熱，趨勢反轉風險極大"

        # 4. 回傳結果
        return {
            'title': 'KD + RSI 混合策略',
            'signal': sig,
            'desc': desc,
            'vals': {
                '日 K': day_k,
                '週 K': week_k,
                '日 RSI': day_rsi,
                '週 RSI': week_rsi,
                '買進得分': f"{buy_score} / 4",
                '賣出得分': f"{sell_score} / 4"
            }
        }

    except Exception as e:
        print(f"[KD+RSI Error] {e}")
        return {
            'title': '複合策略錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {}
        }