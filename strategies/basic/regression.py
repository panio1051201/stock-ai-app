import pandas as pd
import numpy as np

def analyze(df):
    """
    策略核心：高斯 (線性回歸趨勢) + 台灣軌道派 (標準差通道)
    
    邏輯：
    1. 中心線 (Regression Line)：代表股價的「真實價值」與「方向」。
    2. 上軌 (+2SD)：代表「超買壓力區」。
    3. 下軌 (-2SD)：代表「超賣支撐區」。
    
    操作心法：
    - 多頭趨勢 (斜率向上)：回測下軌買進，碰到上軌獲利。
    - 空頭趨勢 (斜率向下)：反彈上軌賣出，碰到下軌回補。
    """
    try:
        # 設定週期 (20日，約一個月)
        days = 20
        if len(df) < days: return None
        
        # 取得最近 N 天的收盤價
        y = df['Close'].tail(days).values
        x = np.arange(days)
        
        # 1. 計算線性回歸 (利用高斯的最小平方法)
        # polyfit 回傳兩個值：slope (斜率), intercept (截距)
        slope, intercept = np.polyfit(x, y, 1)
        
        # 計算回歸線上的每一個點 (理論價)
        reg_line = slope * x + intercept
        current_reg_price = reg_line[-1] # 最新的理論價
        
        # 2. 計算標準差通道 (台灣軌道派心法)
        # 計算殘差 (真實價 - 理論價) 的標準差
        residuals = y - reg_line
        std_dev = np.std(residuals)
        
        # 定義上下軌 (通常用 2 倍標準差)
        upper_rail = current_reg_price + (2 * std_dev)
        lower_rail = current_reg_price - (2 * std_dev)
        
        current_price = y[-1]
        
        # 3. 判斷訊號
        sig = "觀望"
        desc = f"斜率 {round(slope, 2)}，股價在通道內"
        
        # --- 判斷趨勢方向 (看斜率) ---
        if slope > 0.1: # 斜率向上 (多頭)
            trend = "多頭趨勢"
            
            # 多頭操作：買低 (碰到下軌)
            if current_price <= lower_rail * 1.01: # 接近下軌 1%
                sig = "買進 (回測下軌)"
                desc = "回歸心法：多頭趨勢回測支撐 (價值浮現)"
            
            # 多頭操作：賣高 (碰到上軌)
            elif current_price >= upper_rail * 0.99:
                sig = "賣出 (觸碰上軌)"
                desc = "高爾頓：正乖離過大，將回歸平均 (獲利點)"
                
        elif slope < -0.1: # 斜率向下 (空頭)
            trend = "空頭趨勢"
            
            # 空頭操作：空高 (碰到上軌)
            if current_price >= upper_rail * 0.99:
                sig = "賣出 (壓力測試)"
                desc = "空頭趨勢反彈至壓力區"
            
            # 空頭操作：補低 (碰到下軌)
            elif current_price <= lower_rail * 1.01:
                sig = "回補 (觸碰下軌)"
                desc = "負乖離過大，隨時反彈"
                
        else:
            trend = "盤整趨勢"
            desc = "斜率走平，區間震盪"

        return {
            'title': '線性回歸通道 (Regression Channel)',
            'signal': sig,
            'desc': f"{trend}。{desc}",
            'vals': {
                '斜率 (趨勢)': round(slope, 3),
                '現價': round(current_price, 2),
                '上軌 (壓力)': round(upper_rail, 2),
                '中軌 (價值)': round(current_reg_price, 2),
                '下軌 (支撐)': round(lower_rail, 2)
            }
        }

    except Exception as e:
        print(f"[Reg Error] {e}")
        return {
            'title': '回歸分析錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {'斜率': 0}
        }