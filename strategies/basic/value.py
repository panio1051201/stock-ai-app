import pandas as pd
import yfinance as yf
import math

def analyze(df, stock_code=None):
    """
    Role: 資深價值投資與護城河分析師 (Senior Value Investing & Moat Analyst)
    Task: 執行深度基本面量化評級 (A-E)
    """
    try:
        if not stock_code:
            return {'title': '錯誤', 'signal': 'ERR', 'desc': '無法取得代碼', 'vals': {}}

        # --- 兼容性修正 (FinMind -> YFinance) ---
        # 如果傳進來的是純數字 (如 2330)，yfinance 需要加上 .TW 才能抓到台股財報
        # 移除可能存在的空白
        stock_code = str(stock_code).strip()
        
        if stock_code.isdigit():
            yf_code = f"{stock_code}.TW"
        else:
            yf_code = stock_code

        print(f"[Deep Research] 啟動價值分析程序: {yf_code} ...")
        ticker = yf.Ticker(yf_code)
        info = ticker.info
        
        # --- Phase 1: 數據挖掘 (Information Gathering) ---
        # 取得關鍵財務數據 (若無數據則給預設值以防報錯)
        if df.empty:
            price = 0
        else:
            price = df['Close'].iloc[-1]
        
        # 1. 獲利能力 (護城河代理指標)
        roe = info.get('returnOnEquity', 0) or 0
        gross_margin = info.get('grossMargins', 0) or 0
        op_margin = info.get('operatingMargins', 0) or 0
        
        # 2. 財務健康 (抗脆弱性)
        total_debt = info.get('totalDebt', 0) or 0
        total_equity = info.get('totalStockholderEquity', 1) or 1
        debt_to_equity = info.get('debtToEquity', 0)
        
        # yfinance 的 debtToEquity 有時是百分比 (50=50%) 有時是小數 (0.5=50%)
        # 這裡做一個簡單的標準化：如果大於 10，通常是百分比，轉為小數
        if debt_to_equity and debt_to_equity > 10: 
            debt_to_equity /= 100 
        elif debt_to_equity is None:
             debt_to_equity = 0
        
        current_ratio = info.get('currentRatio', 0) or 0
        
        # 3. 現金流 (真實獲利)
        fcf = info.get('freeCashflow', 0) or 0
        
        # 4. 估值 (葛拉漢基準)
        eps = info.get('trailingEps', 0)
        bvps = info.get('bookValue', 0)
        
        # --- Phase 2: 結構化評分 (Scoring Framework) ---
        # 滿分 100 分，根據巴菲特/葛拉漢邏輯配分
        score = 0
        reasons = []
        risks = []
        
        # 1. 護城河檢測 (40分) - 高 ROE 與 利潤率代表有護城河
        if roe > 0.15: 
            score += 20
            reasons.append("高ROE(護城河寬)")
        elif roe > 0.10: 
            score += 10
            
        if gross_margin > 0.40: # 40% 毛利通常代表有定價權
            score += 10
            reasons.append("高毛利(定價權)")
        elif gross_margin > 0.20:
            score += 5
            
        if op_margin > 0.10: score += 10 # 營業利益率健康
        
        # 2. 抗脆弱性檢測 (30分) - 低負債與流動性
        if debt_to_equity < 0.5: 
            score += 15
            reasons.append("低負債(抗脆弱)")
        elif debt_to_equity < 1.0: 
            score += 5
        else:
            risks.append("高槓桿風險")
            
        if current_ratio > 1.5: score += 10 # 流動性佳
        if fcf > 0: 
            score += 5 
            reasons.append("自由現金流正")
        else:
            risks.append("自由現金流為負")

        # 3. 估值安全邊際 (30分)
        graham_price = 0
        if eps and bvps and eps > 0 and bvps > 0:
            graham_price = math.sqrt(22.5 * eps * bvps)
            if price < graham_price * 0.8: # 八折以下
                score += 30
                reasons.append("深度低估(安全邊際大)")
            elif price < graham_price:
                score += 20
                reasons.append("價格合理")
            elif price > graham_price * 1.5:
                score -= 10 # 懲罰過高估值
                risks.append("估值過高")
        else:
            # 虧損公司無法計算葛拉漢數
            risks.append("EPS或淨值為負")
            score -= 20 # 嚴重扣分

        # --- Phase 3: 綜合評級 (Final Verdict) ---
        rating = "C"
        verdict = "適合1年以上長期持有"

        if score >= 85:
            rating = "A"
            verdict = "適合10年以上長期持有 (傳世資產)"
        elif score >= 70:
            rating = "B"
            verdict = "適合5年以上長期持有 (核心配置)"
        elif score >= 50:
            rating = "C"
            verdict = "適合1年以上長期持有 (中期觀察)"
        elif score >= 30:
            rating = "D"
            verdict = "找適當時機賣出 (結構衰退)"
        else:
            rating = "E"
            verdict = "盡快賣出 (極度危險)"

        # 格式化輸出
        risk_alert = " | ".join(risks[:2]) if risks else "無顯著財務風險"

        desc = f"得分:{score} | {verdict}"
        
        return {
            'title': '巴菲特護城河評級',
            'signal': f"評級: {rating}",
            'desc': desc,
            'vals': {
                '綜合得分': score,
                'ROE (%)': f"{round(roe*100, 1)}%",
                '毛利率 (%)': f"{round(gross_margin*100, 1)}%",
                '負債權益比': round(debt_to_equity, 2),
                '合理價': round(graham_price, 2) if graham_price else "無法計算",
                '風險提示': risk_alert
            }
        }

    except Exception as e:
        print(f"[Value Analysis Error] {e}")
        import traceback
        traceback.print_exc()
        return {
            'title': '價值分析錯誤',
            'signal': 'ERROR',
            'desc': '無法取得財報數據或計算錯誤',
            'vals': {}
        }