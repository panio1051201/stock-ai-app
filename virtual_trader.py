"""
Virtual Trading - 模擬炒股系統
用虛擬金練習，不會真的虧錢
"""

import pandas as pd
from datetime import datetime
import json
import os

class VirtualTrader:
    """虛擬交易系統"""
    
    def __init__(self, initial_cash=1000000, file='virtual_account.json'):
        """
        初始化虛擬帳戶
        
        Args:
            initial_cash: 初始資金（預設100萬）
            file: 帳戶檔案
        """
        self.file = file
        self.initial_cash = initial_cash
        self.account = self.load()
    
    def load(self):
        """載入帳戶"""
        if os.path.exists(self.file):
            try:
                with open(self.file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 新建帳戶
        return {
            'cash': self.initial_cash,
            'initial_cash': self.initial_cash,
            'positions': [],  # 持倉
            'history': [],    # 交易歷史
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    def save(self):
        """儲存帳戶"""
        self.account['updated_at'] = datetime.now().isoformat()
        try:
            with open(self.file, 'w', encoding='utf-8') as f:
                json.dump(self.account, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存失敗: {e}")
    
    def buy(self, code, name, shares, price):
        """
        模擬買入
        
        Returns:
            (success, message)
        """
        total_cost = shares * price
        commission = total_cost * 0.001425  # 交易手續費（約0.1425%）
        total = total_cost + commission
        
        # 檢查餘額
        if total > self.account['cash']:
            return False, f'現金不足！需要 ${total:,.0f}，帳戶只有 ${self.account["cash"]:,.0f}'
        
        # 執行買入
        self.account['cash'] -= total
        
        # 檢查是否已有持倉
        position_found = False
        for pos in self.account['positions']:
            if pos['code'] == code:
                # 更新現有持倉
                old_shares = pos['shares']
                old_price = pos['avg_price']
                
                new_shares = old_shares + shares
                new_cost = old_shares * old_price + shares * price
                new_avg = new_cost / new_shares
                
                pos['shares'] = new_shares
                pos['avg_price'] = new_avg
                pos['updated_at'] = datetime.now().isoformat()
                
                position_found = True
                break
        
        if not position_found:
            # 新增持倉
            self.account['positions'].append({
                'code': code,
                'name': name,
                'shares': shares,
                'avg_price': price,
                'bought_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        # 記錄歷史
        self.account['history'].append({
            'action': 'buy',
            'code': code,
            'name': name,
            'shares': shares,
            'price': price,
            'commission': commission,
            'total': total,
            'cash': self.account['cash'],
            'time': datetime.now().isoformat()
        })
        
        self.save()
        return True, f'✅ 買入成功！\n{name} ({code})\n{shares} 股 @ ${price}\n手續費: ${commission:,.0f}\n剩餘現金: ${self.account["cash"]:,.0f}'
    
    def sell(self, code, shares=None, price=None):
        """
        模擬賣出
        
        Args:
            code: 股票代碼
            shares: 賣出股數（None = 全數賣出）
            price: 賣出價格（None = 使用成本價）
        """
        # 找持倉
        position_idx = None
        position = None
        
        for i, pos in enumerate(self.account['positions']):
            if pos['code'] == code:
                position_idx = i
                position = pos
                break
        
        if position is None:
            return False, f'沒有持有 {code}'
        
        # 檢查股數
        if shares is None:
            shares = position['shares']
        
        if shares > position['shares']:
            return False, f'持股不足！持有 {position["shares"]} 股，要賣 {shares} 股'
        
        # 檢查價格
        if price is None:
            price = position['avg_price']
        
        # 計算金額
        total_revenue = shares * price
        commission = total_revenue * 0.001425  # 手續費
        tax = total_revenue * 0.003  # 交易稅（0.3%）
        net = total_revenue - commission - tax
        
        # 更新持倉
        if shares >= position['shares']:
            # 全數賣出
            profit = net - (position['shares'] * position['avg_price'])
            self.account['positions'].pop(position_idx)
        else:
            # 部分賣出
            profit = (price - position['avg_price']) * shares
            position['shares'] -= shares
            position['updated_at'] = datetime.now().isoformat()
        
        # 更新現金
        self.account['cash'] += net
        
        # 記錄歷史
        self.account['history'].append({
            'action': 'sell',
            'code': code,
            'name': position['name'],
            'shares': shares,
            'price': price,
            'commission': commission,
            'tax': tax,
            'net': net,
            'profit': profit,
            'cash': self.account['cash'],
            'time': datetime.now().isoformat()
        })
        
        self.save()
        
        emoji = '🟢' if profit >= 0 else '🔴'
        return True, f'✅ 賣出成功！\n{position["name"]} ({code})\n{shares} 股 @ ${price}\n淨額: ${net:,.0f}\n獲利: {emoji}${abs(profit):,.0f}\n剩餘現金: ${self.account["cash"]:,.0f}'
    
    def get_portfolio_value(self, current_prices=None):
        """計算總市值"""
        total_stock_value = 0
        positions_value = []
        
        for pos in self.account['positions']:
            code = pos['code']
            shares = pos['shares']
            avg_price = pos['avg_price']
            
            # 取得現價
            if current_prices and code in current_prices:
                current_price = current_prices[code]
            else:
                current_price = avg_price  # 如果沒有現價，用成本價
            
            value = shares * current_price
            cost = shares * avg_price
            profit = value - cost
            profit_rate = (profit / cost * 100) if cost > 0 else 0
            
            total_stock_value += value
            positions_value.append({
                'code': code,
                'name': pos['name'],
                'shares': shares,
                'avg_price': avg_price,
                'current_price': current_price,
                'value': value,
                'cost': cost,
                'profit': profit,
                'profit_rate': profit_rate
            })
        
        total_assets = self.account['cash'] + total_stock_value
        total_profit = total_assets - self.account['initial_cash']
        profit_rate = (total_profit / self.account['initial_cash'] * 100) if self.account['initial_cash'] > 0 else 0
        
        return {
            'cash': self.account['cash'],
            'stock_value': total_stock_value,
            'total_assets': total_assets,
            'initial_cash': self.account['initial_cash'],
            'total_profit': total_profit,
            'profit_rate': profit_rate,
            'positions': positions_value,
            'win_count': len([h for h in self.account['history'] if h['action'] == 'sell' and h.get('profit', 0) > 0]),
            'lose_count': len([h for h in self.account['history'] if h['action'] == 'sell' and h.get('profit', 0) < 0])
        }
    
    def reset(self):
        """重置帳戶"""
        self.account = {
            'cash': self.initial_cash,
            'initial_cash': self.initial_cash,
            'positions': [],
            'history': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.save()
        return True, f'✅ 帳戶已重置，初始金額 ${self.initial_cash:,.0f}'
    
    def format_summary(self, current_prices=None):
        """格式化帳戶摘要"""
        portfolio = self.get_portfolio_value(current_prices)
        
        emoji = '🟢' if portfolio['profit_rate'] >= 0 else '🔴'
        
        summary = f"""
{'='*50}
  虛擬帳戶摘要
{'='*50}

初始資金: ${portfolio['initial_cash']:,.0f}
總資產:   ${portfolio['total_assets']:,.0f}
持倉市值: ${portfolio['stock_value']:,.0f}
可用現金: ${portfolio['cash']:,.0f}

總賺虧:   {emoji}${abs(portfolio['total_profit']):,.0f} ({'+' if portfolio['profit_rate'] >= 0 else ''}{portfolio['profit_rate']:.2f}%)

勝率:     {portfolio['win_count']}勝 {portfolio['lose_count']}敗
{'='*50}
"""
        
        # 持倉明細
        if portfolio['positions']:
            summary += '\n持倉明細:\n'
            for pos in portfolio['positions']:
                pos_emoji = '🟢' if pos['profit'] >= 0 else '🔴'
                summary += f"  {pos['code']} {pos['name']}\n"
                summary += f"    {pos['shares']}股 @ ${pos['avg_price']:.2f}\n"
                summary += f"    現價: ${pos['current_price']:.2f} {pos_emoji}{abs(pos['profit_rate']):.1f}%\n"
        
        return summary
    
    def get_history_html(self, limit=20):
        """取得歷史 HTML"""
        history = self.account['history'][-limit:]
        
        if not history:
            return '<p class="no-history">尚無交易紀錄</p>'
        
        html = '<div class="history-list">'
        
        for h in reversed(history):
            action = h['action']
            code = h['code']
            name = h.get('name', '')
            shares = h['shares']
            price = h['price']
            
            if action == 'buy':
                html += f'''
                <div class="history-item buy">
                    <div class="history-action">📥 買入</div>
                    <div class="history-detail">
                        <div class="history-stock">{code} {name}</div>
                        <div class="history-info">{shares} 股 @ ${price}</div>
                    </div>
                    <div class="history-time">{h['time'][:10]}</div>
                </div>
                '''
            else:
                profit = h.get('profit', 0)
                emoji = '🟢' if profit >= 0 else '🔴'
                html += f'''
                <div class="history-item sell">
                    <div class="history-action">📤 賣出</div>
                    <div class="history-detail">
                        <div class="history-stock">{code} {name}</div>
                        <div class="history-info">{shares} 股 @ ${price}</div>
                        <div class="history-profit">{emoji}${abs(profit):,.0f}</div>
                    </div>
                    <div class="history-time">{h['time'][:10]}</div>
                </div>
                '''
        
        html += '</div>'
        return html


# 快捷函式
def buy(code, shares, price):
    """快速買入"""
    import data_loader
    name, _ = data_loader.get_stock_name(code)
    
    trader = VirtualTrader()
    success, msg = trader.buy(code, name, shares, price)
    print(msg)
    return success

def sell(code, shares=None, price=None):
    """快速賣出"""
    trader = VirtualTrader()
    success, msg = trader.sell(code, shares, price)
    print(msg)
    return success

def show_account():
    """顯示帳戶"""
    trader = VirtualTrader()
    print(trader.format_summary())


# 路由範例
TRADER_ROUTES = '''
# 在 app.py 中加入

from virtual_trader import VirtualTrader

trader = VirtualTrader(initial_cash=1000000)

@app.route('/api/trader/account')
def get_virtual_account():
    """取得虛擬帳戶"""
    from data_loader import get_latest_prices
    prices = get_latest_prices()
    
    portfolio = trader.get_portfolio_value(prices)
    return jsonify(portfolio)

@app.route('/api/trader/buy', methods=['POST'])
def virtual_buy():
    """虛擬買入"""
    data = request.json
    
    success, msg = trader.buy(
        data['code'],
        data.get('name', ''),
        int(data['shares']),
        float(data['price'])
    )
    
    return jsonify({'success': success, 'message': msg})

@app.route('/api/trader/sell', methods=['POST'])
def virtual_sell():
    """虛擬賣出"""
    data = request.json
    
    success, msg = trader.sell(
        data['code'],
        data.get('shares'),
        data.get('price')
    )
    
    return jsonify({'success': success, 'message': msg})

@app.route('/api/trader/reset')
def reset_virtual_account():
    """重置帳戶"""
    success, msg = trader.reset()
    return jsonify({'success': success, 'message': msg})

@app.route('/api/trader/history')
def get_trader_history():
    """取得交易歷史"""
    html = trader.get_history_html()
    return html
'''


if __name__ == '__main__':
    print("=" * 50)
    print("  虛擬炒股系統")
    print("=" * 50)
    
    trader = VirtualTrader(initial_cash=1000000)
    
    print("\n1. 買入測試...")
    trader.buy('2330', '台積電', 1000, 800)
    
    print("\n2. 再買鴻海...")
    trader.buy('2317', '鴻海', 2000, 200)
    
    print("\n3. 帳戶摘要...")
    print(trader.format_summary({'2330': 850, '2317': 180}))
    
    print("\n4. 歷史:")
    print(trader.get_history_html())
