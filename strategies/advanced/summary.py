import pandas as pd
import numpy as np
from strategies.basic import qqe, kd, rsi

# 自動拆包小幫手
def extract_df(data):
    if isinstance(data, tuple):
        return data[0]
    return data

def extract_rev_df(data):
    if isinstance(data, tuple) and len(data) > 1:
        return data[1]
    return None

def analyze(df, stock_code=None, fin_data=None, chip_data=None, margin_data=None, buy_price=None, market_type='TW'):
    """
    Role: 總分析師 (Portfolio Manager Ver.)
    Task: 整合 技術+基本+籌碼+信用 + 成本價位建議，支援多市場擴充。
    """
    # 1. 資料清洗
    original_df = extract_df(df)
    fin_df = extract_df(fin_data)
    rev_df = extract_rev_df(fin_data) # 單獨抽出月營收
    chip_df = extract_df(chip_data)
    margin_df = extract_df(margin_data)

    # 2. 基礎防呆
    if original_df is None or original_df.empty:
        return {'title': '綜合診斷', 'signal': '資料不足', 'desc': '無法取得行情資料', 'vals': {}}

    try:
        # --- 1. 技術面評估 (共用模組) ---
        close = float(original_df['Close'].iloc[-1])
        ma5 = original_df['Close'].rolling(5).mean().iloc[-1]
        ma20 = original_df['Close'].rolling(20).mean().iloc[-1]
        ma60 = original_df['Close'].rolling(60).mean().iloc[-1]
        
        # 價量關係 (判斷是否有爆大量)
        vol = float(original_df['Volume'].iloc[-1])
        vol_ma5 = original_df['Volume'].rolling(5).mean().iloc[-1]
        is_vol_surge = vol > vol_ma5 * 1.5

        # MACD
        exp12 = original_df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = original_df['Close'].ewm(span=26, adjust=False).mean()
        macd_line = exp12 - exp26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_val = macd_line.iloc[-1]
        sig_val = signal_line.iloc[-1]

        # QQE, KD, RSI 的三位一體判斷
        res_kd = kd.calculate_kd(original_df['Close'], original_df['High'], original_df['Low'])
        k_val, d_val = res_kd[0], res_kd[1]
        rsi_val = rsi.calculate_rsi(original_df['Close'], period=14)
        rsi_ma, qqe_band, qqe_trend = qqe.calculate_qqe(original_df)
        q_trend = qqe_trend.iloc[-1]

        tech_score = 0
        if close > ma5: tech_score += 5
        if close > ma20: tech_score += 5
        if close > ma60: tech_score += 5
        if ma5 > ma20: tech_score += 5
        if macd_val > sig_val: tech_score += 5
        if is_vol_surge and close > original_df['Close'].iloc[-2]: tech_score += 5 # 價跌量縮或價漲量增
        
        # QQE + KD + RSI 權重增益
        osc_score = 0
        if q_trend == 1: osc_score += 5       # QQE 看多
        if k_val > d_val: osc_score += 5      # KD 金叉
        if rsi_val > 50: osc_score += 5       # RSI 強勢區
        
        # 三向共振加成
        is_synergy = (q_trend == 1 and k_val > d_val and rsi_val > 50)
        if is_synergy: osc_score += 10
        
        tech_score += osc_score
        tech_score = min(50, tech_score) # 技術面上限調整為 50

        # ========== 各市場專屬分析 ==========
        fund_score = 0
        pe_ratio = "N/A"
        revenue_msg = "無營收數據"
        chip_score = 0
        inst_msg = "無籌碼數據"
        margin_score = 0
        margin_msg = "無信用數據"
        macro_msg = "無"

        if market_type == 'TW':
            # --- 2A. 台股基本面 (權重 20%) ---
            # 台股極度重視月營收增長
            if rev_df is not None and not rev_df.empty:
                try:
                    latest_rev = float(rev_df['revenue'].iloc[-1])
                    prev_rev_yy = float(rev_df['revenue_year'].iloc[-1]) # 去年同期
                    yoy = (latest_rev - prev_rev_yy) / prev_rev_yy * 100 if prev_rev_yy > 0 else 0
                    if yoy > 15: fund_score += 10
                    elif yoy > 0: fund_score += 5
                    revenue_msg = f"YoY {yoy:+.1f}%"
                except: pass

            try:
                import sys
                import os
                sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
                from data_loader import get_stock_and_category_pe
                
                cat_pe_str = "N/A"
                if stock_code:
                    stock_pe, cat_avg_pe, cat_name = get_stock_and_category_pe(stock_code)
                    if stock_pe > 0:
                        pe_ratio = f"{stock_pe:.1f}"
                        if 0 < stock_pe < 15: fund_score += 10 
                        elif 15 <= stock_pe < 25: fund_score += 5 
                    else:
                        fund_score += 10 # 沒 PE 就預設給分
                        
                    if cat_avg_pe > 0:
                        cat_pe_str = f"{cat_avg_pe:.1f} 倍 ({cat_name})"
            except Exception as e:
                print(f"Summary PE fetch error: {e}")
                fund_score += 10
                cat_pe_str = "N/A"

            # 計算去年和前年 EPS
            eps_ly = "N/A"
            eps_py = "N/A"
            if fin_df is not None and not fin_df.empty:
                try:
                    eps_data = fin_df[fin_df['type'] == 'EPS'].copy()
                    if not eps_data.empty:
                        eps_data['year'] = eps_data['date'].astype(str).str[:4]
                        yearly_eps = eps_data.groupby('year')['value'].sum().round(2).to_dict()
                        import datetime
                        curr_y = datetime.datetime.now().year
                        eps_ly = yearly_eps.get(str(curr_y - 1), "N/A")
                        eps_py = yearly_eps.get(str(curr_y - 2), "N/A")
                except Exception as e:
                    print(f"Summary EPS calc error: {e}")
            
            # --- 3A. 台股籌碼面 (三大法人) (權重 20%) ---
            if chip_df is not None and not chip_df.empty:
                recent_days = 3
                recent_chips = chip_df.tail(recent_days)
                
                foreign_buy = recent_chips['Foreign_Investor_Net'].sum() if 'Foreign_Investor_Net' in recent_chips.columns else 0
                trust_buy = recent_chips['Investment_Trust_Net'].sum() if 'Investment_Trust_Net' in recent_chips.columns else 0
                dealer_buy = recent_chips['Dealer_Net'].sum() if 'Dealer_Net' in recent_chips.columns else 0
                
                total_buy = foreign_buy + trust_buy + dealer_buy
                
                if total_buy > 0: chip_score += 10
                if trust_buy > 0: chip_score += 10 # 台股投信作帳行情重
                
                inst_msg = f"近{recent_days}日合買 {int(total_buy//1000)} 張"
                if total_buy < 0: inst_msg = f"近{recent_days}日合賣 {int(abs(total_buy)//1000)} 張"

            # --- 4A. 台股信用面 (融資券) (權重 10%) ---
            if margin_df is not None and not margin_df.empty:
                latest = margin_df.iloc[-1]
                prev = margin_df.iloc[-2] if len(margin_df) > 1 else latest
                
                mp_bal = float(latest.get('MarginPurchaseTodayBalance', 0))
                mp_prev = float(prev.get('MarginPurchaseTodayBalance', 0))
                mp_change = mp_bal - mp_prev
                
                ss_bal = float(latest.get('ShortSaleTodayBalance', 0))
                ss_prev = float(prev.get('ShortSaleTodayBalance', 0))
                ss_change = ss_bal - ss_prev
                
                prev_close = float(original_df['Close'].iloc[-2]) if len(original_df) > 1 else close
                price_change = close - prev_close
                
                if mp_change < 0: 
                    margin_score += 10
                    margin_msg = "融資減 (籌碼趨穩)"
                elif mp_change > 0 and price_change < 0:
                    margin_score -= 5
                    margin_msg = "融資增 (接刀風險)"
                else:
                    margin_score += 5
                    margin_msg = "融資持平"

                if ss_change > 0 and price_change > 0:
                    margin_score += 5
                    margin_msg += " + 軋空發動"

        elif market_type == 'US':
            # --- 2B. 美股未來擴充保留區 ---
            # 美股更看重每季財報 EPS Beat/Miss, Foward Guidance (未來指引), 總經 (Fed rate) 等
            macro_msg = "美股指標(建置中)"
            # fund_score, chip_score 的邏輯將改為選項及大戶期權動向 (Options Gamma 避險)
            fund_score = 15
            chip_score = 15

        elif market_type == 'CRYPTO':
            # --- 2C. 加密貨幣未來擴充保留區 ---
            # 幣圈更看重鏈上數據(On-chain data), 資金費率(Funding Rate), 爆倉熱圖等
            macro_msg = "加密指標(建置中)"
            fund_score = 15
            chip_score = 15
            
        elif market_type == 'FUTURES':
            # --- 2D. 期貨未來擴充保留區 ---
            # 期貨更看重未平倉量(OI), 價差(Basis), 散戶多空比等
            macro_msg = "期貨指標(建置中)"
            fund_score = 15
            chip_score = 15

        elif market_type == 'OPTIONS':
            # --- 2E. 選擇權未來擴充保留區 ---
            # 選擇權更看重隱含波動率(IV), Put/Call Ratio, 最大痛點(Max Pain) 等
            macro_msg = "選擇權指標(建置中)"
            fund_score = 15
            chip_score = 15
        else:
            # 預設通用
            pass

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
                if is_synergy: advice += " [觸發三位一體指標共振]"
            
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
            '💡 系統操作建議': advice,
            '收盤價': f"{close}",
            'QQE 趨勢': "🟢 多頭" if q_trend == 1 else "🔴 空頭",
            'KD 狀態': "黃金交叉" if k_val > d_val else "死亡交叉",
            'RSI (14)': f"{rsi_val:.1f}"
        }

        # 依市場動態加入欄位
        if market_type == 'TW':
            vals['法人動向'] = inst_msg
            vals['資券變化'] = margin_msg
            vals['月營收(YoY)'] = revenue_msg
            vals['個股本益比'] = f"{pe_ratio} 倍" if pe_ratio != "N/A" else "N/A"
            vals['類股平均本益比'] = cat_pe_str
            vals['去年EPS'] = f"{eps_ly} 元" if eps_ly != "N/A" else "N/A"
            vals['前年EPS'] = f"{eps_py} 元" if eps_py != "N/A" else "N/A"
        else:
            vals['總經/衍生品'] = macro_msg

        return {
            'title': f'綜合全方位健檢 ({market_type})',
            'signal': signal,
            'desc': desc,
            'vals': vals
        }

    except Exception as e:
        print(f"[Summary Error] {e}")
        return {'title': '分析異常', 'signal': 'ERROR', 'desc': '數據格式異常，請檢查 Logs', 'vals': {}}
