"""
Price Alert System - 價格警報系統
支援 LINE 推播
"""

import pandas as pd
from datetime import datetime, timedelta
import json
import os
import time
import threading
import data_loader

class PriceAlert:
    """價格警報管理器"""
    
    def __init__(self, alert_file='price_alerts.json'):
        self.alert_file = alert_file
        self.alerts = self.load()
        self.triggered = []  # 已觸發的警報
    
    def load(self):
        """載入警報"""
        if os.path.exists(self.alert_file):
            try:
                with open(self.alert_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save(self):
        """儲存警報"""
        try:
            with open(self.alert_file, 'w', encoding='utf-8') as f:
                json.dump(self.alerts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存失敗: {e}")
    
    def add_alert(self, code, name, target_price, condition='above', note=''):
        """
        新增價格警報
        
        Args:
            code: 股票代碼
            name: 股票名稱
            target_price: 目標價格
            condition: 'above' (高於) / 'below' (低於)
            note: 備註
        """
        alert = {
            'id': f"{code}_{int(time.time())}",
            'code': code,
            'name': name,
            'target_price': float(target_price),
            'condition': condition,  # 'above' or 'below'
            'note': note,
            'created_at': datetime.now().isoformat(),
            'triggered': False,
            'triggered_at': None
        }
        
        self.alerts.append(alert)
        self.save()
        
        return alert['id']
    
    def remove_alert(self, alert_id):
        """移除警報"""
        self.alerts = [a for a in self.alerts if a['id'] != alert_id]
        self.save()
        return True
    
    def check_alerts(self, prices=None):
        """
        檢查所有警報
        
        Args:
            prices: dict of {code: price}
        
        Returns:
            list of triggered alerts
        """
        if prices is None:
            prices = {}
        
        triggered = []
        
        for alert in self.alerts:
            if alert.get('triggered'):
                continue
            
            code = alert['code']
            target = alert['target_price']
            condition = alert['condition']
            
            # 取得現價
            current_price = prices.get(code)
            if current_price is None:
                try:
                    _, full_code = data_loader.get_stock_name(code)
                    df, current_price = data_loader.fetch_data(full_code, days=5)
                    if current_price:
                        prices[code] = current_price
                except:
                    continue
            
            if current_price is None:
                continue
            
            # 檢查是否觸發
            should_trigger = False
            
            if condition == 'above' and current_price >= target:
                should_trigger = True
            elif condition == 'below' and current_price <= target:
                should_trigger = True
            
            if should_trigger:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now().isoformat()
                alert['current_price'] = current_price
                
                triggered.append(alert)
        
        if triggered:
            self.save()
        
        return triggered
    
    def get_alerts(self, code=None, active_only=False):
        """取得警報列表"""
        alerts = self.alerts
        
        if code:
            alerts = [a for a in alerts if a['code'] == code]
        
        if active_only:
            alerts = [a for a in alerts if not a.get('triggered')]
        
        return alerts
    
    def format_alert_message(self, alert):
        """格式化警報訊息"""
        code = alert['code']
        name = alert.get('name', code)
        target = alert['target_price']
        current = alert.get('current_price', 'N/A')
        condition = '⬆️ 突破' if alert['condition'] == 'above' else '⬇️ 跌破'
        note = alert.get('note', '')
        
        return f"""
{condition} {name} ({code})

目標價: ${target}
現價: ${current}

{note}
        
⏰ {datetime.now().strftime('%H:%M:%S')}
"""

    def send_line_notify(self, message, token=None):
        """
        發送 LINE 通知
        
        Args:
            message: 訊息內容
            token: LINE Notify Token
        """
        if not token:
            # 嘗試從檔案讀取
            try:
                with open('line_token.txt', 'r') as f:
                    token = f.read().strip()
            except:
                print("未設定 LINE Token")
                return False
        
        try:
            import requests
            url = 'https://notify-api.line.me/api/notify'
            headers = {'Authorization': f'Bearer {token}'}
            data = {'message': message}
            
            response = requests.post(url, headers=headers, data=data)
            return response.status_code == 200
            
        except Exception as e:
            print(f"LINE 發送失敗: {e}")
            return False


class AlertChecker:
    """警報檢查器（背景執行）"""
    
    def __init__(self, interval=60):
        self.interval = interval  # 檢查間隔（秒）
        self.running = False
        self.thread = None
        self.alert = PriceAlert()
        self.line_token = None
    
    def start(self, line_token=None):
        """啟動檢查"""
        if self.running:
            return
        
        self.running = True
        self.line_token = line_token
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"價格警報檢查器已啟動 ({self.interval}秒間隔)")
    
    def stop(self):
        """停止檢查"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("價格警報檢查器已停止")
    
    def _run(self):
        """背景執行"""
        while self.running:
            try:
                # 檢查警報
                triggered = self.alert.check_alerts()
                
                # 發送通知
                for alert in triggered:
                    msg = self.alert.format_alert_message(alert)
                    print(msg)
                    
                    if self.line_token:
                        self.alert.send_line_notify(msg, self.line_token)
                
                if triggered:
                    print(f"已觸發 {len(triggered)} 個警報")
            
            except Exception as e:
                print(f"檢查錯誤: {e}")
            
            # 等待下次檢查
            time.sleep(self.interval)


# 快捷函式
def add_alert(code, target, condition='above'):
    """快速新增警報"""
    import data_loader
    name, _ = data_loader.get_stock_name(code)
    
    alert = PriceAlert()
    alert_id = alert.add_alert(code, name, target, condition)
    print(f"已新增警報: {code} {name} {condition} ${target}")
    return alert_id

def remove_alert(alert_id):
    """移除警報"""
    alert = PriceAlert()
    alert.remove_alert(alert_id)
    print(f"已移除警報: {alert_id}")

def list_alerts():
    """列出所有警報"""
    alert = PriceAlert()
    alerts = alert.get_alerts(active_only=True)
    
    if not alerts:
        print("目前沒有警報")
        return
    
    print(f"\n{'='*60}")
    print(f"{'價格警報列表':^60}")
    print(f"{'='*60}")
    
    for a in alerts:
        status = '⏳' if not a.get('triggered') else '✅'
        cond = '↑' if a['condition'] == 'above' else '↓'
        print(f"{status} {a['code']} {a['name']} {cond} ${a['target_price']}")

def check_now():
    """立即檢查"""
    alert = PriceAlert()
    triggered = alert.check_alerts()
    
    if triggered:
        print(f"觸發 {len(triggered)} 個警報:")
        for a in triggered:
            print(alert.format_alert_message(a))
    else:
        print("沒有警報觸發")


# 路由範例
ALERT_ROUTES = '''
# 在 app.py 中加入

from price_alert import PriceAlert, AlertChecker

alert_system = PriceAlert()
alert_checker = AlertChecker(interval=60)  # 每分鐘檢查

@app.route('/api/alerts')
def get_alerts():
    """取得警報列表"""
    active = request.args.get('active', 'true').lower() == 'true'
    alerts = alert_system.get_alerts(active_only=active)
    return jsonify({'alerts': alerts, 'count': len(alerts)})

@app.route('/api/alerts/add', methods=['POST'])
def add_price_alert():
    """新增警報"""
    data = request.json
    alert_id = alert_system.add_alert(
        data['code'],
        data.get('name', ''),
        float(data['target_price']),
        data.get('condition', 'above'),
        data.get('note', '')
    )
    return jsonify({'success': True, 'alert_id': alert_id})

@app.route('/api/alerts/remove/<alert_id>')
def remove_price_alert(alert_id):
    """移除警報"""
    alert_system.remove_alert(alert_id)
    return jsonify({'success': True})

@app.route('/api/alerts/check')
def check_alerts_now():
    """立即檢查"""
    triggered = alert_system.check_alerts()
    return jsonify({
        'triggered': len(triggered),
        'alerts': triggered
    })

@app.route('/api/alerts/start')
def start_alert_checker():
    """啟動警報檢查（背景）"""
    line_token = request.args.get('line_token')
    alert_checker.start(line_token)
    return jsonify({'status': 'started'})

@app.route('/api/alerts/stop')
def stop_alert_checker():
    """停止警報檢查"""
    alert_checker.stop()
    return jsonify({'status': 'stopped'})

# 在應用啟動時自動啟動（可選）
# alert_checker.start()
'''


if __name__ == '__main__':
    print("=" * 50)
    print("  價格警報系統")
    print("=" * 50)
    
    # 新增測試警報
    print("\n1. 新增測試警報...")
    add_alert('2330', 850, 'above')
    add_alert('2330', 750, 'below')
    
    # 列出警報
    print("\n2. 警報列表:")
    list_alerts()
    
    # 立即檢查
    print("\n3. 立即檢查:")
    check_now()
