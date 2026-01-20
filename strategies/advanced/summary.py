import pandas as pd
import numpy as np

def analyze(df, stock_code=None, fin_data=None, chip_data=None):
    """
    Role: 首席投資長 (CIO) - 優化評級版
    Task: 綜合 "技術面 + 基本面 + 籌碼面" 給出符合直覺的評級
    """
    if df is None or df.empty:
        return None

    try:
        # ==================================
        # 1. 技術面診斷 (滿分約 60)
        # ==================================
        close = df['Close']
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        ma60 = close.rolling(60).mean()
        
        curr_close = close.iloc[-1]
        curr_ma5 = ma5.iloc[-1]
        curr_ma20 = ma20.iloc[-1]
        curr_ma60 = ma60.iloc[-1]
        
        tech_score = 0
        tech_msg = []
        
        # 均線排列
        if curr_close > curr_ma5 > curr_ma20 > curr_ma60:
            tech_score += 40
            tech_msg.append("均線多頭排列")
        elif curr_close > curr_ma20:
            tech_score += 20
            tech_msg.append("站上月線")
        elif curr_close < curr_ma5 < curr_ma20 < curr_ma60:
            tech_score -= 40
            tech_msg.append("均線空頭排列")
        else:
            tech_msg.append("均線糾結")

        # KD 指標
        rsv = (close - df['Low'].rolling(9).min()) / (df['High'].rolling(9).max() - df['Low'].rolling(9).min()) * 100
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        if k.iloc[-1] > d.iloc[-1] and k.iloc[-1] < 80:
            tech_score += 15 #稍微加重KD權重
            tech_msg.append("KD金叉")

        # ==================================
        # 2. 籌碼面診斷 (滿分約 50)
        # ==================================
        chip_score = 0
        chip_msg = []
        
        if chip_data is not None and not chip_data.empty:
            chip_df = chip_data.pivot_table(index='date', columns='name', values='net', aggfunc='sum').fillna(0).sort_index()
            if not chip_df.empty:
                latest = chip_df.iloc[-1]
                foreign = latest.get('Foreign_Investor', 0) / 1000
                trust = latest.get('Investment_Trust', 0) / 1000
                
                # 投信 (權重最高)
                if trust > 0:
                    chip_score += 25 # 加重投信權重
                    chip_msg.append("投信買超")
                elif trust < 0:
                    chip_score -= 25
                    chip_msg.append("投信賣超")
                    
                # 外資
                if foreign > 1000:
                    chip_score += 15
                    chip_msg.append("外資大買")
                elif foreign < -1000:
                    chip_score -= 15
                    chip_msg.append("外資大賣")
                    
                # 土洋合作
                if trust > 0 and foreign > 0:
                    chip_score += 10
                    chip_msg.append("土洋合一")
        else:
            chip_msg.append("無籌碼資料")

        # ==================================
        # 3. 基本面診斷 (滿分約 40)
        # ==================================
        fund_score = 0
        fund_msg = []
        
        if fin_data:
            df_fin, df_rev = fin_data
            if not df_rev.empty:
                latest_rev = df_rev.sort_values('date').iloc[-1]
                yoy = latest_rev['revenue_year']
                
                if yoy > 20: 
                    fund_score += 30
                    fund_msg.append("營收爆發")
                elif yoy > 0: 
                    fund_score += 15
                    fund_msg.append("營收成長")
                else: 
                    fund_score -= 15
                    fund_msg.append("營收衰退")
        else:
            fund_msg.append("無財報資料")

        # ==================================
        # 4. 綜合總結 (總分理論上限約 150)
        # ==================================
        total_score = tech_score + chip_score + fund_score
        
        # ★ 優化後的評級標準 (符合人類直覺)
        if total_score >= 80:
            signal = "🚀 強力買進 (Strong Buy)"
            style = "多頭共振 (S級)"
            advice = "各面向皆強，建議積極佈局。"
        elif total_score >= 50:
            signal = "📈 積極偏多 (Buy)"
            style = "趨勢向上 (A級)"
            advice = "多方佔優，適合順勢操作。"
        elif total_score >= 20:
            signal = "👀 謹慎偏多 (Hold/Buy)"
            style = "震盪偏多 (B級)"
            advice = "基本面或籌碼有支撐，可分批佈局。"
        elif total_score <= -20:
            signal = "📉 偏空操作 (Sell)"
            style = "空方控盤"
            advice = "趨勢轉弱，建議保守或減碼。"
        else:
            signal = "⚖️ 中立觀望 (Neutral)"
            style = "多空不明"
            advice = "缺乏明確方向，建議觀望。"

        # 產生描述
        tech_str = "、".join(tech_msg) if tech_msg else "無技術訊號"
        chip_str = "、".join(chip_msg) if chip_msg else "籌碼中性"
        fund_str = "、".join(fund_msg) if fund_msg else "財報平平"
        
        full_desc = f"【技術】{tech_str}。【籌碼】{chip_str}。【基本】{fund_str}。"

        return {
            'title': 'AI 全方位綜合診斷 (優化版)',
            'signal': signal,
            'desc': full_desc,
            'vals': {
                '總分評級': f"{total_score} 分",
                '技術面': tech_msg[0] if tech_msg else "-",
                '籌碼面': chip_msg[0] if chip_msg else "-",
                '基本面': fund_msg[0] if fund_msg else "-",
                'AI 觀點': advice
            }
        }

    except Exception as e:
        return {
            'title': '綜合診斷失敗',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {}
        }