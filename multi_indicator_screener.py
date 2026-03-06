#!/usr/bin/env python3
"""
综合选股工具 - 多指标共振
整合砖形图 + B2 + 动能指标 + 趋势
"""

import requests
import time

def get_kline(secid, days=60):
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "0",
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

def get_realtime(code):
    if code.startswith("6"):
        secid = "1." + code
    else:
        secid = "0." + code
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {"secid": secid, "fields": "f2,f3,f4,f12,f13,f14"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("data") and data["data"].get("diff"):
            d = data["data"]["diff"][0]
            return {"code": d.get("f12", ""), "name": d.get("f14", ""), "price": d.get("f2"), "change": d.get("f3")}
    except:
        pass
    return None

def calc_zhuanxing(klines):
    if len(klines) < 10:
        return {"value": 0, "signal": "", "score": 0}
    results = []
    for i in range(5, len(klines)):
        close = klines[i]["close"]
        high_4 = max([k["high"] for k in klines[max(0,i-3):i+1]])
        low_4 = min([k["low"] for k in klines[max(0,i-3):i+1]])
        if high_4 == low_4:
            var3 = 50
        else:
            var3 = (close - low_4) / (high_4 - low_4) * 100
        var5 = var3 + 100
        var6 = var5 - 100
        zhuan = max(0, var6 - 4)
        results.append(zhuan)
    if len(results) < 2:
        return {"value": results[-1] if results else 0, "signal": "", "score": 0}
    signal = ""
    score = 0
    if results[-1] > 0 and results[-2] == 0:
        signal = "绿转红"
        score = 30
    elif results[-1] > 0:
        signal = "红持"
        score = 15
    return {"value": results[-1], "signal": signal, "score": score}

def calc_b2(klines):
    if len(klines) < 20:
        return {"signal": "", "score": 0}
    recent = klines[-5:]
    volumes = [k["volume"] for k in recent]
    vol_ratio = volumes[-1] / (sum(volumes[:-1]) / 4) if sum(volumes[:-1]) > 0 else 0
    change_pct = (recent[-1]["close"] - recent[-2]["close"]) / recent[-2]["close"] * 100
    peak = max([k["close"] for k in recent[:-1]])
    breakout = recent[-1]["close"] > peak
    signal = ""
    score = 0
    if vol_ratio > 1.5 and change_pct > 3.95 and breakout:
        signal = "B2突破"
        score = 25
    elif vol_ratio > 1.3 and change_pct > 2:
        signal = "放量上涨"
        score = 10
    return {"signal": signal, "score": score, "vol_ratio": round(vol_ratio, 2), "change": round(change_pct, 2)}

def calc_rsi(klines):
    if len(klines) < 14:
        return {"signal": "", "score": 0}
    closes = [k["close"] for k in klines[-14:]]
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    avg_gain = sum(gains) / 14 if gains else 0
    avg_loss = sum(losses) / 14 if losses else 0
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    signal = ""
    score = 0
    if rsi < 30:
        signal = f"RSI超卖({int(rsi)})"
        score = 20
    elif rsi < 50:
        signal = f"RSI低位({int(rsi)})"
        score = 10
    return {"signal": signal, "score": score, "rsi": round(rsi, 1)}

def calc_single_needle(klines):
    if len(klines) < 5:
        return {"signal": "", "score": 0}
    k = klines[-1]
    body = k["close"] - k["open"]
    lower_shadow = min(k["open"], k["close"]) - k["low"]
    if lower_shadow > abs(body) * 2 and lower_shadow / (k["high"] - k["low"]) > 0.5:
        return {"signal": "单针下探", "score": 15}
    return {"signal": "", "score": 0}

def calc_trend(klines):
    if len(klines) < 20:
        return {"signal": "", "score": 0}
    ma5 = sum([k["close"] for k in klines[-5:]]) / 5
    ma10 = sum([k["close"] for k in klines[-10:]]) / 10
    ma20 = sum([k["close"] for k in klines[-20:]]) / 20
    if ma5 > ma10 > ma20:
        return {"signal": "多头趋势", "score": 15}
    elif ma5 > ma10:
        return {"signal": "短期多头", "score": 5}
    return {"signal": "", "score": 0}

def analyze_stock(code):
    if code.startswith("6"):
        secid = "1." + code
    elif code.startswith("0") or code.startswith("3"):
        secid = "0." + code
    else:
        secid = "0." + code
    klines = get_kline(secid, 60)
    realtime = get_realtime(code)
    if not klines:
        return None
    zhuanxing = calc_zhuanxing(klines)
    b2 = calc_b2(klines)
    rsi = calc_rsi(klines)
    single_needle = calc_single_needle(klines)
    trend = calc_trend(klines)
    total_score = zhuanxing["score"] + b2["score"] + rsi["score"] + single_needle["score"] + trend["score"]
    signals = []
    if zhuanxing["signal"]:
        signals.append(zhuanxing["signal"])
    if b2["signal"]:
        signals.append(b2["signal"])
    if rsi["signal"]:
        signals.append(rsi["signal"])
    if single_needle["signal"]:
        signals.append(single_needle["signal"])
    if trend["signal"]:
        signals.append(trend["signal"])
    return {
        "code": code,
        "name": realtime["name"] if realtime else code,
        "price": realtime["price"] if realtime else klines[-1]["close"],
        "change": realtime["change"] if realtime else 0,
        "signals": signals,
        "score": total_score
    }

def main():
    print("=" * 70)
    print("🎯 综合选股工具 - 多指标共振")
    print("=" * 70)
    test_stocks = ["601890", "600893", "600410", "601777", "600984", "000988", "002510"]
    results = []
    for code in test_stocks:
        print(f"\n分析 {code}...", end=" ")
        result = analyze_stock(code)
        if result:
            results.append(result)
            print(f"得分: {result['score']}")
        time.sleep(0.3)
    results.sort(key=lambda x: x["score"], reverse=True)
    print("\n" + "=" * 70)
    print("📊 综合评分排名")
    print("=" * 70)
    print(f"{'排名':<4} {'代码':<8} {'名称':<10} {'评分':<6} {'信号'}")
    print("-" * 70)
    for i, r in enumerate(results, 1):
        signals = " | ".join(r["signals"][:3]) if r["signals"] else "无信号"
        print(f"{i:<4} {r['code']:<8} {r['name']:<10} {r['score']:<6} {signals}")
    print("\n" + "=" * 70)
    print("💡 重点关注（评分>30或多指标共振）")
    print("=" * 70)
    for r in results:
        if r["score"] >= 30 or len(r["signals"]) >= 3:
            print(f"\n⭐ {r['name']}({r['code']}) 评分: {r['score']}")
            for s in r["signals"]:
                print(f"   - {s}")

if __name__ == "__main__":
    main()
