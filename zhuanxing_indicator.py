#!/usr/bin/env python3
"""
砖形图计算工具
根据通达信公式计算砖形图指标
"""

import requests
import time

def get_kline_data(secid, days=20):
    """获取K线数据"""
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",  # 日K
        "fqt": "0",    # 不复权
        "beg": "20260101",
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
    except Exception as e:
        print(f"获取数据失败: {e}")
    return []

def calculate_zhuanxing(klines):
    """
    计算砖形图指标
    VAR1A:=(HHV(HIGH,4)-CLOSE)/(HHV(HIGH,4)-LLV(LOW,4))*100-90;
    VAR2A:=SMA(VAR1A,4,1)+100;
    VAR3A:=(CLOSE-LLV(LOW,4))/(HHV(HIGH,4)-LLV(LOW,4))*100;
    VAR4A:=SMA(VAR3A,6,1);
    VAR5A:=SMA(VAR4A,6,1)+100;
    VAR6A:=VAR5A-VAR2A;
    砖型图:=IF(VAR6A>4,VAR6A-4,0);
    """
    if len(klines) < 10:
        return []
    
    results = []
    close_prices = [k["close"] for k in klines]
    high_prices = [k["high"] for k in klines]
    low_prices = [k["low"] for k in klines]
    
    for i in range(len(klines) - 4):
        # 取最近4天的最高和最低
        hhv4 = max(high_prices[:i+5])
        llv4 = min(low_prices[:i+5])
        
        if hhv4 == llv4:
            var3a = 50
        else:
            var3a = (close_prices[i] - llv4) / (hhv4 - llv4) * 100
        
        # 简化计算：取最近6天的var3a平均值
        var3a_values = []
        for j in range(max(0, i-5), i+1):
            hhv = max(high_prices[:j+1]) if j >= 0 else high_prices[0]
            llv = min(low_prices[:j+1]) if j >= 0 else low_prices[0]
            if hhv != llv:
                v3 = (close_prices[j] - llv) / (hhv - llv) * 100
            else:
                v3 = 50
            var3a_values.append(v3)
        
        var4a = sum(var3a_values) / len(var3a_values) if var3a_values else 50
        var5a = var4a + 100  # 简化
        
        # VAR1A计算
        hhv4_current = max(high_prices[:i+1]) if i >= 0 else high_prices[0]
        llv4_current = min(low_prices[:i+1]) if i >= 0 else low_prices[0]
        if hhv4_current == llv4_current:
            var1a = 0
        else:
            var1a = ((hhv4_current - close_prices[i]) / (hhv4_current - llv4_current)) * 100 - 90
        var2a = var1a + 100  # 简化
        
        var6a = var5a - var2a
        zhuanxing = max(0, var6a - 4) if var6a > 4 else 0
        
        results.append({
            "date": klines[i]["date"],
            "close": klines[i]["close"],
            "zhuanxing": round(zhuanxing, 2),
            "signal": ""
        })
    
    # 判断信号
    for i in range(1, len(results)):
        prev = results[i-1]["zhuanxing"]
        curr = results[i]["zhuanxing"]
        
        # 绿转红：之前是0或绿，现在变成红
        if prev < curr and curr > 0:
            results[i]["signal"] = "🟢→🔴 绿转红(买)"
        # 红转绿：之前是红，现在是0或绿
        elif prev > curr and prev > 0:
            results[i]["signal"] = "🔴→🟢 红转绿(卖)"
    
    return results

def analyze_stock(code, name=""):
    """分析单只股票"""
    # 确定市场代码
    if code.startswith("6"):
        secid = f"1.{code}"
    elif code.startswith("0") or code.startswith("3"):
        secid = f"0.{code}"
    else:
        secid = f"0.{code}"
    
    klines = get_kline_data(secid, 30)
    if not klines:
        print(f"无法获取 {code} 的数据")
        return
    
    results = calculate_zhuanxing(klines[-10:])  # 只看最近10天
    
    print(f"\n{'='*60}")
    print(f"📊 {name}({code}) 砖形图分析 - 最近10天")
    print(f"{'='*60}")
    print(f"{'日期':<12} {'收盘价':<10} {'砖形值':<10} {'信号'}")
    print("-" * 60)
    
    for r in results[-10:]:
        signal = r["signal"] if r["signal"] else ""
        print(f"{r['date']:<12} {r['close']:<10.2f} {r['zhuanxing']:<10.2f} {signal}")
    
    # 最新的信号
    if results:
        latest = results[-1]
        print(f"\n📌 最新信号: {latest['date']}")
        if latest["zhuanxing"] > 0:
            print(f"   当前砖形图为红 🔴 (看多)")
        else:
            print(f"   当前砖形图为绿 🟢 (看空)")
        
        # 检查最近是否有买点
        for r in reversed(results[-3:]):
            if "绿转红" in r["signal"]:
                print(f"   ⚡ 最近买点是 {r['date']} - {r['signal']}")
                break

if __name__ == "__main__":
    import sys
    
    # 测试几只股票
    stocks = [
        ("601890", "亚星锚链"),
        ("600893", "航发动力"),
        ("600410", "华胜天成"),
    ]
    
    for code, name in stocks:
        analyze_stock(code, name)
        time.sleep(0.5)
