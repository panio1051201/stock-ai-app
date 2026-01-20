import pandas as pd
from strategies.basic import macd, rsi

def analyze(df):
    """
    策略核心：MACD + RSI 順勢爆發 (兼容版)
    """
    try:
        # 1. 取得數據
        res_macd = macd.analyze(df)
        res_rsi = rsi.analyze(df)
        
        # 防呆
        if not res_macd or not res_rsi:
            return None

        vals_m = res_macd.get('vals', {})
        vals_r = res_rsi.get('vals', {})

        # 2. 智慧提取數值 (兼容不同版本的 Key)
        dif = vals_m.get('DIF (快線)') or vals_m.get('DIF') or 0
        mac = vals_m.get('MACD (慢線)') or vals_m.get('MACD') or 0
        elder_status = vals_m.get('Elder動能', '')
        
        day_rsi = vals_r.get('日 RSI') or vals_r.get('RSI 6') or vals_r.get('RSI6') or 50
        week_rsi = vals_r.get('週 RSI') or vals_r.get('RSI 12') or 50

        # 3. 計算分數
        buy_score = 0
        sell_score = 0
        
        # --- 買方計分 ---
        if dif > mac: buy_score += 1
        if "增強" in elder_status or "向上" in elder_status: buy_score += 1
        if day_rsi > 50: buy_score += 1
        if week_rsi > 50: buy_score += 1
        
        # --- 賣方計分 ---
        if dif < mac: sell_score += 1
        if "衰退" in elder_status or "向下" in elder_status: sell_score += 1
        if day_rsi < 50: sell_score += 1
        if day_rsi > 80: sell_score += 1

        # 4. 訊號判定
        sig = "觀望"
        desc = f"多方 {buy_score} 分 / 空方 {sell_score} 分"
        
        if buy_score > 0 and buy_score >= sell_score:
            if buy_score >= 3: sig = "強力買進"
            elif buy_score == 2: sig = "小試身手"
            else: sig = "試單"
            
        elif sell_score > 0 and sell_score > buy_score:
            if sell_score >= 3: sig = "強力賣出"
            elif sell_score == 2: sig = "少量出單"
            else: sig = "先賣一張"

        return {
            'title': 'MACD + RSI 策略',
            'signal': sig,
            'desc': desc,
            'vals': {
                'DIF': dif,
                'MACD': mac,
                '日 RSI': day_rsi,
                '週 RSI': week_rsi,
                '多方得分': f"{buy_score}/4",
                '空方得分': f"{sell_score}/4"
            }
        }

    except Exception as e:
        print(f"[MACD+RSI Error] {e}")
        return {
            'title': 'MACD+RSI 錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {}
        }