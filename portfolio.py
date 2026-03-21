"""
My Portfolio - 我的持股投資組合
記錄投資、計算損益、統計分析
"""

import pandas as pd
from datetime import datetime
import json
import os

class Portfolio:
    """投資組合管理器"""
    
    def __init__(self, portfolio_file='my_portfolio.json'):
        self.portfolio_file = portfolio_file
        self.data = self.load()
    
    def load(self):
        """載入投資組合"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'stocks': [], 'cash': 0, 'history': []}
        return {'stocks': [], 'cash': 0, 'history': []}
    
    def save(self):
        """儲存投資組合"""
        try:
            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存失敗: {e}")
    
    def add_stock(self, code, name, shares, buy_price, buy_date=None):
        """
        新增持股
        
        Args:
            code: 股票代碼
            name: 股票名稱
            shares: 股數
            buy_price: 買入價格
            buy_date: 買入日期 (預設今天)
        """
        if buy_date is None:
            buy_date = datetime.now().strftime('%Y-%m-%d')
        
        # 檢查是否已存在
        for stock in self.data['stocks']:
            if stock['code'] == code:
                # 更新現有持股
                old_shares = stock['shares']
                old_price = stock['buy_price']
                total_cost = old_shares * old_price + shares * buy_price
                new_shares = old_shares + shares
                new_price = total_cost / new_shares
                
                stock['shares'] = new_shares
                stock['buy_price'] = new_price
                stock['last_update'] = datetime.now().isoformat()
                
                # 記錄歷史
                self.add_history('add', code, shares, buy_price)
                self.save()
                return True, '已更新現有持股'
        
        # 新增持股
        self.data['stocks'].append({
            'code': code,
            'name': name,
            'shares': shares,
            'buy_price': buy_price,
            'buy_date': buy_date,
            'added_date': datetime.now().strftime('%Y-%m-%d'),
            'last_update': datetime.now().isoformat()
        })
        
        self.add_history('buy', code, shares, buy_price)
        self.save()
        return True, f'已新增 {code} {name}'
    
    def remove_stock(self, code, shares=None, sell_price=None):
        """
        賣出持股
        
        Args:
            code: 股票代碼
            shares: 賣出股數 (None = 全數賣出)
            sell_price: 賣出價格
        """
        for i, stock in enumerate(self.data['stocks']):
            if stock['code'] == code:
                if shares is None or shares >= stock['shares']:
                    # 全數賣出
                    if sell_price:
                        profit = (sell_price - stock['buy_price']) * stock['shares']
                        self.add_history('sell_full', code, stock['shares'], sell_price, profit)
                    self.data['stocks'].pop(i)
                    self.save()
                    return True, f'已全數賣出 {code}'
                else:
                    # 部分賣出
                    profit = (sell_price - stock['buy_price']) * shares
                    stock['shares'] -= shares
                    stock['last_update'] = datetime.now().isoformat()
                    self.add_history('sell_partial', code, shares, sell_price, profit)
                    self.save()
                    return True, f'已賣出 {code} {shares} 股'
        
        return False, f'找不到 {code}'
    
    def update_price(self, code, current_price):
        """更新現價"""
        for stock in self.data['stocks']:
            if stock['code'] == code:
                stock['current_price'] = current_price
                stock['last_update'] = datetime.now().isoformat()
                self.save()
                return True
        return False
    
    def add_history(self, action, code, shares, price, profit=None):
        """新增歷史記錄"""
        entry = {
            'date': datetime.now().isoformat(),
            'action': action,
            'code': code,
            'shares': shares,
            'price': price,
            'total': shares * price
        }
        if profit is not None:
            entry['profit'] = profit
        
        self.data['history'].append(entry)
        
        # 只保留最近100筆記錄
        if len(self.data['history']) > 100:
            self.data['history'] = self.data['history'][-100:]
    
    def get_summary(self, current_prices=None):
        """
        取得投資組合摘要
        
        Args:
            current_prices: dict of {code: price}
        """
        stocks = self.data['stocks']
        
        if not stocks:
            return {
                'total_cost': 0,
                'total_value': 0,
                'total_profit': 0,
                'profit_rate': 0,
                'count': 0,
                'stocks': []
            }
        
        total_cost = 0
        total_value = 0
        stock_list = []
        
        for stock in stocks:
            code = stock['code']
            shares = stock['shares']
            buy_price = stock['buy_price']
            cost = shares * buy_price
            
            current_price = current_prices.get(code, stock.get('current_price', buy_price)) if current_prices else stock.get('current_price', buy_price)
            value = shares * current_price
            profit = value - cost
            profit_rate = (profit / cost * 100) if cost > 0 else 0
            
            total_cost += cost
            total_value += value
            
            stock_list.append({
                'code': code,
                'name': stock['name'],
                'shares': shares,
                'buy_price': buy_price,
                'current_price': current_price,
                'cost': cost,
                'value': value,
                'profit': profit,
                'profit_rate': profit_rate,
                'buy_date': stock.get('buy_date', '')
            })
        
        total_profit = total_value - total_cost
        profit_rate = (total_profit / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_cost': total_cost,
            'total_value': total_value,
            'total_profit': total_profit,
            'profit_rate': profit_rate,
            'cash': self.data.get('cash', 0),
            'total_assets': total_value + self.data.get('cash', 0),
            'count': len(stocks),
            'stocks': stock_list
        }
    
    def format_table(self, summary=None):
        """格式化為表格顯示"""
        if summary is None:
            summary = self.get_summary()
        
        if not summary['stocks']:
            return "目前沒有持股"
        
        # 表頭
        header = f"{'代碼':<8} {'名稱':<10} {'股數':>6} {'成本':>10} {'現價':>10} {'現值':>12} {'賺虧':>12} {'%':>8}"
        sep = "=" * len(header)
        
        lines = [sep, header, sep]
        
        for s in summary['stocks']:
            emoji = '🟢' if s['profit'] >= 0 else '🔴'
            profit_str = f"{emoji}{s['profit']:,.0f}"
            rate_str = f"{'+' if s['profit_rate'] >= 0 else ''}{s['profit_rate']:.2f}%"
            
            line = f"{s['code']:<8} {s['name']:<10} {s['shares']:>6} {s['buy_price']:>10.2f} {s['current_price']:>10.2f} {s['value']:>12,.0f} {profit_str:>12} {rate_str:>8}"
            lines.append(line)
        
        lines.append(sep)
        
        # 總計
        total_emoji = '🟢' if summary['profit_rate'] >= 0 else '🔴'
        lines.append(f"總成本: {summary['total_cost']:,.0f} | 總市值: {summary['total_value']:,.0f}")
        lines.append(f"總賺虧: {total_emoji}{summary['total_profit']:,.0f} ({'+' if summary['profit_rate'] >= 0 else ''}{summary['profit_rate']:.2f}%)")
        lines.append(f"可用現金: {summary['cash']:,.0f} | 總資產: {summary['total_assets']:,.0f}")
        
        return "\n".join(lines)
    
    def get_html(self, summary=None):
        """取得 HTML 格式"""
        if summary is None:
            summary = self.get_summary()
        
        if not summary['stocks']:
            return '''
            <div class="portfolio-empty">
                <i class="fas fa-chart-line"></i>
                <p>目前沒有持股</p>
                <p>點擊上方「+」新增第一筆投資</p>
            </div>
            '''
        
        # 總覽
        total_class = 'profit' if summary['profit_rate'] >= 0 else 'loss'
        total_emoji = '🟢' if summary['profit_rate'] >= 0 else '🔴'
        
        html = f'''
        <div class="portfolio-summary">
            <div class="summary-card {total_class}">
                <div class="summary-label">總資產</div>
                <div class="summary-value">${summary['total_assets']:,.0f}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">總市值</div>
                <div class="summary-value">${summary['total_value']:,.0f}</div>
            </div>
            <div class="summary-card {total_class}">
                <div class="summary-label">總賺虧</div>
                <div class="summary-value">{total_emoji}{summary['total_profit']:,.0f}</div>
                <div class="summary-rate">{'+' if summary['profit_rate'] >= 0 else ''}{summary['profit_rate']:.2f}%</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">現金</div>
                <div class="summary-value">${summary['cash']:,.0f}</div>
            </div>
        </div>
        
        <div class="portfolio-list">
            <table class="portfolio-table">
                <thead>
                    <tr>
                        <th>股票</th>
                        <th>股數</th>
                        <th>成本</th>
                        <th>現價</th>
                        <th>現值</th>
                        <th>賺虧</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for s in summary['stocks']:
            row_class = 'profit' if s['profit'] >= 0 else 'loss'
            emoji = '🟢' if s['profit'] >= 0 else '🔴'
            
            html += f'''
                    <tr class="{row_class}">
                        <td>
                            <div class="stock-code">{s['code']}</div>
                            <div class="stock-name">{s['name']}</div>
                        </td>
                        <td>{s['shares']}</td>
                        <td>${s['buy_price']:.2f}</td>
                        <td>${s['current_price']:.2f}</td>
                        <td>${s['value']:,.0f}</td>
                        <td>
                            <div>{emoji}{s['profit']:,.0f}</div>
                            <div class="rate">{'+' if s['profit_rate'] >= 0 else ''}{s['profit_rate']:.2f}%</div>
                        </td>
                    </tr>
            '''
        
        html += '''
                </tbody>
            </table>
        </div>
        '''
        
        return html


# 快捷函式
def quick_add(code, name, shares, price):
    """快速新增持股"""
    portfolio = Portfolio()
    success, msg = portfolio.add_stock(code, name, shares, price)
    print(msg)
    return success

def quick_remove(code, shares=None, sell_price=None):
    """快速賣出"""
    portfolio = Portfolio()
    success, msg = portfolio.remove_stock(code, shares, sell_price)
    print(msg)
    return success

def show_portfolio():
    """顯示投資組合"""
    portfolio = Portfolio()
    summary = portfolio.get_summary()
    print(portfolio.format_table(summary))


# 路由範例
PORTFOLIO_ROUTES = '''
# 在 app.py 中加入

from portfolio import Portfolio

portfolio = Portfolio()

@app.route('/api/portfolio')
def get_portfolio():
    """取得投資組合"""
    summary = portfolio.get_summary()
    return jsonify(summary)

@app.route('/api/portfolio/html')
def get_portfolio_html():
    """取得 HTML 格式"""
    summary = portfolio.get_summary()
    html = portfolio.get_html(summary)
    return html

@app.route('/api/portfolio/add', methods=['POST'])
def add_to_portfolio():
    """新增持股"""
    data = request.json
    success, msg = portfolio.add_stock(
        data['code'],
        data.get('name', ''),
        int(data['shares']),
        float(data['buy_price']),
        data.get('buy_date')
    )
    return jsonify({'success': success, 'message': msg})

@app.route('/api/portfolio/sell', methods=['POST'])
def sell_from_portfolio():
    """賣出持股"""
    data = request.json
    success, msg = portfolio.remove_stock(
        data['code'],
        data.get('shares'),
        float(data.get('sell_price', 0))
    )
    return jsonify({'success': success, 'message': msg})

@app.route('/api/portfolio/update_prices', methods=['POST'])
def update_portfolio_prices():
    """更新所有現價"""
    from data_loader import get_latest_prices
    prices = get_latest_prices()
    
    summary = portfolio.get_summary(prices)
    return jsonify(summary)
'''


if __name__ == '__main__':
    print("=" * 50)
    print("  我的持股投資組合")
    print("=" * 50)
    
    portfolio = Portfolio()
    
    print("\n1. 新增測試持股...")
    portfolio.add_stock('2330', '台積電', 1000, 800)
    portfolio.add_stock('2317', '鴻海', 2000, 200)
    
    print("\n2. 投資組合:")
    summary = portfolio.get_summary({
        '2330': 850,
        '2317': 180
    })
    print(portfolio.format_table(summary))
    
    print("\n3. HTML 格式:")
    html = portfolio.get_html(summary)
    print(html[:500])
