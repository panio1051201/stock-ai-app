import pandas as pd
import numpy as np
import datetime

def analyze(df):
    try:
        if df.empty or len(df) < 20:
            return {"error": "資料不足，無法計算布林通道 (需至少 20 天資料)", "signal": "N/A", "desc": "N/A", "chart_data": {}}
        
        # 計算布林通道 (20MA, ±2 標準差)
        period = 20
        df['middle_band'] = df['Close'].rolling(window=period).mean()
        df['std_dev'] = df['Close'].rolling(window=period).std()
        df['upper_band'] = df['middle_band'] + (df['std_dev'] * 2)
        df['lower_band'] = df['middle_band'] - (df['std_dev'] * 2)
        
        # 移除 NaN 以確保圖表整潔
        valid_df = df.dropna(subset=['middle_band', 'upper_band', 'lower_band']).copy()
        if valid_df.empty:
            return {"error": "資料不足，無法計算布林通道", "signal": "N/A", "desc": "N/A"}

        # 將時間索引轉換回字串供 JSON 序列化
        valid_df['Date_str'] = valid_df.index.strftime('%Y-%m-%d')
        dates = valid_df['Date_str'].tolist()
        prices = valid_df['Close'].tolist()
        upper = valid_df['upper_band'].tolist()
        middle = valid_df['middle_band'].tolist()
        lower = valid_df['lower_band'].tolist()

        # 分析最後一天的狀態
        latest = valid_df.iloc[-1]
        prev = valid_df.iloc[-2] if len(valid_df) > 1 else latest
        curr_price = latest['Close']
        curr_upper = latest['upper_band']
        curr_lower = latest['lower_band']

        signal = "持股觀望 (Neutral)"
        desc = f"股價在布林通道內波動。(目前股價: {curr_price:.2f}, 通道上軌: {curr_upper:.2f}, 下軌: {curr_lower:.2f})"

        # 基礎判斷邏輯
        if curr_price < curr_lower:
            signal = "超賣買進 (Buy) - 跌破下軌"
            desc = f"股價跌破布林下軌 ({curr_lower:.2f})，可能出現短期超賣反彈機會。"
        elif curr_price > curr_upper:
            signal = "超買賣出 (Sell) - 突破上軌"
            desc = f"股價突破布林上軌 ({curr_upper:.2f})，顯示短期超買，需注意回檔風險。"
        elif prev['Close'] < prev['lower_band'] and curr_price > curr_lower:
             signal = "轉強買進 (Buy) - 回收下軌"
             desc = f"股價剛從布林下軌下方收升回通道內，暗示超賣反轉力道出現。"

        return {
            "signal": signal,
            "desc": desc,
            "chart_data": {
                "title": "布林通道 (BOLLINGER)",
                "dates": dates,
                "prices": prices,
                "lines": [
                    {"label": "Upper Band", "data": upper, "color": "rgba(255, 69, 58, 0.6)"},
                    {"label": "20 MA", "data": middle, "color": "rgba(255, 214, 10, 0.6)"},
                    {"label": "Lower Band", "data": lower, "color": "rgba(48, 209, 88, 0.6)"}
                ]
            }
        }
    except Exception as e:
        return {"error": f"布林通道計算錯誤: {str(e)}", "signal": "Error", "desc": str(e)}
