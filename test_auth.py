import requests
import json
import time

URL = "http://127.0.0.1:5000/api/analyze"
BT_URL = "http://127.0.0.1:5000/api/proxy/retrolyze"

print("--- 測試 1: 訪客 (無代碼) 嘗試執行 FOREIGN_BUY (應被拒絕) ---")
res = requests.post(URL, json={'code': '2330', 'type': 'FOREIGN_BUY', 'access_code': ''})
print(res.status_code, res.json())

print("\n--- 測試 2: 會員 (MEMBER) 嘗試執行 FOREIGN_BUY (應被拒絕) ---")
res = requests.post(URL, json={'code': '2330', 'type': 'FOREIGN_BUY', 'access_code': 'MEMBER'})
print(res.status_code, res.json())

print("\n--- 測試 3: 管理員 (Ray Cheng) 執行 FOREIGN_BUY (應被允許) ---")
res = requests.post(URL, json={'code': '2330', 'type': 'FOREIGN_BUY', 'access_code': 'Ray Cheng'})
print(res.status_code, res.json().get('result', {}).get('title', 'Unknown'))

print("\n--- 測試 4: 訪客執行回測 RETROLYZE (應被拒絕) ---")
res = requests.post(BT_URL, json={'symbol': '2330', 'start_date': '2023-01-01', 'end_date': '2023-12-31', 'access_code': ''})
print(res.status_code, res.json())

print("\n--- 測試 5: 訪客消耗 25 次額度測試 (一般功能 MA) ---")
session = requests.Session()
count = 0
for i in range(27):
    # 用相同的 IP (預設 requests local loopback)
    r = session.post(URL, json={'code': '2330', 'type': 'MA', 'access_code': ''})
    res_json = r.json()
    if 'error' in res_json:
        print(f"在第 {i+1} 次請求被擋下！回應：", res_json)
        break
    count += 1
print(f"總共成功執行了 {count} 次免費請求")
