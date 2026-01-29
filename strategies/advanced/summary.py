import pandas as pd
import numpy as np

# 自動拆包小幫手
def extract_df(data):
    if isinstance(data, tuple):
        return data[0]
    return data

def analyze(df, stock_code=None, fin_data=None, chip_data=None, margin_data=None, buy_price=None):
    """
    Role: AI 總分析師 (Portfolio Manager Ver.)
    Task: 整合 技術+基本+籌碼+信用 + 成本價位建議
    """
    # 1. 資料清洗
    df = extract_df(df)
    fin_data = extract_df(fin_data)
    chip_data = extract_df(chip_data)
    margin_data = extract_df(margin_data)

    # 2. 基礎防呆
    if df is None or df.empty:
        return {'title': '綜合診斷', 'signal': '資料不足', 'desc': '無法取得行情資料', 'vals': {}}

    try:
        # --- 1. 技術面評估 (權重 40%) ---
        close = float(df['Close'].iloc[-1])
        ma5 = df['Close'].rolling(5).mean().iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        
        # MACD
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_val = macd.iloc[-1]
        sig_val = signal_line.iloc[-1]

        tech_score = 0
        if close > ma5: tech_score += 10
        if close > ma20: tech_score += 10
        if close > ma60: tech_score += 10
        if ma5 > ma20: tech_score += 10
        if macd_val > sig_val: tech_score += 10 

        # --- 2. 基本面評估 (權重 20%) ---
        fund_score = 0
        pe_ratio = "N/A"
        if fin_data is not None and not fin_data.empty:
            if 'PER' in fin_data.columns:
                pe = fin_data['PER'].iloc[-1]
                pe_ratio = f"{pe:.1f}"
                if 0 < pe < 15: fund_score += 20 
                elif 15 <= pe < 25: fund_score += 10 
            else:
                fund_score += 10 

        # --- 3. 籌碼面評估 (權重 20%) ---
        chip_score = 0
        inst_msg = "無法人數據"
        if chip_data is not None and not chip_data.empty:
            recent_days = 3
            recent_chips = chip_data.tail(recent_days)
            
            foreign_buy = recent_chips['Foreign_Investor_Net'].sum() if 'Foreign_Investor_Net' in recent_chips.columns else 0
            trust_buy = recent_chips['Investment_Trust_Net'].sum() if 'Investment_Trust_Net' in recent_chips.columns else 0
            dealer_buy = recent_chips['Dealer_Net'].sum() if 'Dealer_Net' in recent_chips.columns else 0
            
            total_buy = foreign_buy + trust_buy + dealer_buy
            
            if total_buy > 0: chip_score += 10
            if trust_buy > 0: chip_score += 10 
            
            inst_msg = f"近{recent_days}日法人合買 {int(total_buy//1000)} 張"
            if total_buy < 0: inst_msg = f"近{recent_days}日法人合賣 {int(abs(total_buy)//1000)} 張"

        # --- 4. 信用面評估 (融資券) (權重 20%) ---
        margin_score = 0
        margin_msg = "無融資券數據"
        if margin_data is not None and not margin_data.empty:
            latest = margin_data.iloc[-1]
            prev = margin_data.iloc[-2] if len(margin_data) > 1 else latest
            
            mp_bal = float(latest.get('MarginPurchaseTodayBalance', 0))
            mp_prev = float(prev.get('MarginPurchaseTodayBalance', 0))
            mp_change = mp_bal - mp_prev
            
            ss_bal = float(latest.get('ShortSaleTodayBalance', 0))
            ss_prev = float(prev.get('ShortSaleTodayBalance', 0))
            ss_change = ss_bal - ss_prev
            
            prev_close = float(df['Close'].iloc[-2]) if len(df) > 1 else close
            price_change = close - prev_close
            
            if mp_change < 0: 
                margin_score += 10
                margin_msg = "融資減少 (籌碼趨穩)"
            elif mp_change > 0 and price_change < 0:
                margin_score -= 5
                margin_msg = "融資增加 (接刀風險)"
            else:
                margin_score += 5
                margin_msg = "融資持平"

            if ss_change > 0 and price_change > 0:
                margin_score += 10
                margin_msg += " + 軋空發動"

        # --- 5. 總分計算 ---
        total_score = tech_score + fund_score + chip_score + margin_score
        total_score = min(100, max(0, total_score))
        
        signal = "觀望"
        if total_score >= 80: signal = "強力買進 (Strong Buy)"
        elif total_score >= 60: signal = "偏多操作 (Buy)"
        elif total_score <= 40: signal = "偏空操作 (Sell)"
        
        desc = f"技術{tech_score}分, 基本{fund_score}分, 籌碼{chip_score}分, 信用{margin_score}分"
        
        # --- 6. 持倉建議 (如果有輸入成本) ---
        advice = "請輸入成本以獲取建議"
        if buy_price and buy_price > 0:
            roi = (close - buy_price) / buy_price * 100
            
            # A. 高分區 (多頭強勢)
            if total_score >= 75:
                if roi > 0: advice = "🔥 趨勢極強+獲利中 ➔ 建議加碼 (Pyramiding)"
                else: advice = "📉 遭錯殺+基本面好 ➔ 建議分批攤平 (Average Down)"
            
            # B. 中高分區 (震盪偏多)
            elif total_score >= 60:
                if roi > 0: advice = "✅ 訊號穩健 ➔ 續抱，設好移動停利"
                else: advice = "👀 尚未轉強 ➔ 暫時觀望，等待打底"
            
            # C. 中低分區 (震盪偏空)
            elif total_score >= 40:
                if roi > 0: advice = "⚠️ 動能減弱 ➔ 建議獲利減碼"
                else: advice = "💔 趨勢不明 ➔ 反彈時考慮停損"
            
            # D. 低分區 (空頭走勢)
            else:
                if roi > 0: advice = "🚨 籌碼鬆動 ➔ 建議獲利了結 (Take Profit)"
                else: advice = "🩸 趨勢轉空 ➔ 建議果斷停損 (Stop Loss)"

        vals = {
            '🏆 總分評級': f"{total_score} 分",
            '信號': signal,
            '💡 AI 操作建議': advice, # 新增這一行
            '收盤價': f"{close}",
            '均線狀態': "多頭排列" if close > ma20 > ma60 else "整理/空頭",
            'PER 本益比': pe_ratio,
            '法人動向': inst_msg,
            '資券變化': margin_msg,
            'MACD': "黃金交叉" if macd_val > sig_val else "死亡交叉"
        }

        return {
            'title': 'AI 全方位健檢',
            'signal': signal,
            'desc': desc,
            'vals': vals
        }

    except Exception as e:
        print(f"[Summary Error] {e}")
        return {'title': '分析異常', 'signal': 'ERROR', 'desc': '數據格式異常，請檢查 Logs', 'vals': {}}