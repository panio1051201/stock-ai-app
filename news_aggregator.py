"""
News Aggregator - 新聞聚合器
自動抓取、更新、分類新聞
"""

import requests
from datetime import datetime, timedelta
import json
import os
import time
import random

# 新聞來源
NEWS_SOURCES = {
    'twse': {
        'name': '台灣證券交易所',
        'url': 'https://www.twse.com.tw/rss/',
        'type': 'official'
    },
    'cnyes': {
        'name': '鉅亨網',
        'url': 'https://news.cnyes.com/news/cat/tw_stock',
        'type': 'finance'
    },
    'money': {
        'name': 'Money DJ',
        'url': 'https://www.moneydj.com/news/topnews.htm',
        'type': 'finance'
    },
    'technews': {
        'name': '科技新報',
        'url': 'https://technews.tw/',
        'type': 'tech'
    },
    'udn': {
        'name': '聯合新聞網',
        'url': 'https://udn.com/news/cate/2/6639',
        'type': 'general'
    }
}

class NewsAggregator:
    """新聞聚合器"""
    
    def __init__(self, cache_file='news_cache.json'):
        self.cache_file = cache_file
        self.news_cache = self.load_cache()
    
    def load_cache(self):
        """載入快取"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'news': [], 'last_update': None}
        return {'news': [], 'last_update': None}
    
    def save_cache(self):
        """儲存快取"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.news_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"快取儲存失敗: {e}")
    
    def fetch_cnyes_news(self):
        """抓取鉅亨網新聞"""
        news = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(
                'https://api.cnyes.com/media/api/v1/newscenter/category/tw_stock',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', [])[:20]:
                    news.append({
                        'title': item.get('title', ''),
                        'source': '鉅亨網',
                        'url': item.get('href', ''),
                        'time': item.get('publishAt', ''),
                        'category': '財經'
                    })
        except Exception as e:
            print(f"鉅亨網抓取失敗: {e}")
        
        return news
    
    def fetch_twse_news(self):
        """抓取證交所新聞"""
        news = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(
                'https://www.twse.com.tw/rss/news',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # 解析 XML (簡單處理)
                content = response.text
                # 這裡需要 XML 解析，实际实现中可使用 lxml
                print("證交所新聞抓取成功")
        except Exception as e:
            print(f"證交所抓取失敗: {e}")
        
        return news
    
    def fetch_moneydj_news(self):
        """抓取 MoneyDJ 新聞"""
        news = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(
                'https://www.moneydj.com/news/topnews.htm',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("MoneyDJ 新聞抓取成功")
        except Exception as e:
            print(f"MoneyDJ 抓取失敗: {e}")
        
        return news
    
    def update_all(self, force=False):
        """更新所有新聞"""
        now = datetime.now()
        
        # 檢查是否需要更新（30分鐘內已更新）
        if not force and self.news_cache.get('last_update'):
            last = datetime.fromisoformat(self.news_cache['last_update'])
            if (now - last).minutes < 30:
                print(f"新聞已在 {self.news_cache['last_update']} 更新，跳過")
                return self.news_cache['news']
        
        print(f"[{now}] 開始更新新聞...")
        
        all_news = []
        
        # 依序抓取（避免被封）
        sources = ['cnyes', 'twse', 'moneydj']
        
        for source in sources:
            try:
                if source == 'cnyes':
                    news = self.fetch_cnyes_news()
                elif source == 'twse':
                    news = self.fetch_twse_news()
                elif source == 'moneydj':
                    news = self.fetch_moneydj_news()
                
                all_news.extend(news)
                print(f"  {source}: {len(news)} 則")
                
                # 隨機延遲避免被封
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"  {source} 失敗: {e}")
        
        # 更新快取
        self.news_cache = {
            'news': all_news,
            'last_update': now.isoformat(),
            'count': len(all_news)
        }
        self.save_cache()
        
        print(f"新聞更新完成，共 {len(all_news)} 則")
        return all_news
    
    def get_stock_news(self, stock_code=None, stock_name=None, limit=10):
        """取得特定股票相關新聞"""
        news = self.news_cache.get('news', [])
        
        if not stock_code and not stock_name:
            return news[:limit]
        
        # 簡單關鍵字匹配
        keywords = []
        if stock_code:
            keywords.append(stock_code)
        if stock_name:
            keywords.extend(stock_name.split())
        
        relevant = []
        for item in news:
            title = item.get('title', '').lower()
            for kw in keywords:
                if kw.lower() in title:
                    relevant.append(item)
                    break
        
        return relevant[:limit]
    
    def get_news_by_category(self, category, limit=10):
        """依分類取得新聞"""
        news = self.news_cache.get('news', [])
        filtered = [n for n in news if n.get('category') == category]
        return filtered[:limit]
    
    def format_news_html(self, news_list=None):
        """格式化新聞為 HTML"""
        if news_list is None:
            news_list = self.news_cache.get('news', [])[:20]
        
        if not news_list:
            return '<p class="no-news">暫無新聞</p>'
        
        html = '<div class="news-list">'
        
        for i, item in enumerate(news_list):
            category = item.get('category', '一般')
            title = item.get('title', '無標題')
            source = item.get('source', '未知')
            url = item.get('url', '#')
            time_str = item.get('time', '')
            
            # 熱門標記
            is_hot = i < 3
            hot_tag = '<span class="news-hot">熱</span>' if is_hot else ''
            
            html += f'''
            <div class="news-item" data-category="{category}">
                <span class="news-category {category}">{category}</span>
                <a href="{url}" target="_blank" class="news-title">
                    {hot_tag}{title}
                </a>
                <span class="news-source">{source}</span>
            </div>
            '''
        
        html += '</div>'
        return html


def auto_update_on_startup():
    """啟動時自動更新新聞（背景執行）"""
    import threading
    
    def background_update():
        time.sleep(5)  # 等待系統啟動
        aggregator = NewsAggregator()
        aggregator.update_all(force=True)
    
    thread = threading.Thread(target=background_update, daemon=True)
    thread.start()
    print("新聞自動更新執行緒已啟動")


# 新聞相關路由
NEWS_ROUTES = '''
# 在 app.py 中加入以下路由

from news_aggregator import NewsAggregator

news_agg = NewsAggregator()

@app.route('/api/news')
def get_news():
    """取得新聞列表"""
    category = request.args.get('category')
    limit = int(request.args.get('limit', 20))
    
    if category:
        news = news_agg.get_news_by_category(category, limit)
    else:
        news = news_agg.news_cache.get('news', [])[:limit]
    
    return jsonify({
        'news': news,
        'last_update': news_agg.news_cache.get('last_update'),
        'count': len(news)
    })

@app.route('/api/news/stock/<code>')
def get_stock_news(code):
    """取得個股相關新聞"""
    limit = int(request.args.get('limit', 10))
    name = request.args.get('name', '')
    
    news = news_agg.get_stock_news(code, name, limit)
    
    return jsonify({
        'stock': code,
        'news': news,
        'count': len(news)
    })

@app.route('/api/news/refresh')
def refresh_news():
    """手動刷新新聞"""
    news_agg.update_all(force=True)
    return jsonify({
        'success': True,
        'count': len(news_agg.news_cache.get('news', [])),
        'last_update': news_agg.news_cache.get('last_update')
    })

# 在應用啟動時自動更新
@app.before_request
def check_news_update():
    if not news_agg.news_cache.get('last_update'):
        import threading
        def delayed_update():
            time.sleep(5)
            news_agg.update_all()
        threading.Thread(target=delayed_update, daemon=True).start()
'''


if __name__ == '__main__':
    print("=" * 50)
    print("  新聞聚合器測試")
    print("=" * 50)
    
    agg = NewsAggregator()
    
    print("\n1. 測試更新新聞...")
    news = agg.update_all()
    
    print(f"\n2. 新聞總數: {len(news)}")
    
    print("\n3. 前5則新聞:")
    for i, item in enumerate(news[:5]):
        print(f"  [{i+1}] {item.get('title', 'N/A')[:50]}...")
    
    print("\n4. 測試 HTML 格式:")
    html = agg.format_news_html(news[:5])
    print(html[:500])
