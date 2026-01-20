import pandas as pd

def analyze(df):
    """
    策略核心：Alexander Elder (柱狀體動能) + 朱家泓 (雙線型態)
    """
    try:
        # 1. 數據準備
        close = df['Close']
        if len(close) < 35: return None # MACD 需要約 30 天以上資料才準

        # 2. 計算 MACD 標準公式
        # 快線 (12 EMA)
        exp12 = close.ewm(span=12, adjust=False).mean()
        # 慢線 (26 EMA)
        exp26 = close.ewm(span=26, adjust=False).mean()
        # DIF (快 - 慢)
        dif = exp12 - exp26
        # MACD 信號線 (9 EMA of DIF)
        macd = dif.ewm(span=9, adjust=False).mean()
        # 柱狀體 OSC (DIF - MACD) -> Elder 最看重的動能
        osc = dif - macd

        # 3. 取得關鍵數據 (當前 vs 前一日)
        c_dif, p_dif = dif.iloc[-1], dif.iloc[-2]
        c_macd, p_macd = macd.iloc[-1], macd.iloc[-2]
        c_osc, p_osc = osc.iloc[-1], osc.iloc[-2]
        
        # 4. 訊號邏輯
        
        # --- A. Alexander Elder 動能分析 (看柱狀體斜率) ---
        # 柱狀體往上長 (紅柱變短 或 綠柱變長) = 多頭動能增強
        elder_bull_power = c_osc > p_osc
        # 柱狀體往下長 (綠柱變短 或 紅柱變長) = 空頭動能增強
        elder_bear_power = c_osc < p_osc

        # --- B. 朱家泓 位置與型態分析 (看 DIF 與 零軸) ---
        zhu_bull_zone = c_dif > 0  # 水上 (多頭浪)
        zhu_bear_zone = c_dif < 0  # 水下 (空頭浪)
        
        # 金叉與死叉判定
        golden_cross = c_dif > c_macd and p_dif <= p_macd
        death_cross = c_dif < c_macd and p_dif >= p_macd

        # =================================================
        # 綜合訊號判斷
        # =================================================
        
        short_sig = "觀望"
        swing_sig = "觀望"
        desc = ""
        
        # --- 1. 短線訊號 (進出場時機) ---
        # 買點：朱家泓金叉 + Elder動能向上
        if golden_cross:
            if zhu_bull_zone:
                short_sig = "買進 (水上金叉)"
                desc = "朱家泓：回檔結束，多頭續攻。"
            else:
                short_sig = "搶短 (水下金叉)"
                desc = "朱家泓：跌深反彈，短線操作。"
        # 買點：Elder 翻紅 (柱狀體由負轉正)
        elif p_osc < 0 and c_osc > 0:
            short_sig = "買進 (動能翻紅)"
            desc = "Elder：空頭力竭，多頭接棒。"
            
        # 賣點：死叉 或 Elder 動能轉弱
        elif death_cross:
            short_sig = "賣出 (死叉)"
            desc = "朱家泓：轉折向下，獲利了結。"
        elif elder_bear_power and c_osc > 0:
            # 綠柱變短，雖然還沒死叉，但 Elder 認為動能已失
            short_sig = "減碼 (動能減弱)"
            desc = "Elder：多頭動能衰退 (綠柱縮短)。"


        # --- 2. 波段訊號 (趨勢判定) ---
        # 多頭波段：Elder 動能向上 且 (DIF > 0 或 剛金叉)
        if elder_bull_power and (zhu_bull_zone or golden_cross):
            swing_sig = "持有 (多頭)"
            if zhu_bull_zone:
                swing_desc = "Elder：動能向上 + 朱家泓：水上行舟"
            else:
                swing_desc = "Elder：動能轉強，打底完成"
        
        # 空頭波段：Elder 動能向下
        elif elder_bear_power:
            swing_sig = "空手 (空頭)"
            if zhu_bear_zone:
                swing_desc = "Elder：動能向下 + 朱家泓：水下沉船"
            else:
                swing_desc = "Elder：獲利回吐賣壓"
        
        else:
            swing_desc = "多空力道膠著"

        # --- 3. 最終整合 ---
        final_sig = short_sig
        
        # 顯示數值整理
        vals = {
            'DIF (快線)': round(c_dif, 2),
            'MACD (慢線)': round(c_macd, 2),
            '柱狀體 (OSC)': round(c_osc, 2),
            'Elder動能': '增強 ↗' if elder_bull_power else '衰退 ↘',
            '朱家泓水位': '水上 (多)' if zhu_bull_zone else '水下 (空)'
        }

        return {
            'title': 'MACD (Elder x 朱家泓)',
            'signal': final_sig,
            'desc': f"{desc} {swing_desc}",
            'vals': vals
        }

    except Exception as e:
        print(f"[MACD Error] {e}")
        return {
            'title': 'MACD 分析錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {'DIF': 0, 'MACD': 0}
        }