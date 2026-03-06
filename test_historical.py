#!/usr/bin/env python3
"""
历史选股测试 - 使用指定日期的数据
用于验证策略有效性
"""

import requests
import time
import sys

# 测试截止日期
TEST_DATE = "20260213"  # 2月13日

# 测试股票池
TEST_POOL = [
    "601890", "600893", "600410", "601777", "600984",
    "000988", "002510", "002047", "002896", "600150"
]

def get_kline(code, days=60):
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
        "beg": "20250101",
        "end": TEST_DATE,
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

def calc_rsi(klines):
    if len(klines) < 14:
        return 0, ""
    closes = [k["close"] for k in klines[-14:]]
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(diff if diff > 0 else 0)
        losses.append(abs(diff) if diff < 0 else 0)
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14
    rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 100
    if rsi < 30:
        return 20, f"⚡RSI超卖({int(rsi)})"
    elif rsi < 50:
        return 10, f"📉RSI低位({int(rsi)})"
    return 0, ""

def calc_trend(klines):
    if len(klines) < 20:
        return 0, ""
    ma5 = sum([k["close"] for k in klines[-5:]]) / 5
    ma10 = sum([k["close"] for k in klines[-10:]]) / 10
    ma20 = sum([k["close"] for k in klines[-20:]]) / 20
    if ma5 > ma10 > ma20:
        return 15, "📈多头趋势"
    elif ma5 > ma10:
        return 5, "📊短期多头"
    return 0, ""

def get_close_price(code):
    """获取2月13日收盘价"""
    if code.startswith("6"):
        secid = "1." + code
    else:
        secid = "0." + code
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f2",
        "fields2": "f51",
        "klt": "101", "fqt": 0,
        "beg": TEST_DATE,
        "end": TEST_DATE,
        "lmt": 1
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("data") and data["data"].get("klines"):
            return float(data["data"]["klines"][0].split(",")[2])
    except:
        pass
    return None

def main():
    print("=" * 75)
    print(f"📅 历史选股测试 - 测试日期: 2月13日")
    print("=" * 75)
    
    results = []
    for code in TEST_POOL:
        print(f"分析 {code}...", end=" ")
        
        klines = get_kline(code, 60)
        if not klines or len(klines) < 20:
            print("数据不足")
            continue
        
        # 2月13日收盘价
        close_price = get_close_price(code)
        
        z_val, z_sig = calc_zhuanxing(klines)
        b2_val, b2_sig = calc_b2(klines)
        rsi_val, rsi_sig = calc_rsi(klines)
        trend_val, trend_sig = calc_trend(klines)
        
        total = z_val + b2_val + rsi_val + trend_val
        
        signals = [s for s in [z_sig, b2_sig, rsi_sig, trend_sig] if s]
        
        if total > 0:
            results.append({
                "code": code,
                "close": close_price,
                "score": total,
                "signals": signals
            })
            print(f"评分:{total}")
        else:
            print("无信号")
    
    # 排序
    results.sort(key=lambda x: -x["score"])
    
    print("\n" + "=" * 75)
    print(f"📊 2月13日选股结果")
    print("=" * 75)
    print(f"{'排名':<4} {'代码':<8} {'收盘价':<10} {'评分':<6} {'信号'}")
    print("-" * 75)
    
    for i, r in enumerate(results, 1):
        sigs = " | ".join(r["signals"])
        close_str = f"{r['close']:.2f}" if r.get("close") else "N/A"
        print(f"{i:<4} {r['code']:<8} {close_str:<10} {r['score']:<6} {sigs}")
    
    # 推荐的股票
    print("\n" + "=" * 75)
    print("🎯 2月13日推荐股票（评分>40）")
    print("=" * 75)
    
    for r in results:
        if r["score"] >= 40:
            print(f"\n⭐ {r['code']} 评分:{r['score']}")
            for s in r["signals"]:
                print(f"   → {s}")
            
            # 知识库案例匹配
            if "绿转红" in r["signals"] or "B2突破" in r["signals"]:
                print("   📚 知识库匹配:")
                print("      • B2买点的核心是寻找突破后能继续上涨的股票")
                print("      • 高值只是辅助参考，关键是形态和量能")
                print("      • 超短线寻找转折点的爆发力")
    
    # 验证：2月13日买了这些股票，2月14日会怎样？
    print("\n" + "=" * 75)
    print("🔍 2月14日验证（如果有的话）")
    print("=" * 75)
    
    for r in results[:3]:
        code = r["code"]
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
            "beg": "20260214",
            "end": "20260214",
            "lmt": 1
        }
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            if data.get("data") and data["data"].get("klines"):
                parts = data["data"]["klines"][0].split(",")
                close_14 = float(parts[2])
                change_14 = float(parts[8])
                print(f"{r['code']}: 2月14日 {close_14:.2f} ({change_14:+.2f}%)")
        except:
            pass

if __name__ == "__main__":
    main()
