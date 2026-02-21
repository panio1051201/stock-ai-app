import sys
import os
import logging
import datetime
import csv
import io
import pandas as pd
from datetime import timedelta
from flask import Flask, jsonify, render_template, request, Response
from flask_cors import CORS
import data_loader

sys.path.append(os.getcwd())

# ==========================================
# 1. 引入所有策略模組
# ==========================================
from strategies.basic import ma, kd, rsi, macd, box, regression, value, financial, chips, fibonacci, support_resistance, gap, pattern
from strategies.advanced import kd_rsi, ma_macd, macd_rsi, summary, find_demon

app = Flask(__name__)
CORS(app)

# ==========================================
# 2. 全局設定
# ==========================================
ADMIN_KEYS = ["RAY_ADMIN_888", "BOSS_001"]
VIP_KEYS = ["VIP_USER_001", "FRIEND_JOY", "2026_PRO", "VIP_TEST"]

# 免費額度: 25 次 / 1 小時
LIMIT_COUNT = 25
LIMIT_HOURS = 1

# 資料庫
USAGE_DB = {}   # 用戶流量限制
STATS_DB = {}   # 訪客停留時間統計
ACCESS_LOG = [] # 詳細操作日誌 (匯出用)

# 策略對應表
STRATEGIES = {
    'MA': ma, 'KD': kd, 'RSI': rsi, 'MACD': macd, 'BOX': box, 'REG': regression, 
    'VALUE': value, 'FINANCIAL': financial, 'CHIPS': chips, 
    'FIB': fibonacci, 'SR': support_resistance,
    'GAP': gap, 'PATTERN': pattern,
    'KDRSI': kd_rsi, 'MAKD': ma_macd, 'MACDRSI': macd_rsi, 
    'SUMMARY': summary, 'DEMON': find_demon
}

# ==========================================
# 3. 核心功能函式
# ==========================================

def track_activity(ip, stock_code, strategy, chip_data=None, margin_data=None):
    """ 記錄用戶行為與數據 (用於匯出報表) """
    now = datetime.datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    # 更新停留時間與次數
    if today not in STATS_DB: STATS_DB[today] = {}
    if ip not in STATS_DB[today]:
        STATS_DB[today][ip] = {'first': now, 'last': now, 'hits': 1}
    else:
        STATS_DB[today][ip]['last'] = now
        STATS_DB[today][ip]['hits'] += 1
    
    # 解析籌碼數據
    inst_net = "N/A"
    margin_bal = "N/A"
    
    try:
        # 三大法人買賣超
        if chip_data is not None and not chip_data.empty:
            cols = ['Foreign_Investor_Net', 'Investment_Trust_Net', 'Dealer_Net']
            valid_cols = [c for c in chip_data.columns if c in cols]
            if valid_cols:
                inst_net = int(chip_data.iloc[-1][valid_cols].sum())
        
        # 融資餘額
        if margin_data is not None and not margin_data.empty:
            tgt_col = 'MarginPurchaseTodayBalance'
            if tgt_col in margin_data.columns:
                margin_bal = int(margin_data.iloc[-1][tgt_col])
    except:
        pass 

    # 寫入日誌
    duration_min = (STATS_DB[today][ip]['last'] - STATS_DB[today][ip]['first']).total_seconds() / 60
    
    log_entry = {
        'Time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'IP': ip,
        'Stock': stock_code,
        'Strategy': strategy,
        'Inst_Net': inst_net,       
        'Margin_Bal': margin_bal,   
        'Visit_Hits': STATS_DB[today][ip]['hits'], 
        'Stay_Time': f"{duration_min:.1f} min"     
    }
    ACCESS_LOG.append(log_entry)
    if len(ACCESS_LOG) > 5000: ACCESS_LOG.pop(0)

def check_permission(ip, access_code, st_type):
    """ 檢查用戶權限 """
    now = datetime.datetime.now()
    code_input = str(access_code).strip()
    is_admin = code_input in ADMIN_KEYS
    is_vip = code_input in VIP_KEYS
    
    if st_type == 'DEMON':
        return (True, "") if is_admin else (False, "⛔ 權限不足：此功能僅限核心管理員使用。")

    if is_admin or is_vip: return True, ""
    
    # 訪客限制
    if ip not in USAGE_DB:
        USAGE_DB[ip] = {'reset_time': now + timedelta(hours=LIMIT_HOURS), 'count': 0}
    else:
        if now > USAGE_DB[ip]['reset_time']:
            USAGE_DB[ip] = {'reset_time': now + timedelta(hours=LIMIT_HOURS), 'count': 0}
            
    record = USAGE_DB[ip]
    if record['count'] >= LIMIT_COUNT:
        return False, f"⚠️ 免費額度 ({LIMIT_COUNT}次/時) 已用完！請於 {record['reset_time'].strftime('%H:%M')} 後再來。"
    
    return True, ""

# ==========================================
# 4. 路由設定
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/retrolyze')
def retrolyze():
    return render_template('retrolyze.html')

