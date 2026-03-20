#!/usr/bin/env python3
"""
短线交易综合系统
早盘(10:00) + 午后(14:00) + 收盘(14:50) 三次监控
"""

import requests
import time
import sys
import json

# ============= 配置 =============
SCAN_TIMES = {
    "10:00": "早盘监控",
    "14:00": "午后监控", 
    "14:50": "收盘确认"
}

# ============= 数据获取 =============
# 重要：腾讯财经API为首选，东方财富API为备用

def get_sector_flow():
    """获取大盘指数涨跌 - 腾讯"""
    
    try:
        url = "https://qt.gtimg.cn/q=sh000001,sz399001,sh000300"
        resp = requests.get(url, timeout=5)
        sectors = []
        for line in resp.text.split("\n"):
            if "=" in line:
                parts = line.split("~")
                if len(parts) > 32:
                    try:
                        name = parts[1][:10]
                        change = float(parts[32]) if parts[32] and parts[32] != '-' else 0
                        sectors.append({"name": name, "change": change})
                    except:
                        pass
        if sectors:
            print(f"  [腾讯] 大盘数据获取成功")
            return sectors[:3]
    except Exception as e:
        print(f"  [腾讯] 获取失败: {e}")
    
    return []

def get_top_gainers(limit=15):
    """获取涨幅>5%且成交>3亿的股票 - 新浪财经沪深接口"""
    
    # 新浪财经：沪深分开取，再合并
    nodes = ["sh_a", "sz_a"]
    all_result = []
    
    for node in nodes:
        for attempt in range(2):
            try:
                url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
                params = {
                    "page": 1,
                    "num": 100,
                    "sort": "percent",
                    "asc": 0,
                    "node": node,
                    "_s_r_a": "page"
                }
                
                resp = requests.get(url, params=params, timeout=15)
                data = resp.json()
                
                for item in data:
                    change = item.get("changepercent", 0)
                    amount = item.get("amount", 0)  # 单位：元
                    
                    # 筛选：涨幅>5% 且 成交>3亿
                    if change > 5 and amount > 300000000:
                        all_result.append({
                            "code": item.get("code", ""),
                            "name": item.get("name", ""),
                            "price": item.get("trade", 0),
                            "change": change,
                            "amount": amount / 100000000  # 亿元
                        })
                break  # 成功则跳到下一个node
                
            except Exception as e:
                if attempt < 1:
                    time.sleep(1)
                    continue
                print(f"  [新浪-{node}] 获取失败: {e}")
    
    if all_result:
        all_result.sort(key=lambda x: x["change"], reverse=True)
        print(f"  [新浪财经] 获取到 {len(all_result)} 只强势股")
        return all_result[:limit]
    
    print("  [警告] API获取失败，将使用浏览器兜底方案")
    return None  # 返回None表示需要浏览器兜底

