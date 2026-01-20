import sys, logging
import datetime
import os
from datetime import timedelta
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import data_loader

# ==========================================
# 1. 引入所有策略模組
# ==========================================
from strategies.basic import ma, kd, rsi, macd, box, regression, value, financial, chips
from strategies.advanced import kd_rsi, ma_macd, macd_rsi, summary, find_demon

app = Flask(__name__)
CORS(app)

# ==========================================
# 2. 會員與權限設定
# ==========================================
ADMIN_KEYS = ["RAY_ADMIN_888", "BOSS_001"]
VIP_KEYS = ["VIP_USER_001", "FRIEND_JOY", "2026_PRO", "VIP_TEST"]
LIMIT_COUNT = 5
LIMIT_HOURS = 3
USAGE_DB = {}

# 註冊策略路由表
STRATEGIES = {
    'MA': ma, 'KD': kd, 'RSI': rsi, 'MACD': macd, 'BOX': box, 'REG': regression, 
    'VALUE': value, 'FINANCIAL': financial, 'CHIPS': chips,
    'KDRSI': kd_rsi, 'MAKD': ma_macd, 'MACDRSI': macd_rsi, 
    'SUMMARY': summary, 'DEMON': find_demon
}

def check_permission(ip, access_code, st_type):
    now = datetime.datetime.now()
    code_input = str(access_code).strip()
    is_admin = code_input in ADMIN_KEYS
    is_vip = code_input in VIP_KEYS
    
    # 妖股獵手限制
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
        return False, f"⚠️ 免費額度 ({LIMIT_COUNT}次) 已用完！請於 {record['reset_time'].strftime('%H:%M')} 後再來，或輸入 VIP 通行碼。"
    
    return True, ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_single():
    data = request.json
    code = data.get('code')
    st_type = data.get('type')
    buy_price_input = data.get('buy_price')
    access_code = data.get('access_code', '')
    
    user_ip = request.remote_addr

    # 1. 權限檢查
    passed, msg = check_permission(user_ip, access_code, st_type)
    if not passed: return jsonify({'error': msg})

    # 2. 計數器增加 (訪客)
    if access_code not in ADMIN_KEYS and access_code not in VIP_KEYS:
        USAGE_DB[user_ip]['count'] += 1
        used = USAGE_DB[user_ip]['count']
        print(f"[Access] IP:{user_ip} 使用第 {used}/{LIMIT_COUNT} 次")

    if st_type != 'DEMON' and not code: 
        return jsonify({'error': '請輸入股票代碼或名稱'})
    
    df = None
    fin_data = None
    chip_data = None
    price = 0
    name = "全市場掃描"
    full_code = "ALL"

    # 3. 資料抓取與分流
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
                # ★ 綜合診斷：三種資料全都要！
                print(f"[Summary] 正在為 {name} 準備全方位資料...")
                df, price = data_loader.fetch_data(full_code)
                fin_data = data_loader.fetch_financials(full_code)
                chip_data = data_loader.fetch_institutional_investors(full_code)
            
            else:
                # 一般技術分析
                df, price = data_loader.fetch_data(full_code)
                if df.empty: return jsonify({'error': f'查無 {name} ({full_code}) 的資料'})
                
        except Exception as e:
            print(f"[Data Error] {e}")
            return jsonify({'error': '資料抓取失敗'})
    
    module = STRATEGIES.get(st_type)
    if not module: return jsonify({'error': '策略未找到'})
    
    try:
        # 4. 策略執行分流
        if st_type == 'DEMON':
            result = module.analyze(None, None)
        elif st_type == 'FINANCIAL':
            result = module.analyze(fin_data, stock_code=full_code)
        elif st_type == 'CHIPS':
            result = module.analyze(chip_data, stock_code=full_code)
        elif st_type == 'SUMMARY':
            # ★ 傳入所有資料給 Summary
            result = module.analyze(df, stock_code=full_code, fin_data=fin_data, chip_data=chip_data)
        elif st_type == 'VALUE':
            result = module.analyze(df, stock_code=full_code)
        else:
            result = module.analyze(df)
            
        if not result: raise ValueError("策略回傳空值")

        # 5. AI 損益建議
        if st_type != 'DEMON' and buy_price_input and str(buy_price_input).strip() != "":
            try:
                buy_price = float(buy_price_input)
                if buy_price > 0:
                    current_price = price
                    roi = (current_price - buy_price) / buy_price * 100
                    roi_str = f"{roi:+.2f}%"
                    sig = result['signal']
                    is_bullish = any(x in sig for x in ["買", "多", "A", "B", "強", "成長", "穩健", "低估", "大好"])
                    is_bearish = any(x in sig for x in ["賣", "空", "D", "E", "弱", "衰退", "危險", "高估", "渙散"])
                    advice = ""
                    if roi >= 10: advice = "🚀 獲利豐厚，建議續抱！" if is_bullish else "💰 訊號轉弱，建議獲利了結。"
                    elif roi >= 0: advice = "📈 獲利中，耐心持有。" if is_bullish else "⚠️ 建議先賣出保本。"
                    elif roi >= -10: advice = "📉 雖小賠但訊號轉強，續抱。" if is_bullish else "💔 建議停損換股。"
                    else: advice = "📉 暫勿殺低，等待反彈。" if is_bullish else "🩸 深套請評估停損。"
                    new_vals = {'--- 持倉分析 ---': '---', '您的成本': buy_price, '目前損益': roi_str, '💡 操作建議': advice}
                    new_vals.update(result['vals'])
                    result['vals'] = new_vals
            except ValueError: pass

    except Exception as e:
        print(f"[Analyze Error] {e}")
        return jsonify({'error': str(e)})
    
    response = {'success': True, 'info': {'code': full_code, 'name': name, 'price': price}, 'result': result, 'chart': None}
    
    # 綜合診斷也要顯示 K 線圖
    if st_type == 'SUMMARY' or (st_type not in ['DEMON', 'FINANCIAL', 'CHIPS'] and df is not None):
        response['chart'] = {'dates': df.index.strftime('%Y-%m-%d').tolist(), 'prices': df['Close'].tolist()}
        
    return jsonify(response)

# ==========================================
# 6. 啟動設定 (支援 Render/Heroku 雲端環境)
# ==========================================
if __name__ == '__main__':
    print("AI 全端金融戰情室 (SaaS Cloud Ver.) 啟動中...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)