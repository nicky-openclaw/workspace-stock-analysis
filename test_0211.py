#!/usr/bin/env python3
"""
历史选股测试 - 2月11日
用2月11日之前的数据选股，验证2月12日走势
"""

import requests
import time

TEST_DATE = "20260211"  # 用2月11日之前的数据
TEST_DATE_AFTER = "20260212"  # 验证这一天

# 测试股票池
TEST_POOL = [
    "601890", "600893", "600410", "601777", "600984",
    "000988", "002510", "002047", "002896", "600150",
    "600412", "601989", "600038", "600705"
]

def get_kline(code, end_date, days=30):
    if code.startswith("6"):
        secid = "1." + code
    else:
        secid = "0." + code
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101", "fqt": 0,
        "beg": "20260101",
        "end": end_date,
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
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": float(parts[5])
                })
            return klines
    except:
        pass
    return []

def calc_zhuanxing(klines):
    if len(klines) < 10:
        return 0, ""
    results = []
    for i in range(5, len(klines)):
        c = klines[i]["close"]
        h4 = max([k["high"] for k in klines[max(0,i-3):i+1]])
        l4 = min([k["low"] for k in klines[max(0,i-3):i+1]])
        var3 = (c - l4) / (h4 - l4) * 100 if h4 != l4 else 50
        var6 = var3 - 90
        zhuan = max(0, var6 - 4) if var6 > 4 else 0
        results.append(zhuan)
    if len(results) >= 2:
        if results[-1] > 0 and results[-2] == 0:
            return results[-1], "🟢绿转红"
        elif results[-1] > 0:
            return results[-1], "🔴红持"
    return results[-1] if results else 0, ""

def calc_b2(klines):
    if len(klines) < 20:
        return 0, ""
    recent = klines[-5:]
    vols = [k["volume"] for k in recent]
    vol_ratio = vols[-1] / (sum(vols[:-1]) / 4) if sum(vols[:-1]) > 0 else 0
    change = (recent[-1]["close"] - recent[-2]["close"]) / recent[-2]["close"] * 100
    peak = max([k["close"] for k in recent[:-1]])
    if vol_ratio > 1.5 and change > 3.95 and recent[-1]["close"] > peak:
        return 30, "📈B2突破"
    elif vol_ratio > 1.3 and change > 2:
        return 15, "📊放量涨"
    return 0, ""

def calc_trend(klines):
    if len(klines) < 20:
        return 0, ""
    ma5 = sum([k["close"] for k in klines[-5:]]) / 5
    ma10 = sum([k["close"] for k in klines[-10:]]) / 10
    ma20 = sum([k["close"] for k in klines[-20:]]) / 20
    if ma5 > ma10 > ma20:
        return 15, "📈多头"
    elif ma5 > ma10:
        return 5, "📊短期"
    return 0, ""

def get_price(code, date):
    if code.startswith("6"):
        secid = "1." + code
    else:
        secid = "0." + code
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f2,f3",
        "fields2": "f51,f52",
        "klt": "101", "fqt": 0,
        "beg": date,
        "end": date,
        "lmt": 1
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("data") and data["data"].get("klines"):
            parts = data["data"]["klines"][0].split(",")
            return float(parts[2]), float(parts[8])
    except:
        pass
    return None, None

def main():
    print("=" * 75)
    print("📅 历史选股测试 - 2月11日")
    print("=" * 75)
    print(f"用2月11日之前的数据选股，验证2月12日走势")
    
    results = []
    for code in TEST_POOL:
        print(f"分析 {code}...", end=" ")
        
        # 用2月11日之前的数据
        klines = get_kline(code, TEST_DATE, 30)
        if not klines or len(klines) < 20:
            print("数据不足")
            continue
        
        z_val, z_sig = calc_zhuanxing(klines)
        b2_val, b2_sig = calc_b2(klines)
        trend_val, trend_sig = calc_trend(klines)
        
        total = z_val + b2_val + trend_val
        signals = [s for s in [z_sig, b2_sig, trend_sig] if s]
        
        if total > 0:
            results.append({
                "code": code,
                "score": total,
                "signals": signals,
                "close_11": klines[-1]["close"]
            })
            print(f"评分:{total}")
    
    # 排序
    results.sort(key=lambda x: -x["score"])
    
    print("\n" + "=" * 75)
    print("📊 2月11日选股结果")
    print("=" * 75)
    
    for r in results:
        print(f"{r['code']}: 评分{r['score']} | {' | '.join(r['signals'])}")
    
    # 验证2月12日
    print("\n" + "=" * 75)
    print("🔍 2月12日验证")
    print("=" * 75)
    
    success = 0
    for r in results[:5]:
        price, change = get_price(r["code"], TEST_DATE_AFTER)
        if price:
            status = "✅" if change > 0 else "❌"
            print(f"{r['code']}: {price:.2f} ({change:+.2f}%) {status}")
            if change > 0:
                success += 1
    
    print(f"\n胜率: {success}/{len(results[:5])} = {success/len(results[:5])*100:.0f}%")

if __name__ == "__main__":
    main()
