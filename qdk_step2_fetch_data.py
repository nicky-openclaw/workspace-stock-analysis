#!/usr/bin/env python3
"""
启动K选股流程 - 完整执行脚本
Step 2: 并行获取数据（修复版）
"""

import akshare as ak
import requests
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time

# 股票列表（43只）
STOCKS_RAW = [
    ("688316", "青云科技-U"),
    ("688229", "博睿数据"),
    ("688158", "优刻得-W"),
    ("603138", "海量数据"),
    ("601339", "百隆东方"),
    ("600851", "海欣股份"),
    ("301606", "绿联科技"),
    ("301396", "宏景科技"),
    ("300846", "首都在线"),
    ("300571", "平治信息"),
    ("300369", "绿盟科技"),
    ("300352", "北信源"),
    ("300166", "东方国信"),
    ("300113", "顺网科技"),
    ("300017", "网宿科技"),
    ("002930", "宏川智慧"),
    ("002730", "电光科技"),
    ("002229", "鸿博股份"),
    ("000973", "佛塑科技"),
    ("688207", "格灵深瞳"),
    ("688052", "纳芯微"),
    ("688023", "安恒信息"),
    ("603876", "鼎胜新材"),
    ("600845", "宝信软件"),
    ("301358", "湖南裕能"),
    ("300608", "思特奇"),
    ("300226", "上海钢联"),
    ("300170", "汉得信息"),
    ("002812", "恩捷股份"),
    ("002575", "群兴玩具"),
    ("002151", "北斗星通"),
    ("001203", "大中矿业"),
    ("000066", "中国长城"),
    ("920670", "数字人"),
    ("688599", "天合光能"),
    ("688327", "云从科技-UW"),
    ("301292", "海科新源"),
    ("300921", "南凌科技"),
    ("300738", "奥飞数据"),
    ("300624", "万兴科技"),
    ("300454", "深信服"),
    ("603881", "数据港"),
    ("601360", "三六零"),
    ("300383", "光环新网"),
]

def convert_stock_code(code):
    """转换股票代码格式"""
    code = code.strip()
    if code.startswith("688"):
        return f"sh{code}"
    elif code.startswith("6"):
        return f"sh{code}"
    elif code.startswith("0") or code.startswith("3"):
        return f"sz{code}"
    elif code.startswith("9"):
        return f"bj{code}"
    return code

# 转换股票代码
STOCKS_FORMATTED = [(convert_stock_code(code), name) for code, name in STOCKS_RAW]
print(f"股票数量: {len(STOCKS_FORMATTED)}")

def get_kline_akshare(stock_code):
    """获取120日K线数据（不复权）"""
    from datetime import datetime, timedelta
    today = datetime.now()
    start = today - timedelta(days=180)  # 取180天确保有足够数据算MA114
    start_date = start.strftime("%Y%m%d")
    end_date = today.strftime("%Y%m%d")
    try:
        # 不复权数据（adjust=""），动态日期
        df = ak.stock_zh_a_hist_tx(
            symbol=stock_code,
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )
        if df is not None and len(df) > 0:
            return stock_code, df
    except Exception as e:
        print(f"K线获取失败 {stock_code}: {e}")
    return stock_code, None

def get_realtime_curl(stock_code):
    """用curl获取实时数据"""
    try:
        url = f"https://qt.gtimg.cn/q={stock_code}"
        resp = requests.get(url, timeout=5)
        text = resp.text
        if text and text != "":
            # 解析返回数据
            parts = text.split("~")
            if len(parts) > 32:
                name = parts[1]
                price = float(parts[3])  # 现价
                # 修复：使用字段32作为涨跌幅，而不是自己计算
                change_pct = float(parts[32])  # 涨跌幅(%)
                yesterday = float(parts[4])  # 昨收价
                open_price = float(parts[5])  # 开盘
                volume = float(parts[6])  # 成交量
                high = float(parts[33])  # 最高
                low = float(parts[34])  # 最低
                return stock_code, {
                    "name": name,
                    "price": price,
                    "yesterday": yesterday,
                    "open": open_price,
                    "volume": volume,
                    "high": high,
                    "low": low,
                    "change_pct": change_pct  # 使用API返回的真实涨跌幅
                }
    except Exception as e:
        print(f"实时数据获取失败 {stock_code}: {e}")
    return stock_code, None

# 并行获取数据
print("\n=== Step 2: 并行获取数据 ===")

kline_data = {}
realtime_data = {}

# 并行获取K线数据
print("获取K线数据...")
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(get_kline_akshare, code): code for code, _ in STOCKS_FORMATTED}
    for future in as_completed(futures):
        stock_code, df = future.result()
        if df is not None:
            kline_data[stock_code] = df

print(f"K线数据获取成功: {len(kline_data)}/{len(STOCKS_FORMATTED)}")

# 并行获取实时数据
print("获取实时数据...")
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(get_realtime_curl, code): code for code, _ in STOCKS_FORMATTED}
    for future in as_completed(futures):
        stock_code, data = future.result()
        if data is not None:
            realtime_data[stock_code] = data

print(f"实时数据获取成功: {len(realtime_data)}/{len(STOCKS_FORMATTED)}")

# 合并数据，计算涨幅
print("\n=== 合并数据 ===")
merged_data = {}

for stock_code, name in STOCKS_FORMATTED:
    kline = kline_data.get(stock_code)
    realtime = realtime_data.get(stock_code)
    
    if kline is not None and realtime is not None:
        # K线最新收盘价作为昨日收盘
        last_close = kline.iloc[-1]['close']
        
        # 实时现价作为今日收盘
        today_close = realtime['price']
        
        # 修复：直接使用API返回的涨跌幅（字段32），更准确
        change_pct = realtime.get('change_pct', (today_close - last_close) / last_close * 100)
        
        merged_data[stock_code] = {
            "name": name,
            "yesterday_close": last_close,
            "today_close": today_close,
            "change_pct": change_pct,
            "open": realtime['open'],
            "high": realtime['high'],
            "low": realtime['low'],
            "volume": realtime['volume'],
            "kline": kline.tail(30).to_dict('records')  # 保存最近30日K线
        }

print(f"合并数据成功: {len(merged_data)}/{len(STOCKS_FORMATTED)}")

# 保存到文件
output_path = "qdk_output/qdk_kline.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=2, default=str)

print(f"\n数据已保存到: {output_path}")
print(f"总计: {len(merged_data)} 只股票")