def get_stock_realtime(code):
    """获取个股实时行情 - 腾讯首选，东方财富备用"""
    # 首选：腾讯财经
    try:
        market = "sh" if code.startswith("6") else "sz"
        url = f"https://qt.gtimg.cn/q={market}{code}"
        resp = requests.get(url, timeout=5)
        for line in resp.text.split("\n"):
            if "=" in line:
                parts = line.split("~")
                if len(parts) > 10:
                    return {
                        "code": parts[2], "name": parts[1],
                        "price": float(parts[3]) if parts[3] else 0,
                        "change": float(parts[4]) if parts[4] else 0,
                        "amount": float(parts[7]) if parts[7] else 0
                    }
    except:
        pass
    
    # 备用：东方财富
    if code.startswith("6"):
        secid = "1." + code
    else:
        secid = "0." + code
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {"secid": secid, "fields": "f2,f3,f4,f5,f7,f8,f9,f12,f14"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("data") and data["data"].get("diff"):
            d = data["data"]["diff"][0]
            return {
                "code": d.get("f12"), "name": d.get("f14"),
                "price": d.get("f2"), "change": d.get("f3"),
                "amount": d.get("f4")
            }
    except:
        pass
    return None

def get_kline(code, days=20):
    """获取K线数据 - 腾讯首选，东方财富备用"""
    
    # 首选：腾讯财经
    try:
        market = "sh" if code.startswith("6") or code.startswith("5") else "sz"
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,{days},qfq"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if 'data' in data and f"{market}{code}" in data['data']:
            klines = data['data'][f"{market}{code}"].get('qfqday', [])
            if klines:
                result = []
                for k in klines:
                    result.append({
                        "date": k[0],
                        "open": float(k[1]),
                        "close": float(k[2]),
                        "high": float(k[3]),
                        "low": float(k[4]),
                        "volume": float(k[5])
                    })
                print(f"  [腾讯财经] K线获取成功")
                return result
    except Exception as e:
        print(f"  [腾讯财经] K线获取失败: {e}")
    
    # 备用：东方财富
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

# ============= 砖型图计算 =============

def calculate_zhuanxing(klines):
    """计算砖型图"""
    if len(klines) < 5:
        return []
    
    results = []
    for i in range(4, len(klines)):
        high_4 = max([k["high"] for k in klines[max(0, i-3):i+1]])
        low_4 = min([k["low"] for k in klines[max(0, i-3):i+1]])
        close = klines[i]["close"]
        open_price = klines[i]["open"]
        
        if high_4 == low_4:
            var1a, var3a = 0, 50
        else:
            var1a = ((high_4 - close) / (high_4 - low_4)) * 100 - 90
            var3a = ((close - low_4) / (high_4 - low_4)) * 100
        
        var6a = var3a - var1a
        zhuan_value = max(0, var6a - 4)
        
        is_red = close >= open_price
        results.append({
            "date": klines[i]["date"],
            "close": close,
            "zhuan": zhuan_value,
            "is_red": is_red,
            "volume": klines[i]["volume"]
        })
    
    return results

def check_zhuanxing_signal(klines):
    """
    检查砖型图买入信号
    
    核心因子：
    1. 当天红砖（收盘 > 开盘）
    2. 前一天绿砖（收盘 < 开盘）  
    3. 红砖体积 > 前一天绿砖体积
    """
    zhuan_data = calculate_zhuanxing(klines)
    if not zhuan_data or len(zhuan_data) < 2:
        return None
    
    today = zhuan_data[-1]
    yesterday = zhuan_data[-2]
    
    # 必须当天红砖
    if not today["is_red"]:
        return None
    
    # 必须前一天绿砖
    if yesterday["is_red"]:
        return None
    
    # 红砖体积 > 前一天绿砖体积
    red_vol = today["zhuan"]
    green_vol = abs(yesterday["zhuan"])
    
    if red_vol <= green_vol:
        return None
    
    # 信号强度
    score = 35  # 砖型基础分
    if red_vol > 100:
        score += 10  # 强红加成
    
    return score

# ============= 信号计算 =============

def calc_signals(rt, klines):
    """计算股票评分和技术信号"""
    score = 0
    signals = []
    
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
    
    amount = rt.get("amount", 0)
    if amount and amount > 500000000:
        score += 20
        signals.append("💰成交>5亿")
    elif amount and amount > 300000000:
        score += 10
        signals.append("💵成交>3亿")
    
    # 放量突破检测
    if klines and len(klines) >= 5:
        vols = [k["volume"] for k in klines[-5:]]
        vol_ratio = vols[-1] / (sum(vols[:-1]) / 4) if sum(vols[:-1]) > 0 else 0
        peak = max([k["high"] for k in klines[:-1]])
        if klines[-1]["close"] > peak and vol_ratio > 1.3:
            score += 25
            signals.append("💥放量突破")
    
    # 砖型图信号检测
    if klines and len(klines) >= 10:
        zhuan_score = check_zhuanxing_signal(klines)
        if zhuan_score:
            score += zhuan_score
            signals.append("🧱砖型买入")
    
    return score, signals

# ============= 主程序 =============

def scan(scan_time):
    print(f"\n{'='*75}")
    print(f"📡 短线交易监控系统 - {scan_time}")
    print(f"{'='*75}")
    
    # 板块资金流
    print("\n🔥 板块资金流:")
    sectors = get_sector_flow()
    if sectors:
        for i, s in enumerate(sectors[:3], 1):
            print(f"  {i}. {s['name']} ({s['change']:+.2f}%)")
    else:
        print("  [提示] 板块数据获取失败")
    
    # 强势股筛选
    print("\n📈 强势股 (涨幅>5% + 成交>3亿):")
    gainers = get_top_gainers(20)
    
    if gainers is None:
        # API失败，返回特殊标记触发浏览器兜底
        print("  [提示] 数据源暂时无响应，请使用浏览器方式获取")
        print("\n" + "="*75)
        print("💡 操作建议")
        print("="*75)
        print("API数据获取失败，需要使用浏览器方式获取数据")
        return None  # None表示需要浏览器兜底
    
    if not gainers:
        print("  [提示] 数据源暂时无响应，请稍后再试")
        print("\n" + "="*75)
        print("💡 操作建议")
        print("="*75)
        print("数据获取失败，建议稍后再试或使用其他数据源验证")
        return []
    
    results = []
    if gainers:
        for g in gainers[:15]:
            # 直接使用获取到的数据，不需要再查询
            rt = {
                "code": g["code"],
                "name": g["name"],
                "price": g["price"],
                "change": g["change"],
                "amount": g["amount"] * 100000000  # 转回元
            }
            
            # 尝试获取K线（可能失败）
            klines = get_kline(g["code"], 20)
            score, signals = calc_signals(rt, klines)
            
            if score > 0:
                results.append({
                    "code": g["code"],
                    "name": g["name"],
                    "price": g["price"],
                    "change": g["change"],
                    "amount": g["amount"],
                    "score": score,
                    "signals": signals
                })
        
        results.sort(key=lambda x: -x["score"])
    
    print(f"\n{'代码':<8} {'名称':<10} {'价格':<8} {'涨幅':<10} {'评分':<6} {'信号'}")
    print("-" * 75)
    
    if results:
        for r in results[:10]:
            sigs = " | ".join(r["signals"][:3])
            print(f"{r['code']:<8} {r['name']:<10} {r['price']:<8} {r['change']:+10.2f}% {r['score']:<6} {sigs}")
    elif gainers is not None:
        # 有数据但评分后无结果
        print("  (无符合条件股票)")
    # else: gainers is None 浏览器兜底情况，不打印"无"
    
    # 重点推荐
    if results:
        strong = [r for r in results if r["score"] >= 30]
        if strong:
            print(f"\n{'='*75}")
            print("💎 重点关注 (评分≥30)")
            print(f"{'='*75}")
            for r in strong[:5]:
                print(f"\n⭐ {r['name']}({r['code']})")
                print(f"   价格: {r['price']} | 涨幅: {r['change']:+.2f}% | 成交: {r['amount']:.1f}亿")
                for s in r["signals"]:
                    print(f"   → {s}")
    
    # 操作建议
    print(f"\n{'='*75}")
    print("💡 操作建议")
    print(f"{'='*75}")
    if scan_time == "10:00":
        print("早盘监控：关注强势股，可小仓位试盘")
    elif scan_time == "14:00":
        print("午后监控：确认信号，等待收盘前决定")
    else:
        print("收盘确认：信号明确，次日执行策略")
    
    # gainers is None → API失败，需要浏览器兜底
    if gainers is None:
        return None
    return results

if __name__ == "__main__":
    scan_time = sys.argv[1] if len(sys.argv) > 1 else "手动"
    scan(scan_time)
