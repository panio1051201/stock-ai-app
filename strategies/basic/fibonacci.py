import pandas as pd

def analyze(df, stock_code=None):
    """
    Role: 技術分析師 - 斐波那契 (Fibonacci)
    Task: 計算波段高低點與黃金分割率回撤位
    """
    if df is None or df.empty:
        return {'title': '斐波那契分析', 'signal': '無數據', 'desc': '無法取得股價資料', 'vals': {}}

    try:
        # 設定波段區間 (例如近半年 120 天)
        lookback = 120
        recent_df = df.tail(lookback)
        
        # 找波段高低點
        high_price = recent_df['High'].max()
        low_price = recent_df['Low'].min()
        current_price = df['Close'].iloc[-1]
        
        diff = high_price - low_price
        
        # 計算黃金分割位
        level_0 = high_price
        level_236 = high_price - 0.236 * diff
        level_382 = high_price - 0.382 * diff
        level_500 = high_price - 0.5 * diff
        level_618 = high_price - 0.618 * diff
        level_100 = low_price
        
        # 判斷目前位置
        status = "區間震盪"
        dist_to_support = 0
        
        if current_price > level_236:
            status = "強勢高檔"
            signal = "看多"
        elif current_price < level_618:
            status = "回檔深"
            signal = "尋找支撐"
            # 接近 0.618 是強力支撐
            if abs(current_price - level_618) / current_price < 0.02:
                signal = "0.618 黃金支撐買點"
        else:
            status = "中繼整理"
            signal = "觀望"

        desc = f"波段高點 {high_price}，低點 {low_price}。目前位於 {status} 區域。"

        return {
            'title': '斐波那契回撤 (Fibonacci)',
            'signal': signal,
            'desc': desc,
            'vals': {
                '🌊 波段高點 (0%)': f"{high_price}",
                '🌊 波段低點 (100%)': f"{low_price}",
                '🔸 0.382 壓力': f"{level_382:.2f}",
                '🔹 0.5 中關': f"{level_500:.2f}",
                '⭐ 0.618 強支撐': f"{level_618:.2f}",
                '現價位置': f"{current_price}"
            }
        }

    except Exception as e:
        return {'title': '分析錯誤', 'signal': 'ERROR', 'desc': str(e), 'vals': {}}