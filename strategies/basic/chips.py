import pandas as pd

def analyze(df, stock_code=None):
    """
    Role: 籌碼分析師 (Chip Analyst)
    Task: 分析外資、投信、自營商的動向
    """
    if df.empty:
        return {
            'title': '籌碼分析 (三大法人)',
            'signal': '無數據',
            'desc': '查無近期法人進出資料。',
            'vals': {}
        }

    try:
        # 1. 整理數據：將三大法人分開
        # Foreign_Investor (外資), Investment_Trust (投信), Dealer (自營商)
        pivot_df = df.pivot_table(index='date', columns='name', values='net', aggfunc='sum').fillna(0)
        pivot_df = pivot_df.sort_index()

        # 取得最新一天的數據
        latest = pivot_df.iloc[-1]
        
        foreign = latest.get('Foreign_Investor', 0) / 1000 # 轉張數 (原本是股數)
        trust = latest.get('Investment_Trust', 0) / 1000
        dealer = latest.get('Dealer_Self_Analysis', 0) + latest.get('Dealer_Hedging', 0) # 自營商通常分自行買賣和避險
        if 'Dealer' in latest: dealer += latest['Dealer'] # 舊格式相容
        dealer = dealer / 1000 

        total_net = foreign + trust + dealer

        # 2. 計算近 5 日累積 (主力連續動向)
        last_5 = pivot_df.tail(5)
        sum_5_trust = last_5.get('Investment_Trust', pd.Series([0])).sum() / 1000
        sum_5_foreign = last_5.get('Foreign_Investor', pd.Series([0])).sum() / 1000

        # 3. 訊號判定邏輯
        score = 0
        reasons = []

        # 投信 (內資風向球，最準)
        if trust > 0: 
            score += 30
            reasons.append("投信買超")
        if sum_5_trust > 1000: # 近5日買超大於1000張
            score += 20
            reasons.append("投信連買")
            
        # 外資 (權值股推手)
        if foreign > 0: 
            score += 10
            reasons.append("外資買超")
        elif foreign < -5000:
            score -= 20
            reasons.append("外資大逃殺")

        # 三大法人同步
        if foreign > 0 and trust > 0 and dealer > 0:
            score += 20
            reasons.append("土洋合一(三法同買)")

        # 結論
        if score >= 50:
            signal = "籌碼大好 A+"
            desc = "主力資金湧入，易漲難跌。"
        elif score >= 20:
            signal = "籌碼偏多 B"
            desc = "法人站在買方，有利多頭。"
        elif score <= -20:
            signal = "籌碼渙散 D"
            desc = "法人調節賣出，需提防下殺。"
        else:
            signal = "籌碼觀望 C"
            desc = "多空力道互抵，等待方向。"

        vals = {
            '外資 (最新)': f"{int(foreign)} 張",
            '投信 (最新)': f"{int(trust)} 張",
            '自營 (最新)': f"{int(dealer)} 張",
            '今日合計': f"{int(total_net)} 張",
            '投信近5日': f"{int(sum_5_trust)} 張",
            '外資近5日': f"{int(sum_5_foreign)} 張",
            '綜合評分': score
        }

        return {
            'title': '三大法人籌碼分析',
            'signal': signal,
            'desc': f"{desc} ({', '.join(reasons)})",
            'vals': vals
        }

    except Exception as e:
        return {
            'title': '分析錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {}
        }