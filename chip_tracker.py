"""
Manual Chip Tracker - 手動籌碼追蹤器
記錄和追蹤自選股的籌碼變化
"""

import pandas as pd
from datetime import datetime, timedelta
import json
import os

class ChipTracker:
    """籌碼追蹤器"""
    
    def __init__(self, watchlist_file='chip_watchlist.json'):
        self.watchlist_file = watchlist_file
        self.watchlist = self.load_watchlist()
    
    def load_watchlist(self):
        """載入自選股"""
        if os.path.exists(self.watchlist_file):
            try:
                with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_watchlist(self):
        """儲存自選股"""
        try:
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(self.watchlist, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存失敗: {e}")
    
    def add_stock(self, code, name=None, note=''):
        """新增股票到追蹤"""
        if code not in self.watchlist:
            self.watchlist[code] = {
                'name': name or code,
                'note': note,
                'added_date': datetime.now().strftime('%Y-%m-%d'),
                'history': []
            }
            self.save_watchlist()
            return True
        return False
    
    def remove_stock(self, code):
        """移除股票"""
        if code in self.watchlist:
            del self.watchlist[code]
            self.save_watchlist()
            return True
        return False
    
    def update_chip(self, code, chip_data):
        """更新籌碼資料"""
        if code not in self.watchlist:
            return False
        
        now = datetime.now()
        
        # 取得今日資料
        today_str = now.strftime('%Y-%m-%d')
        
        # 檢查是否已有今日資料
        history = self.watchlist[code].get('history', [])
        
        # 解析籌碼資料
        try:
            foreign_net = chip_data.get('foreign_net', 0)
            trust_net = chip_data.get('trust_net', 0)
            dealer_net = chip_data.get('dealer_net', 0)
            margin_balance = chip_data.get('margin_balance', 0)
            short_balance = chip_data.get('short_balance', 0)
            
            entry = {
                'date': today_str,
                'time': now.strftime('%H:%M:%S'),
                'foreign_net': foreign_net,
                'trust_net': trust_net,
                'dealer_net': dealer_net,
                'total': foreign_net + trust_net + dealer_net,
                'margin_balance': margin_balance,
                'short_balance': short_balance
            }
            
            # 檢查是否已記錄今日
            today_exists = False
            for i, h in enumerate(history):
                if h.get('date') == today_str:
                    history[i] = entry
                    today_exists = True
                    break
            
            if not today_exists:
                history.append(entry)
            
            # 只保留30天
            if len(history) > 30:
                history = history[-30:]
            
            self.watchlist[code]['history'] = history
            
            # 更新摘要
            if history:
                last = history[-1]
                prev = history[-2] if len(history) > 1 else last
                
                self.watchlist[code]['latest'] = {
                    'date': last['date'],
                    'foreign_net': last['foreign_net'],
                    'trust_net': last['trust_net'],
                    'dealer_net': last['dealer_net'],
                    'total': last['total'],
                    'margin': last['margin_balance'],
                    'foreign_change': last['foreign_net'] - prev.get('foreign_net', 0),
                    'trust_change': last['trust_net'] - prev.get('trust_net', 0),
                }
            
            self.save_watchlist()
            return True
            
        except Exception as e:
            print(f"更新籌碼失敗: {e}")
            return False
    
    def get_summary(self, code):
        """取得個股籌碼摘要"""
        if code not in self.watchlist:
            return None
        
        stock = self.watchlist[code]
        history = stock.get('history', [])
        
        if not history:
            return {
                'code': code,
                'name': stock['name'],
                'status': '尚無資料'
            }
        
        # 計算趨勢
        if len(history) >= 5:
            recent = history[-5:]
            avg_foreign = sum(h.get('foreign_net', 0) for h in recent) / 5
            avg_trust = sum(h.get('trust_net', 0) for h in recent) / 5
        else:
            avg_foreign = history[-1].get('foreign_net', 0)
            avg_trust = history[-1].get('trust_net', 0)
        
        # 判斷狀態
        latest = history[-1]
        total = latest.get('total', 0)
        
        if total > 3000:
            status = '🔴 三大法人偏多'
        elif total < -3000:
            status = '🟢 三大法人偏空'
        else:
            status = '⚪ 中立觀望'
        
        return {
            'code': code,
            'name': stock['name'],
            'note': stock.get('note', ''),
            'status': status,
            'latest': {
                'date': latest.get('date', ''),
                'foreign': latest.get('foreign_net', 0),
                'trust': latest.get('trust_net', 0),
                'dealer': latest.get('dealer_net', 0),
                'total': total,
                'margin': latest.get('margin_balance', 0)
            },
            'trend': {
                'foreign_avg': avg_foreign,
                'trust_avg': avg_trust
            },
            'history_count': len(history)
        }
    
    def get_all_summaries(self):
        """取得所有追蹤股票摘要"""
        summaries = []
        for code in self.watchlist:
            summary = self.get_summary(code)
            if summary:
                summaries.append(summary)
        return summaries
    
    def format_table(self):
        """格式化為表格顯示"""
        summaries = self.get_all_summaries()
        
        if not summaries:
            return "尚無追蹤股票"
        
        # 表頭
        header = f"{'代碼':<8} {'名稱':<10} {'外傷':>10} {'投信':>10} {'自營':>10} {'合計':>10} {'狀態':<15}"
        separator = "-" * len(header)
        
        lines = [header, separator]
        
        for s in summaries:
            code = s['code']
            name = s['name'][:8]
            lat = s.get('latest', {})
            
            foreign = lat.get('foreign', 0)
            trust = lat.get('trust', 0)
            dealer = lat.get('dealer', 0)
            total = lat.get('total', 0)
            status = s['status'][:10]
            
            # 格式化數字
            foreign_str = f"{foreign/1000:>8.0f}張"
            trust_str = f"{trust/1000:>8.0f}張"
            dealer_str = f"{dealer/1000:>8.0f}張"
            total_str = f"{total/1000:>8.0f}張"
            
            line = f"{code:<8} {name:<10} {foreign_str} {trust_str} {dealer_str} {total_str} {status:<15}"
            lines.append(line)
        
        return "\n".join(lines)


# 快捷函式
def quick_add(code, name=''):
    """快速新增股票"""
    tracker = ChipTracker()
    tracker.add_stock(code, name)
    print(f"已新增: {code} {name}")


def quick_update(code):
    """快速更新籌碼"""
    import data_loader
    
    tracker = ChipTracker()
    
    # 抓取籌碼
    try:
        chip_df = data_loader.fetch_institutional_investors(code, days=5)
        if chip_df is None or chip_df.empty:
            print(f"無法取得 {code} 的籌碼資料")
            return
        
        # 計算總計
        foreign_net = chip_df['Foreign_Investor_Net'].sum() if 'Foreign_Investor_Net' in chip_df.columns else 0
        trust_net = chip_df['Investment_Trust_Net'].sum() if 'Investment_Trust_Net' in chip_df.columns else 0
        dealer_net = chip_df['Dealer_Net'].sum() if 'Dealer_Net' in chip_df.columns else 0
        
        chip_data = {
            'foreign_net': foreign_net,
            'trust_net': trust_net,
            'dealer_net': dealer_net
        }
        
        tracker.update_chip(code, chip_data)
        print(f"已更新 {code} 的籌碼")
        
    except Exception as e:
        print(f"更新失敗: {e}")


# 路由範例
CHIP_ROUTES = '''
# 在 app.py 中加入

from chip_tracker import ChipTracker

chip_tracker = ChipTracker()

@app.route('/api/chips/watchlist')
def get_watchlist():
    """取得追蹤清單"""
    summaries = chip_tracker.get_all_summaries()
    return jsonify({
        'stocks': summaries,
        'count': len(summaries)
    })

@app.route('/api/chips/add', methods=['POST'])
def add_to_watchlist():
    """新增股票到追蹤"""
    data = request.json
    code = data.get('code')
    name = data.get('name', '')
    note = data.get('note', '')
    
    if chip_tracker.add_stock(code, name, note):
        return jsonify({'success': True, 'message': f'已新增 {code}'})
    else:
        return jsonify({'success': False, 'message': f'{code} 已在清單中'})

@app.route('/api/chips/remove/<code>')
def remove_from_watchlist(code):
    """移除股票"""
    if chip_tracker.remove_stock(code):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '找不到該股票'})

@app.route('/api/chips/update/<code>')
def update_stock_chips(code):
    """更新股票籌碼"""
    import data_loader
    
    try:
        chip_df = data_loader.fetch_institutional_investors(code, days=5)
        if chip_df is None or chip_df.empty:
            return jsonify({'error': '無法取得籌碼資料'})
        
        foreign_net = int(chip_df['Foreign_Investor_Net'].sum()) if 'Foreign_Investor_Net' in chip_df.columns else 0
        trust_net = int(chip_df['Investment_Trust_Net'].sum()) if 'Investment_Trust_Net' in chip_df.columns else 0
        dealer_net = int(chip_df['Dealer_Net'].sum()) if 'Dealer_Net' in chip_df.columns else 0
        
        chip_data = {
            'foreign_net': foreign_net,
            'trust_net': trust_net,
            'dealer_net': dealer_net
        }
        
        chip_tracker.update_chip(code, chip_data)
        
        return jsonify({
            'success': True,
            'data': chip_tracker.get_summary(code)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chips/table')
def get_chips_table():
    """取得籌碼表格"""
    return chip_tracker.format_table()
'''


if __name__ == '__main__':
    print("=" * 50)
    print("  籌碼追蹤器")
    print("=" * 50)
    
    tracker = ChipTracker()
    
    print("\n1. 新增測試股票")
    tracker.add_stock('2330', '台積電', '護國神山')
    tracker.add_stock('2317', '鴻海', '蘋果供應商')
    
    print("\n2. 追蹤清單:")
    print(tracker.format_table())
    
    print("\n3. 取得摘要:")
    for code in tracker.watchlist:
        summary = tracker.get_summary(code)
        print(f"  {code}: {summary.get('status', 'N/A')}")
