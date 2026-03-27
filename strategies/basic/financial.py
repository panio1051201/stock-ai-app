import pandas as pd

def analyze(data_tuple, stock_code=None):
    """
    Role: 財報分析師 (Financial Analyst)
    Task: 分析 EPS 趨勢、三率(毛利/營益/淨利) 與 月營收成長動能
    Input: (df_fin, df_rev) 財報與營收的 Tuple
    """
    df_fin, df_rev = data_tuple
    
    if df_fin.empty or df_rev.empty:
        return {
            'title': '財報資料不足',
            'signal': '無數據',
            'desc': 'FinMind 無法取得該股足夠的財報或營收資料 (可能是新股或資料庫缺漏)。',
            'vals': {}
        }

    try:
        # --- 1. 財報處理 (EPS & 毛利率) ---
        # 篩選 EPS
        eps_data = df_fin[df_fin['type'] == 'EPS'].sort_values('date')
        # 篩選 毛利率 (GrossProfitMargin) - 財報項目名稱可能為 GrossProfitMargin
        gm_data = df_fin[df_fin['type'] == 'GrossProfitMargin'].sort_values('date')
        
        current_eps = 0
        last_eps = 0
        eps_growth = 0
        
        if not eps_data.empty:
            current_eps = eps_data.iloc[-1]['value']
            # 計算近四季 EPS 總和 (預估本益比用)
            ttm_eps = eps_data.tail(4)['value'].sum()
            
            # 比較上一季
            if len(eps_data) >= 2:
                last_eps = eps_data.iloc[-2]['value']
                eps_growth = (current_eps - last_eps) / abs(last_eps) * 100 if last_eps != 0 else 0
                
            # 計算去年和前年 EPS
            eps_data['year'] = eps_data['date'].astype(str).str[:4]
            yearly_eps = eps_data.groupby('year')['value'].sum().round(2).to_dict()
            import datetime
            curr_y = datetime.datetime.now().year
            eps_ly = yearly_eps.get(str(curr_y - 1), "N/A")
            eps_py = yearly_eps.get(str(curr_y - 2), "N/A")
        else:
            eps_ly = "N/A"
            eps_py = "N/A"

        current_gm = gm_data.iloc[-1]['value'] if not gm_data.empty else 0

        # --- 2. 營收處理 (MoM, YoY) ---
        # 確保日期排序
        df_rev = df_rev.sort_values('date')
        latest_rev = df_rev.iloc[-1]
        
        rev_mom = latest_rev['revenue_month'] # 月增率
        rev_yoy = latest_rev['revenue_year']  # 年增率
        current_revenue = latest_rev['revenue'] / 100000000 # 轉為億元

        # --- 3. 綜合評分與訊號 ---
        score = 0
        reasons = []
        
        # EPS 成長
        if eps_growth > 0: 
            score += 20
            reasons.append("EPS季增")
        if current_eps > 0: score += 10
        
        # 營收動能
        if rev_yoy > 20: 
            score += 30
            reasons.append("營收爆發(>20%)")
        elif rev_yoy > 0: 
            score += 10
            reasons.append("營收成長")
        else:
            reasons.append("營收衰退")
            
        if rev_mom > 0: score += 10

        # 毛利率 (簡單判斷 > 20% 為優)
        if current_gm > 20: score += 10
        
        # 訊號判定
        if score >= 70:
            signal = "財報強勢 A"
            verdict = "基本面強勁，成長動能高"
        elif score >= 50:
            signal = "財報穩健 B"
            verdict = "獲利穩定，表現持平"
        elif score >= 30:
            signal = "財報偏弱 C"
            verdict = "成長趨緩，需留意轉機"
        else:
            signal = "財報危險 D"
            verdict = "獲利衰退，基本面轉弱"

        # 取得本益比資訊
        pe_info_str = "N/A"
        cat_pe_str = "N/A"
        try:
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
            from data_loader import get_stock_and_category_pe
            if stock_code:
                stock_pe, cat_avg_pe, cat_name = get_stock_and_category_pe(stock_code)
                if stock_pe > 0:
                    pe_info_str = f"{round(stock_pe, 2)} 倍"
                if cat_avg_pe > 0:
                    cat_pe_str = f"{round(cat_avg_pe, 2)} 倍 ({cat_name})"
        except Exception as e:
            print(f"Fetch PE error: {e}")

        # 整理數值
        vals = {
            '最新 EPS': round(current_eps, 2),
            '去年 EPS': f"{eps_ly} 元" if eps_ly != "N/A" else "N/A",
            '前年 EPS': f"{eps_py} 元" if eps_py != "N/A" else "N/A",
            'EPS 季增率': f"{round(eps_growth, 2)}%",
            '近四季 EPS (TTM)': round(ttm_eps, 2) if 'ttm_eps' in locals() else "N/A",
            '個股本益比 (PE)': pe_info_str,
            '類股平均本益比': cat_pe_str,
            '最新毛利率': f"{round(current_gm, 2)}%",
            '單月營收(億)': round(current_revenue, 2),
            '營收月增率 (MoM)': f"{round(rev_mom, 2)}%",
            '營收年增率 (YoY)': f"{round(rev_yoy, 2)}%",
            '綜合評分': score
        }
        
        return {
            'title': '季度財報 & 月營收分析',
            'signal': signal,
            'desc': f"{verdict}。({', '.join(reasons)})",
            'vals': vals
        }

    except Exception as e:
        return {
            'title': '分析錯誤',
            'signal': 'ERROR',
            'desc': f"數據解析失敗: {str(e)}",
            'vals': {}
        }