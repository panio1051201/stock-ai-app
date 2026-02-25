import pandas as pd
import numpy as np

def calculate_qqe(df, rsi_period=14, smoothing=5, multiplier=4.236):
    """
    QQE (Quantitative Qualitative Estimation) 核心演算法
    回傳: RSI_MA, Long_Band, Short_Band, Trend
    """
    try:
        close = df['Close']
        if len(close) < rsi_period * 2:
            return pd.Series([50.0]*len(df)), pd.Series([50.0]*len(df)), pd.Series([0]*len(df))

        # 1. 計算 RSI
        delta = close.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=rsi_period-1, adjust=False).mean()
        ema_down = down.ewm(com=rsi_period-1, adjust=False).mean()
        rs = ema_up / (ema_down + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # 2. RSI 平滑化 (RSI MA)
        rsi_ma = rsi.ewm(span=smoothing, adjust=False).mean()
        
        # 3. 計算 RSI 的 ATR (使用 27 週期雙重平滑)
        rsi_diff = rsi_ma.diff().abs()
        # Wilder's Smoothing com=N-1
        atr_rsi = rsi_diff.ewm(com=27-1, adjust=False).mean()
        dar = atr_rsi.ewm(com=27-1, adjust=False).mean() * multiplier
        
        # 4. Trailing Band 計算
        # 初始化
        band = np.zeros(len(df))
        trend = np.zeros(len(df)) # 1: 多頭, -1: 空頭
        
        curr_band = rsi_ma.iloc[0]
        curr_trend = 1
        
        for i in range(1, len(df)):
            prev_rsi_ma = rsi_ma.iloc[i-1]
            curr_rsi_ma = rsi_ma.iloc[i]
            
            # 判斷趨勢反轉
            if curr_trend == 1:
                if curr_rsi_ma < curr_band:
                    curr_trend = -1
                    curr_band = curr_rsi_ma + dar.iloc[i]
                else:
                    # 多頭帶隨價格上升，但不下降 (Trailing)
                    new_band = curr_rsi_ma - dar.iloc[i]
                    if prev_rsi_ma > curr_band:
                        curr_band = max(curr_band, new_band)
                    else:
                        curr_band = new_band
            else:
                if curr_rsi_ma > curr_band:
                    curr_trend = 1
                    curr_band = curr_rsi_ma - dar.iloc[i]
                else:
                    # 空頭帶隨價格下降，但不上升
                    new_band = curr_rsi_ma + dar.iloc[i]
                    if prev_rsi_ma < curr_band:
                        curr_band = min(curr_band, new_band)
                    else:
                        curr_band = new_band
            
            band[i] = curr_band
            trend[i] = curr_trend
            
        return rsi_ma, pd.Series(band, index=df.index), pd.Series(trend, index=df.index)
    except Exception as e:
        print(f"[QQE Calc Error] {e}")
        return pd.Series([50.0]*len(df)), pd.Series([50.0]*len(df)), pd.Series([0]*len(df))

def analyze(df):
    """
    符合系統規範的 QQE 策略入口 
    """
    try:
        rsi_ma, band, trend = calculate_qqe(df)
        
        last_rsi_ma = round(rsi_ma.iloc[-1], 2)
        last_trend = trend.iloc[-1]
        
        # 訊號判斷
        signal = "多方趨勢" if last_trend == 1 else "空方趨勢"
        desc = "指標位於帶狀線之上，動能偏多" if last_trend == 1 else "指標跌破帶狀線，動能偏空"
        
        # 偵測交叉點
        if len(trend) >= 2:
            if trend.iloc[-1] == 1 and trend.iloc[-2] == -1:
                signal = "買進 (QQE 黃金交叉)"
                desc = "QQE 指標由下往上翻多，強烈買進訊號"
            elif trend.iloc[-1] == -1 and trend.iloc[-2] == 1:
                signal = "賣出 (QQE 死亡交叉)"
                desc = "QQE 指標由上往下翻空，建議減碼或避險"

        return {
            'title': 'QQE 量化定性估算指標',
            'signal': signal,
            'desc': desc,
            'vals': {
                'QQE RSI-MA': last_rsi_ma,
                '當前趨勢': "看多" if last_trend == 1 else "看空",
                'OSC 分值': round(last_rsi_ma - 50, 2)
            }
        }
    except Exception as e:
        return {
            'title': 'QQE 分析錯誤',
            'signal': 'ERROR',
            'desc': str(e),
            'vals': {}
        }
