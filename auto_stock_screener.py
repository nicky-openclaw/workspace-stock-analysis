#!/usr/bin/env python3
"""
自动化综合选股工具 - 全流程优化版
支持热点板块 + 多指标共振 + 活跃市值过滤
"""

import requests
import time

# ============ 配置 ============

# 预设热门股票池（可根据热点调整）
DEFAULT_POOL = [
    # 船舶军工
    "601890", "600893", "600412", "601989", "600150",
    # AI科技
    "600410", "000988", "300750", "002410", "688111",
    # 机器人
    "002510", "300024", "002047", "002896",
    # 新能源
    "002594", "300014", "002466",
    # 热门股
    "601777", "600984", "601888"
]

# ============ 数据获取 ============

def get_realtime(code):
    """获取实时行情"""
    if code.startswith("6"):
        secid = "1." + code
    else:
        secid = "0." + code
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {"secid": secid, "fields": "f2,f3,f4,f12,f14"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("data") and data["data"].get("diff"):
            d = data["data"]["diff"][0]
            return {"code": d.get("f12"), "name": d.get("f14"), "price": d.get("f2"), "change": d.get("f3"), "amount": d.get("f4")}
    except:
        pass
    return None

def get_kline(code, days=60):
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
        "klt": "101", "fqt": 0,
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
                klines.append({"close": float(parts[2]), "high": float(parts[3]), "low": float(parts[4]), "volume": float(parts[5])})
            return klines
    except:
        pass
    return []

# ============ 指标计算 ============

def calc_zhuanxing(klines):
    """砖形图"""
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
    """B2买点"""
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
    """RSI指标"""
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
    """均线趋势"""
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

def calc_volatility(klines):
    """波动率 - 近期振幅"""
    if len(klines) < 10:
        return 0, ""
    recent = klines[-10:]
    ranges = [(k["high"] - k["low"]) / k["low"] * 100 for k in recent]
    avg_range = sum(ranges) / len(ranges)
    if avg_range > 8:
        return 10, "💥高波动"
    return 0, ""

# ============ 主程序 ============

def analyze(code):
    rt = get_realtime(code)
    klines = get_kline(code, 60)
    if not klines:
        return None
    
    # 过滤：成交额太小的不要
    if rt and rt.get("amount"):
        if rt["amount"] < 500000000:  # 小于5亿
            return None
    
    z_val, z_sig = calc_zhuanxing(klines)
    b2_val, b2_sig = calc_b2(klines)
    rsi_val, rsi_sig = calc_rsi(klines)
    trend_val, trend_sig = calc_trend(klines)
    vol_val, vol_sig = calc_volatility(klines)
    
    total = z_val + b2_val + rsi_val + trend_val + vol_val
    
    signals = [s for s in [z_sig, b2_sig, rsi_sig, trend_sig, vol_sig] if s]
    
    return {
        "code": code,
        "name": rt["name"] if rt else code,
        "price": rt["price"] if rt else klines[-1]["close"],
        "change": rt["change"] if rt else 0,
        "score": total,
        "signals": signals,
        "zhuo": z_val > 0
    }

def main():
    print("=" * 75)
    print("🚀 自动综合选股工具 - 多指标共振")
    print("=" * 75)
    
    results = []
    for code in DEFAULT_POOL:
        print(f"分析 {code}...", end=" ")
        r = analyze(code)
        if r:
            results.append(r)
            print(f"评分:{r['score']}")
        else:
            print("跳过")
        time.sleep(0.3)
    
    # 排序
    results.sort(key=lambda x: (-x["score"], -abs(x.get("change", 0))))
    
    print("\n" + "=" * 75)
    print("🏆 综合评分排名")
    print("=" * 75)
    print(f"{'排名':<4} {'代码':<8} {'名称':<10} {'现价':<8} {'涨跌':<8} {'评分':<6} {'指标信号'}")
    print("-" * 75)
    
    for i, r in enumerate(results[:15], 1):
        change = f"{r.get('change', 0):.2f}%" if r.get('change') else "N/A"
        sigs = " | ".join(r["signals"][:4]) if r["signals"] else "-"
        print(f"{i:<4} {r['code']:<8} {r['name']:<10} {r.get('price','N/A'):<8} {change:<8} {r['score']:<6} {sigs}")
    
    # 重点推荐
    strong = [r for r in results if r["score"] >= 45 or (r["score"] >= 30 and len(r["signals"]) >= 3)]
    
    print("\n" + "=" * 75)
    print("💎 重点关注（评分≥45或多指标共振）")
    print("=" * 75)
    
    for r in strong[:10]:
        print(f"\n⭐ {r['name']}({r['code']}) 评分:{r['score']}")
        for s in r["signals"]:
            print(f"   → {s}")
        if r.get("change"):
            print(f"   今日涨跌: {r['change']:.2f}%")
    
    # 砖形图买点
    zhuo_buy = [r for r in results if "绿转红" in r["signals"]]
    if zhuo_buy:
        print("\n" + "=" * 75)
        print("🎯 砖形图绿转红信号（当日买点）")
        print("=" * 75)
        for r in zhuo_buy:
            print(f"  ⚡ {r['name']}({r['code']}) - {r.get('change','N/A')}")

if __name__ == "__main__":
    main()
