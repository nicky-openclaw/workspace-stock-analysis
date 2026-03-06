#!/usr/bin/env python3
"""
砖型图精确计算 - v2.0
包含核心因子：
1. 绿转红（砖型图从绿变红）
2. 强红（3分之2以上）
3. 红砖体积 > 前一天绿砖体积
"""

import requests
import time

def get_klines(code, days=60):
    if code.startswith("6"):
        secid = "1." + code
    else:
        secid = "0." + code
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": 0,
        "beg": "20250101",
        "end": time.strftime("%Y%m%d"),
        "lmt": str(days)
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("data") and data["data"].get("klines"):
            klines = []
            for line in data["data"]["klines"]:
                parts = line.split(",")
                klines.append({
                    "date": parts[0],
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": float(parts[5])
                })
            return klines
    except:
        pass
    return []

def calculate_zhuanxing_v2(klines):
    """
    砖型图精确计算 v2.0
    返回：(砖型图值, 是否红砖)
    """
    if len(klines) < 10:
        return [], False
    
    results = []
    
    for i in range(4, len(klines)):
        # 4日区间
        high_4 = max([k["high"] for k in klines[max(0, i-3):i+1]])
        low_4 = min([k["low"] for k in klines[max(0, i-3):i+1]])
        close = klines[i]["close"]
        
        if high_4 == low_4:
            var1a, var3a = 0, 50
        else:
            # VAR1A = (HHV - CLOSE) / (HHV - LLV) * 100 - 90
            var1a = ((high_4 - close) / (high_4 - low_4)) * 100 - 90
            # VAR3A = (CLOSE - LLV) / (HHV - LLV) * 100
            var3a = ((close - low_4) / (high_4 - low_4)) * 100
        
        # VAR6A = (VAR3A + 100) - (VAR1A + 100) = VAR3A - VAR1A
        var6a = var3a - var1a
        
        # 砖型图 = IF(VAR6A > 4, VAR6A - 4, 0)
        zhuan_value = max(0, var6a - 4)
        
        # 红/绿判断
        is_red = close >= klines[i]["open"]
        
        results.append({
            "date": klines[i]["date"],
            "close": close,
            "zhuan": zhuan_value,
            "is_red": is_red,
            "volume": klines[i]["volume"]
        })
    
    return results

def check_buy_signal(klines):
    """
    检查买入信号
    
    核心因子（来自260220笔记+用户补充）：
    1. 当天红砖（收盘 > 开盘）
    2. 前一天绿砖（收盘 < 开盘）  
    3. 红砖体积 > 前一天绿砖体积 ← 用户发现的规律
    4. 强红：红砖体积 > 某个阈值（可选）
    """
    results = calculate_zhuanxing_v2(klines)
    if not results or len(results) < 2:
        return None
    
    today = results[-1]
    yesterday = results[-2]
    
    # 因子1: 当天红砖
    if not today["is_red"]:
        return None
    
    # 因子2: 前一天绿砖
    if yesterday["is_red"]:
        return None
    
    # 因子3: 红砖体积 > 前一天绿砖体积
    red_vol = today["zhuan"]
    green_vol = abs(yesterday["zhuan"])  # 绿砖用绝对值
    
    if red_vol <= green_vol:
        return None
    
    # 信号强度
    score = 35  # 基础分
    
    # 强红加成（红砖体积 > 100）
    if red_vol > 100:
        score += 10
    
    return {
        "code": klines[-1]["date"],
        "signal": "砖型图绿转红+放量",
        "today": {
            "date": today["date"],
            "red_vol": round(red_vol, 1),
            "close": today["close"]
        },
        "yesterday": {
            "date": yesterday["date"],
            "green_vol": round(green_vol, 1)
        },
        "score": score,
        "reason": "绿转红 + 红砖体积放大"
    }

def analyze_stock(code):
    klines = get_klines(code, 60)
    if not klines or len(klines) < 10:
        return None
    
    signal = check_buy_signal(klines)
    
    return {
        "code": code,
        "date": klines[-1]["date"],
        "close": klines[-1]["close"],
        "signal": signal
    }

def main():
    # 测试股票池
    test_stocks = [
        ("600893", "航发动力"),
        ("600366", "宁波韵升"),
        ("600487", "亨通股份"),
        ("688321", "微芯生物"),
        ("600089", "特变电工"),
    ]
    
    print("=" * 70)
    print("🎯 砖型图精确信号检测 v2.0")
    print("=" * 70)
    print("信号条件：")
    print("  1. 当天红砖（收盘 > 开盘）")
    print("  2. 前一天绿砖（收盘 < 开盘）")
    print("  3. 红砖体积 > 前一天绿砖体积 ← 核心因子")
    print("=" * 70)
    
    results = []
    for code, name in test_stocks:
        result = analyze_stock(code)
        if result and result["signal"]:
            sig = result["signal"]
            results.append({
                "name": name,
                "code": code,
                "signal": sig
            })
            print(f"\n✅ {name}({code})")
            print(f"   日期: {sig['today']['date']}")
            print(f"   红砖体积: {sig['today']['red_vol']}")
            print(f"   绿砖体积: {sig['yesterday']['green_vol']}")
            print(f"   评分: {sig['score']}")
        else:
            print(f"\n❌ {name}({code}) - 无信号")
    
    if not results:
        print("\n⚠️ 当前无信号（可能是非交易时段）")

if __name__ == "__main__":
    main()
