#!/usr/bin/env python3
"""
B1选股 Step2: 获取股票的120日K线数据
- 新浪API: 深圳股票
- 东方财富API: 上海股票 + 新股
"""
import json
import urllib.request
import urllib.error
import ssl
import time
import os
import random

# 读取股票清单
input_file = "/Users/nicky/.openclaw/workspace-stock-analysis/b1_output/b1_stocks.json"
output_file = "/Users/nicky/.openclaw/workspace-stock-analysis/b1_output/b1_kline.json"

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

stocks = data['stocks']
print(f"共读取 {len(stocks)} 只股票")

# 统计
success_count = 0
fail_count = 0
skip_count = 0
errors = []

# 结果存储
results = {
    "total": 0,
    "date": "2026-03-09",
    "stocks": []
}

# 创建SSL上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def get_kline_sina(symbol):
    """使用新浪API获取K线"""
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, context=ssl_context, timeout=15) as response:
            content = response.read().decode('utf-8')
        
        kline_data = json.loads(content)
        if isinstance(kline_data, list) and len(kline_data) > 0:
            return kline_data[:120]
    except Exception as e:
        pass
    return None

def get_kline_eastmoney(prefix, code):
    """使用东方财富API获取K线"""
    # secid: 0.XXXXXX(上海) 或 1.XXXXXX(深圳)
    if prefix == 'sh':
        secid = f"0.{code}"
    else:
        secid = f"1.{code}"
    
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20260309&lmt=120"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, context=ssl_context, timeout=15) as response:
            content = response.read().decode('utf-8')
        
        json_data = json.loads(content)
        if json_data.get('data') and json_data['data'].get('klines'):
            klines = []
            for item in json_data['data']['klines']:
                parts = item.split(',')
                klines.append({
                    "date": parts[0],
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": float(parts[5])
                })
            return klines[:120]
    except Exception as e:
        pass
    return None

# 遍历每只股票
for i, stock in enumerate(stocks):
    code = stock['code']
    name = stock['name']
    prefix = stock['prefix']
    
    # 跳过北交所股票（代码以8开头且6位数字）
    if code.startswith('8') and len(code) == 6:
        skip_count += 1
        print(f"[跳过] {code} {name} (北交所)")
        continue
    
    symbol = f"{prefix}{code}"
    kline_data = None
    
    # 优先使用新浪API（深市）
    if prefix == 'sz':
        kline_data = get_kline_sina(symbol)
    
    # 如果新浪失败，使用东方财富API
    if kline_data is None:
        kline_data = get_kline_eastmoney(prefix, code)
    
    if kline_data and len(kline_data) > 0:
        # 东方财富直接返回格式化数据
        if isinstance(kline_data[0], dict) and 'day' in kline_data[0]:
            klines = []
            for item in kline_data:
                klines.append({
                    "date": item.get('day', ''),
                    "open": float(item.get('open', 0)),
                    "close": float(item.get('close', 0)),
                    "high": float(item.get('high', 0)),
                    "low": float(item.get('low', 0)),
                    "volume": float(item.get('volume', 0))
                })
            kline_data = klines
        
        results['stocks'].append({
            "code": code,
            "name": name,
            "prefix": prefix,
            "klines": kline_data
        })
        success_count += 1
        
        if success_count % 30 == 0:
            print(f"[进度] 已成功获取 {success_count} 只")
    else:
        fail_count += 1
        errors.append(f"{code} {name}")
        print(f"[失败] {code} {name}")
    
    # 避免请求过快
    time.sleep(0.1 + random.uniform(0, 0.1))

# 保存结果
results['total'] = len(results['stocks'])
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# 输出统计
print(f"\n========== 任务完成 ==========")
print(f"成功: {success_count}")
print(f"失败: {fail_count}")
print(f"跳过: {skip_count}")
print(f"总计: {len(stocks)}")
print(f"\n结果已保存至: {output_file}")

if errors:
    print(f"\n失败列表(共{len(errors)}只):")
    for err in errors[:15]:
        print(f"  - {err}")
