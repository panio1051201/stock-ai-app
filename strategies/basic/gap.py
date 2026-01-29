import pandas as pd

def analyze(df, stock_code=None):
    """
    Role: 缺口分析師
    Task: 找出未回補的跳空缺口 (Gap)
    """
    if df is None or df.empty:
        return {'title': '缺口分析', 'signal': '無數據', 'desc': '', 'vals': {}}

    try:
        # 找近 120 天
        data = df.tail(120).copy()
        data['Prev_High'] = data['High'].shift(1)
        data['Prev_Low'] = data['Low'].shift(1)
        
        gaps = []
        
        # 掃描缺口
        for i in range(1, len(data)):
            curr = data.iloc[i]
            prev = data.iloc[i-1]
            date_str = data.index[i].strftime('%Y-%m-%d')
            
            # 向上跳空 (由下往上)
            if curr['Low'] > prev['High']:
                gap_size = (curr['Low'] - prev['High']) / prev['High'] * 100
                if gap_size > 0.5: # 過濾太小的
                    gaps.append({
                        'date': date_str,
                        'type': '向上跳空 (支撐)',
                        'price': f"{prev['High']:.2f} ~ {curr['Low']:.2f}",
                        'filled': False
                    })
            
            # 向下跳空 (由上往下)
            elif curr['High'] < prev['Low']:
                gap_size = (prev['Low'] - curr['High']) / prev['Low'] * 100
                if gap_size > 0.5:
                    gaps.append({
                        'date': date_str,
                        'type': '向下跳空 (壓力)',
                        'price': f"{curr['High']:.2f} ~ {prev['Low']:.2f}",
                        'filled': False
                    })
        
        # 簡單回補判斷 (簡化版：只列出最近 3 個)
        gaps.reverse() # 讓最新的在前面
        recent_gaps = gaps[:4]
        
        if not recent_gaps:
            return {'title': '缺口分析', 'signal': '無明顯缺口', 'desc': '近期股價走勢連續，無跳空。', 'vals': {}}

        vals = {}
        vals['現價'] = f"{df['Close'].iloc[-1]}"
        
        idx = 1
        last_type = "無"
        for g in recent_gaps:
            icon = "🟢" if "向上" in g['type'] else "🔴"
            vals[f"缺口 {idx}"] = f"{g['date']} | {icon} {g['type']} | {g['price']}"
            if idx == 1: last_type = g['type']
            idx += 1
            
        signal = "留意缺口"
        if "向上" in last_type: signal = "多方缺口支撐"
        if "向下" in last_type: signal = "空方缺口壓力"

        return {
            'title': '跳空缺口分析',
            'signal': signal,
            'desc': f"偵測到近期有 {len(recent_gaps)} 個未回補缺口。",
            'vals': vals
        }

    except Exception as e:
        return {'title': '分析錯誤', 'signal': 'ERROR', 'desc': str(e), 'vals': {}}