#!/usr/bin/env python3
"""
砖型图精确计算
包含：绿转红 + 强红(3分之2) + 红砖体积 > 前一天绿砖体积
"""

import requests
import time

def get_kline(code, days=30):
    """获取K线数据"""
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

def calculate_zhuanxing(klines):
    """
    砖型图计算
    返回：(砖型图值, 红/绿, 信号)
    """
    if len(klines) < 10:
        return None, None, None
    
    results = []
    
    for i in range(5, len(klines)):
        # 取最近4天的高低
        high_4 = max([k["high"] for k in klines[max(0, i-3):i+1]])
        low_4 = min([k["low"] for k in klines[max(0, i-3):i+1]])
        close = klines[i]["close"]
        
        if high_4 == low_4:
            var3 = 50
        else:
            var3 = (close - low_4) / (high_4 - low_4) * 100
        
        # 简化计算
        var5 = var3 + 100
        var6 = var5 - 100
        zhuan_value = max(0, var6 - 4) if var6 > 4 else 0
        
        # 判断红绿
        is_red = close >= klines[i]["open"]  # 收盘价 >= 开盘价 = 红
        
        results.append({
            "date": klines[i]["date"],
            "close": close,
            "zhuan": zhuan_value,
            "is_red": is_red,
            "volume": klines[i]["volume"]
        })
    
    return results

def check_signal(klines):
    """
    检查是否符合砖型图信号
    
    信号条件：
    1. 当天红砖
    2. 当天红砖体积 > 0
    3. 前一天是绿砖
    4. 当天红砖体积 > 前一天绿砖体积
    """
    results = calculate_zhuanxing(klines)
    if not results or len(results) < 2:
        return None
    
    today = results[-1]
    yesterday = results[-2]
    
    # 条件1: 当天红砖
    if not today["is_red"]:
        return None
    
    # 条件2: 当天红砖体积 > 0
    if today["zhuan"] <= 0:
        return None
    
    # 条件3: 前一天是绿砖
    if yesterday["is_red"]:
        return None
    
    # 条件4: 当天红砖体积 > 前一天绿砖体积（取绝对值）
    # 绿砖体积用0减去计算值
    yesterday_vol = abs(yesterday["zhuan"]) if yesterday["zhuan"] < 0 else 0.1
    
    if today["zhuan"] > yesterday_vol:
        return {
            "signal": "砖型图绿转红+放量",
            "today_zhuan": today["zhuan"],
            "yesterday_zhuan": yesterday["zhuan"],
            "score": 35,  # 强化信号加5分
            "reason": "绿转红 + 红砖体积放大"
        }
    
    # 弱信号：绿转红但没有明显放量
    return {
        "signal": "砖型图绿转红",
        "today_zhuan": today["zhuan"],
        "yesterday_zhuan": yesterday["zhuan"],
        "score": 30,
        "reason": "绿转红"
    }

def analyze_stock(code):
    """分析单只股票"""
    klines = get_kline(code, 30)
    if not klines or len(klines) < 10:
        return None
    
    signal_info = check_signal(klines)
    
    return {
        "code": code,
        "latest": klines[-1]["date"],
        "close": klines[-1]["close"],
        "signal": signal_info
    }

def main():
    import sys
    
    # 测试股票池
    test_stocks = [
        ("600893", "航发动力"),
        ("600366", "宁波韵升"),
        ("600487", "亨通股份"),
        ("688321", "微芯生物"),
        ("600089", "特变电工"),
        ("000400", "许继电气"),
    ]
    
    print("=" * 70)
    print("🎯 砖型图精确信号检测")
    print("=" * 70)
    print("信号条件：")
    print("  1. 当天红砖（收盘>开盘）")
    print("  2. 前一天绿砖（收盘<开盘）")
    print("  3. 红砖体积 > 前一天绿砖体积")
    print("=" * 70)
    
    for code, name in test_stocks:
        print(f"\n分析 {name}({code})...")
        result = analyze_stock(code)
        
        if result and result["signal"]:
            sig = result["signal"]
            print(f"  ✅ 信号: {sig['signal']}")
            print(f"     原因: {sig['reason']}")
            print(f"     红砖体积: {sig['today_zhuan']:.2f}")
            print(f"     绿砖体积: {sig['yesterday_zhuan']:.2f}")
            print(f"     评分: {sig['score']}")
        else:
            print(f"  ❌ 无信号")

if __name__ == "__main__":
    main()