@app.route('/api/admin/export', methods=['POST'])
def export_stats():
    data = request.json
    access_code = data.get('access_code', '')
    
    if access_code not in ADMIN_KEYS:
        return jsonify({'error': '權限不足'}), 403

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['時間', '用戶IP', '查詢股票', '使用功能', '法人買賣超', '融資餘額', '今日操作次數', '停留時間'])
    
    for log in reversed(ACCESS_LOG):
        cw.writerow([
            log['Time'], log['IP'], log['Stock'], log['Strategy'], 
            log['Inst_Net'], log['Margin_Bal'], 
            log['Visit_Hits'], log['Stay_Time']
        ])
            
    output = si.getvalue()
    return Response('\ufeff' + output, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=traffic_report.csv"})

@app.route('/api/analyze', methods=['POST'])
def analyze_single():
    data = request.json
    code = data.get('code')
    st_type = data.get('type')
    buy_price_input = data.get('buy_price')
    access_code = data.get('access_code', '')
    user_ip = request.remote_addr

    passed, msg = check_permission(user_ip, access_code, st_type)
    if not passed: return jsonify({'error': msg})

    if access_code not in ADMIN_KEYS and access_code not in VIP_KEYS:
        USAGE_DB[user_ip]['count'] += 1

    if st_type != 'DEMON' and not code: 
        return jsonify({'error': '請輸入股票代碼'})
    
    df, fin_data, chip_data, margin_data, price = None, None, None, None, 0
    name, full_code = "全市場掃描", "ALL"

    # 解析成本價
    buy_price_val = None
    if buy_price_input and str(buy_price_input).strip() != "":
        try:
            buy_price_val = float(buy_price_input)
        except: pass

    if st_type != 'DEMON':
        try:
            name, full_code = data_loader.get_stock_name(code)
            
            if st_type == 'FINANCIAL':
                fin_data = data_loader.fetch_financials(full_code)
                _, price = data_loader.fetch_data(full_code, days=5)
            elif st_type == 'CHIPS':
                chip_data = data_loader.fetch_institutional_investors(full_code)
                _, price = data_loader.fetch_data(full_code, days=5)
            elif st_type == 'SUMMARY':
                df, price = data_loader.fetch_data(full_code)
                fin_data = data_loader.fetch_financials(full_code)
                chip_data = data_loader.fetch_institutional_investors(full_code)
            else:
                df, price = data_loader.fetch_data(full_code)
            
            if st_type in ['SUMMARY', 'CHIPS']:
                try:
                    import FinMind
                    from FinMind.data import DataLoader
                    api = DataLoader()
                    margin_data = api.taiwan_stock_margin_purchase_short_sale(
                        stock_id=full_code,
                        start_date=(datetime.datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
                    )
                except: pass

        except Exception as e:
            return jsonify({'error': '資料抓取失敗'})
    
    track_activity(user_ip, full_code, st_type, chip_data, margin_data)

    module = STRATEGIES.get(st_type)
    if not module: return jsonify({'error': '策略未找到'})
    
    try:
        # ★ 策略執行分流
        if st_type == 'DEMON': 
            result = module.analyze(None, None)
        elif st_type == 'FINANCIAL': 
            result = module.analyze(fin_data, stock_code=full_code)
        elif st_type == 'CHIPS': 
            result = module.analyze(chip_data, stock_code=full_code)
        elif st_type == 'SUMMARY': 
            # ★ 傳入成本價，讓策略自己算加碼/攤平建議
            result = module.analyze(df, stock_code=full_code, fin_data=fin_data, chip_data=chip_data, margin_data=margin_data, buy_price=buy_price_val)
        elif st_type == 'VALUE': 
            result = module.analyze(df, stock_code=full_code)
        else: 
            result = module.analyze(df)
            
        if not result: raise ValueError("策略回傳空值")

        # ★ 後處理：如果是 SUMMARY，它已經自己算過建議了，不需要這裡的通用建議
        # 但如果是其他功能 (如 MA, KD)，我們還是要幫忙算一下簡單的損益
        if st_type != 'SUMMARY' and st_type != 'DEMON' and buy_price_val and buy_price_val > 0:
            roi = (price - buy_price_val) / buy_price_val * 100
            
            # 通用建議 (比較笨，只看漲跌)
            sig = result.get('signal', '')
            is_bullish = any(x in sig for x in ["買", "多", "A", "B", "強", "成長"])
            advice = "獲利續抱" if roi > 0 else "停損觀察"
            if roi < -10: advice = "建議停損"
            if roi > 20: advice = "分批獲利"

            new_vals = {'您的成本': buy_price_val, '目前損益': f"{roi:+.2f}%", '💡 操作建議': advice}
            new_vals.update(result['vals'])
            result['vals'] = new_vals
            
        # 如果是 SUMMARY，我們只負責補上「您的成本」和「目前損益」的顯示 (如果策略沒回傳的話)
        # 但其實 summary.py 已經有根據 roi 給建議了，這裡只要補顯示數值即可
        if st_type == 'SUMMARY' and buy_price_val and buy_price_val > 0:
             if '您的成本' not in result['vals']:
                 roi = (price - buy_price_val) / buy_price_val * 100
                 # 插在最前面
                 temp = {'您的成本': buy_price_val, '目前損益': f"{roi:+.2f}%"}
                 temp.update(result['vals'])
                 result['vals'] = temp

    except Exception as e:
        return jsonify({'error': str(e)})
    
    response = {'success': True, 'info': {'code': full_code, 'name': name, 'price': price}, 'result': result, 'chart': None}
    
    no_chart_list = ['DEMON', 'FINANCIAL', 'CHIPS', 'GAP', 'PATTERN', 'SR']
    if st_type == 'SUMMARY' or (st_type not in no_chart_list and df is not None):
        response['chart'] = {'dates': df.index.strftime('%Y-%m-%d').tolist(), 'prices': df['Close'].tolist()}
        
    return jsonify(response)

if __name__ == '__main__':
    print("AI 全端金融戰情室 (SaaS Cloud Ver.) 啟動中...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)