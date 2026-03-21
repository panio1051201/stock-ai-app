# 金融戰情室 Pro (Stock AI Pro)

全端股票分析系統，支援技術分析、籌碼分析、財務分析。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📊 功能

### 技術分析
| 策略 | 說明 |
|------|------|
| MA | 葛蘭碧八大法則 + 林恩如均線戰法 |
| KD | KDJ 隨機指標 |
| RSI | 相對強弱指數 |
| MACD | 指數平滑異同移動平均線 |
| QQE | 量化趨勢指標 |
| Bollinger | 布林通道 |
| BOX | 區間震盪指標 |

### 進階分析
| 策略 | 說明 |
|------|------|
| SUMMARY | 綜合全方位健檢（技術+基本面+籌碼） |
| DEMON | 妖股精靈（全市場強勢股掃描） |
| FOREIGN_BUY | 主力買超追蹤 |
| FINANCIAL | 財務報表分析 |
| CHIPS | 三大法人籌碼 |

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定 API Token

```bash
# 取得 FinMind API Token
# 免費申請: https://finmindtrade.com/

export FINMIND_API_TOKEN="your_token_here"
```

### 3. 啟動

```bash
python app.py
```

打開瀏覽器訪問: http://localhost:5000

## 📁 專案結構

```
stock-ai-app/
├── app.py                 # Flask 主程式
├── data_loader.py         # 資料載入器
├── error_handler.py       # 錯誤處理
├── performance.py         # 效能優化
├── strategies/
│   ├── basic/            # 基礎策略
│   └── advanced/          # 進階策略
├── templates/
│   └── index.html         # 前端介面
└── static/               # 靜態資源
```

## 🎯 使用方式

1. 輸入股票代碼（如：2330）
2. 選擇分析策略
3. 點擊分析

### 支援功能
- [x] 技術指標分析
- [x] 籌碼分析（三大法人）
- [x] 財務分析（EPS、殖利率）
- [x] 綜合健檢
- [x] 妖股掃描
- [x] 歷史回測
- [x] 錯誤處理強化
- [x] UI/UX 增強
- [x] 效能優化

## 🔧 技術棧

- **後端**: Flask, Pandas, NumPy
- **前端**: HTML5, JavaScript, Chart.js
- **資料來源**: FinMind API

## 📝 License

MIT License
