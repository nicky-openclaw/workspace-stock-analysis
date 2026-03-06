#!/usr/bin/env python3
"""
盘中实时监控工具
10:00 早盘监控 - 强势股筛选
14:00 午后监控 - 下午启动信号
14:50 收盘监控 - 信号确认
"""

import requests
import time

# ============ 板块资金流 ============

def get_sector_flow():
    """获取板块资金流"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1, "pz": 5, "po": 1, "np": 1,
        "fltt": 2, "invt": 2, "fid": "f3",
        "fs": "m:90+t:2",
        "fields": "f1,f2,f3,f4,f12,f13,f14",
        "_": int(time.time() * 1000)
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        sectors = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"][:5]:
                sectors.append({
                    "name": item.get("f14"),
                    "change": item.get("f3", 0)
                })
        return sectors
    except:
        return []

# ============ 实时涨跌幅 ============

def get_realtime_stocks():
    """获取实时涨跌幅排行"""
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = {
        "fltt": 2,
        "fields": "f1,f2,f3,f4,f7,f8,f9,f10,f12,f13,f14",
        "secids": "1.000001,0.399001",  # 上证+深证
        "_": int(time.time() * 1000)
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("data") and data["data"].get("diff"):
            return data["data"]["diff"]
    except:
        pass
    return []

def get_top_gainers(limit=10):
    """获取涨幅前10"""
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = {
        "fltt": 2,
        "fields": "f2,f3,f4,f7,f12,f14",
        "secids": "",
        "ut": "7eea3edcaed734bea779c7096df40b1b",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "pn": 1,
        "pz": limit,
        "po": 1,
        "np": 1,
        "_": int(time.time() * 1000)
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        stocks = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"][:limit]:
                change = item.get("f3", 0)
                amount = item.get("f4", 0)
                # 过滤：涨幅>5% + 成交额>3亿
                if change > 5 and amount > 300000000:
                    stocks.append({
                        "code": item.get("f12"),
                        "name": item.get("f14"),
                        "price": item.get("f2"),
                        "change": change,
                        "amount": amount / 100000000
                    })
        return stocks
    except:
        return []

# ============ 个股实时数据 ============

def get_stock_realtime(code):
    """获取个股实时数据"""
    if code.startswith("6"):
        secid = "1." + code
    else:
        secid = "0." + code
    
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "secid": secid,
        "fields": "f2,f3,f4,f5,f7,f8,f9,f10,f12,f13,f14"
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("data") and data["data"].get("diff"):
            d = data["data"]["diff"][0]
            return {
                "code": d.get("f12"),
                "name": d.get("f14"),
                "price": d.get("f2"),
                "change": d.get("f3"),
                "amount": d.get("f4"),
                "vol": d.get("f5"),
                "high": d.get("f7"),
                "low": d.get("f8"),
                "open": d.get("f9")
            }
    except:
        pass
    return None

# ============ K线数据 ============

def get_kline(code, days=20):
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
                klines.append({
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "volume": float(parts[5])
                })
            return klines
    except:
        pass
    return []

# ============ 盘中信号计算 ============

def calc_zhuanxing(klines):
    """砖形图 - 简化版"""
    if len(klines) < 5:
        return 0, ""
    # 简化：看最近几天的趋势
    recent = klines[-3:]
    closes = [k["close"] for k in recent]
    if closes[-1] > closes[0] * 1.02:
        return 30, "📈上升趋势"
    return 0, ""

def calc_breakout(klines):
    """放量突破"""
    if len(klines) < 10:
        return 0, ""
    recent = klines[-5:]
    vols = [k["volume"] for k in recent]
    vol_ratio = vols[-1] / (sum(vols[:-1]) / 4) if sum(vols[:-1]) > 0 else 0
    change = (recent[-1]["close"] - recent[-2]["close"]) / recent[-2]["close"] * 100
    peak = max([k["high"] for k in recent[:-1]])
    if recent[-1]["close"] > peak and vol_ratio > 1.3:
        return 25, "💥放量突破"
    return 0, ""

def calc_strength(rt, klines):
    """综合评分"""
    score = 0
    signals = []
    
    # 涨幅评分
    change = rt.get("change", 0)
    if change > 9:
        score += 30
        signals.append("🔥涨停")
    elif change > 7:
        score += 20
        signals.append("⚡大涨")
    elif change > 5:
        score += 15
        signals.append("🚀涨幅>5%")
    
    # 放量评分
    amount = rt.get("amount", 0)
    if amount and amount > 500000000:
        score += 20
        signals.append("💰成交额>5亿")
    elif amount and amount > 300000000:
        score += 10
        signals.append("💵成交额>3亿")
    
    # 趋势评分
    z_val, z_sig = calc_zhuanxing(klines)
    score += z_val
    if z_sig:
        signals.append(z_sig)
    
    # 突破评分
    b_val, b_sig = calc_breakout(klines)
    score += b_val
    if b_sig:
        signals.append(b_sig)
    
    return score, signals

# ============ 主程序 ============

def scan_market(scan_time):
    """扫描市场"""
    print(f"\n{'='*70}")
    print(f"📡 盘中实时监控 - {scan_time}")
    print(f"{'='*70}")
    
    # 1. 板块资金流
    print("\n🔥 板块资金流 (前5):")
    sectors = get_sector_flow()
    for i, s in enumerate(sectors, 1):
        print(f"  {i}. {s['name']} ({s['change']:+.2f}%)")
    
    # 2. 涨幅前10
    print("\n📈 涨幅前10 (涨幅>5% + 成交额>3亿):")
    gainers = get_top_gainers(10)
    
    results = []
    for g in gainers[:10]:
        rt = get_stock_realtime(g["code"])
        if rt:
            klines = get_kline(g["code"], 20)
            score, signals = calc_strength(rt, klines)
            if score > 0:
                results.append({
                    "code": g["code"],
                    "name": rt["name"],
                    "price": rt["price"],
                    "change": rt["change"],
                    "amount": rt.get("amount", 0) / 100000000,
                    "score": score,
                    "signals": signals
                })
    
    # 排序
    results.sort(key=lambda x: -x["score"])
    
    # 输出
    print(f"\n{'代码':<8} {'名称':<10} {'价格':<8} {'涨幅':<8} {'成交额':<10} {'评分':<6} {'信号'}")
    print("-" * 80)
    
    for r in results[:8]:
        sigs = " | ".join(r["signals"][:3])
        print(f"{r['code']:<8} {r['name']:<10} {r['price']:<8} {r['change']:+.2f}%{'':<3} {r['amount']:.1f}亿{'':<4} {r['score']:<6} {sigs}")
    
    # 重点推荐
    strong = [r for r in results if r["score"] >= 30]
    if strong:
        print(f"\n{'='*70}")
        print("💎 重点关注 (评分≥30)")
        print(f"{'='*70}")
        for r in strong[:5]:
            print(f"\n⭐ {r['name']}({r['code']})")
            print(f"   价格: {r['price']} | 涨幅: {r['change']:+.2f}% | 成交额: {r['amount']:.1f}亿")
            for s in r["signals"]:
                print(f"   → {s}")
    
    return results

def main():
    import sys
    scan_time = sys.argv[1] if len(sys.argv) > 1 else "手动"
    scan_market(scan_time)

if __name__ == "__main__":
    main()
