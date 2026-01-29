import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

def analyze(df, stock_code=None):
    """
    Role: 型態辨識專家
    Task: 偵測 W底 (雙重底) 或 M頭 (雙重頂)
    """
    if df is None or df.empty:
        return {'title': '型態辨識', 'signal': '無數據', 'desc': '', 'vals': {}}

    try:
        # 取近 60 天數據
        close = df['Close'].values
        dates = df.index
        
        # 找局部高低點 (Local Max/Min)
        # order=5 代表前後 5 天都是最高/最低才算
        local_max_idx = argrelextrema(close, np.greater, order=5)[0]
        local_min_idx = argrelextrema(close, np.less, order=5)[0]
        
        local_max = close[local_max_idx]
        local_min = close[local_min_idx]
        
        vals = {}
        signal = "盤整無型態"
        desc = "未偵測到明顯 W底 或 M頭"
        
        # --- 判斷 W 底 (雙重底) ---
        # 邏輯：最近有兩個低點，價格接近 (誤差 3% 內)，且中間有個高點
        if len(local_min) >= 2:
            min1 = local_min[-2]
            min2 = local_min[-1]
            idx1 = local_min_idx[-2]
            idx2 = local_min_idx[-1]
            
            # 兩個低點夠近嗎？
            if abs(min1 - min2) / min1 < 0.03:
                # 檢查中間有沒有高點 (頸線)
                neck_candidates = [x for x in local_max if idx1 < np.where(close==x)[0][0] < idx2]
                # 注意：這裡簡化處理，直接檢查中間的最高價
                mid_slice = close[idx1:idx2]
                neck_price = mid_slice.max()
                
                current_price = close[-1]
                
                if current_price > neck_price:
                    signal = "W底 (突破頸線)"
                    desc = "W型態完成，突破頸線，強勢看多。"
                else:
                    signal = "W底 (成形中)"
                    desc = "右腳成形，尚未突破頸線。"
                    
                vals['型態'] = "W底 (Double Bottom)"
                vals['左腳低點'] = f"{min1}"
                vals['右腳低點'] = f"{min2}"
                vals['頸線壓力'] = f"{neck_price}"

        # --- 判斷 M 頭 (雙重頂) ---
        # 邏輯：最近有兩個高點，價格接近
        if len(local_max) >= 2 and signal == "盤整無型態":
            max1 = local_max[-2]
            max2 = local_max[-1]
            
            if abs(max1 - max2) / max1 < 0.03:
                signal = "M頭 (成形中)"
                desc = "高檔出現雙重頂，留意回檔風險。"
                
                vals['型態'] = "M頭 (Double Top)"
                vals['左頭高點'] = f"{max1}"
                vals['右頭高點'] = f"{max2}"

        vals['現價'] = f"{close[-1]}"

        return {
            'title': 'AI 型態辨識',
            'signal': signal,
            'desc': desc,
            'vals': vals
        }

    except Exception as e:
        # 如果 scipy 沒裝或是數據不足
        return {'title': '型態分析', 'signal': '數據不足', 'desc': '需要更多交易日資料', 'vals': {}}