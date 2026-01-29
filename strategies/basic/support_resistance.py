import pandas as pd
import numpy as np

def analyze(df, stock_code=None):
    """
    Role: 關鍵價位分析師 (Pro Ver.)
    Task: 整合均線、波段高低點、斐波那契，產生排序後的支撐壓力列表
    Output: 給前端渲染成紅綠列表的格式
    """
    if df is None or df.empty:
        return {'title': '支撐壓力', 'signal': '無數據', 'desc': '', 'vals': {}}

    try:
        close = df['Close'].iloc[-1]
        
        # 1. 收集所有關鍵價位
        levels = []
        
        # A. 均線 (MA)
        ma_days = [5, 10, 20, 60]
        for d in ma_days:
            ma_val = df['Close'].rolling(d).mean().iloc[-1]
            if not np.isnan(ma_val):
                levels.append({'price': ma_val, 'source': f'MA{d}'})
        
        # B. 波段高低點 (近 60 日)
        recent = df.tail(60)
        high_60 = recent['High'].max()
        low_60 = recent['Low'].min()
        levels.append({'price': high_60, 'source': '60日高點'})
        levels.append({'price': low_60, 'source': '60日低點'})
        
        # C. 斐波那契 (Fibonacci)
        diff = high_60 - low_60
        fibs = [0.236, 0.382, 0.5, 0.618]
        for f in fibs:
            p = high_60 - diff * f
            levels.append({'price': p, 'source': f'Fib {f*100:.1f}%'})

        # 2. 處理數據：排序、去重、判斷類型
        # 先去除價格太接近的 (誤差 0.5% 內視為同一條線)
        unique_levels = []
        levels.sort(key=lambda x: x['price'], reverse=True) # 由大到小排序
        
        for l in levels:
            if not unique_levels:
                unique_levels.append(l)
            else:
                last = unique_levels[-1]
                if abs(last['price'] - l['price']) / last['price'] > 0.005:
                    unique_levels.append(l)
                else:
                    # 如果重疊，合併名稱 (例如 MA60 + Fib 0.5)
                    last['source'] += f" / {l['source']}"

        # 3. 產生結果字典 (格式：Price | Type | Gap% | Source)
        # 為了讓前端依序顯示，我們用 Level_01, Level_02 當 Key
        result_vals = {}
        
        # 插入現價 (作為分隔線概念，雖然前端可能不顯示這行，但用來定位)
        # result_vals['現價'] = f"{close}|Current|0.00%|目前價格"
        
        idx = 1
        for item in unique_levels:
            p = item['price']
            src = item['source']
            gap = (p - close) / close * 100
            
            # 判斷是支撐還是壓力
            if p > close:
                l_type = "壓力"
            else:
                l_type = "支撐"
                
            # 格式化: "價格|類型|漲跌幅|說明"
            key_name = f"L_{idx:02d}" # L_01, L_02... 確保排序
            val_str = f"{p:.2f}|{l_type}|{gap:+.2f}%|{src}"
            result_vals[key_name] = val_str
            idx += 1

        # 訊號判斷
        signal = "區間震盪"
        desc = "股價位於支撐與壓力之間"
        
        # 找最近的壓力與支撐
        res_list = [l for l in unique_levels if l['price'] > close]
        sup_list = [l for l in unique_levels if l['price'] < close]
        
        if res_list and (res_list[-1]['price'] - close)/close < 0.01:
            signal = "挑戰壓力"
            desc = f"即將挑戰 {res_list[-1]['source']} ({res_list[-1]['price']:.2f})"
        elif sup_list and (close - sup_list[0]['price'])/close < 0.01:
            signal = "回測支撐"
            desc = f"回測 {sup_list[0]['source']} ({sup_list[0]['price']:.2f})"

        return {
            'title': '關鍵支撐壓力',
            'signal': signal,
            'desc': desc,
            'vals': result_vals
        }

    except Exception as e:
        return {'title': '分析錯誤', 'signal': 'ERROR', 'desc': str(e), 'vals': {}}