#!/usr/bin/env python3
"""
热点监控工具 - 整合东方财富板块资金流 + 雪球热股榜
用于超短线选股辅助
"""

import requests
import json
import time

# 东方财富 - 行业资金流
def get_dongcai_hy():
    api_url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": 10,
        "po": 1,
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:90+t:2",
        "fields": "f1,f2,f3,f4,f12,f13,f14",
        "_": int(time.time() * 1000)
    }
    try:
        resp = requests.get(api_url, params=params, timeout=10)
        data = resp.json()
        results = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"][:10]:
                results.append({
                    "name": item.get("f14", ""),
                    "change": item.get("f3", 0),
                    "source": "东财-行业"
                })
        return results
    except Exception as e:
        print(f"东财API错误: {e}")
        return []

# 东方财富 - 概念资金流  
def get_dongcai_gn():
    api_url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": 10,
        "po": 1,
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:90+t:3",
        "fields": "f1,f2,f3,f4,f12,f13,f14",
        "_": int(time.time() * 1000)
    }
    try:
        resp = requests.get(api_url, params=params, timeout=10)
        data = resp.json()
        results = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"][:10]:
                results.append({
                    "name": item.get("f14", ""),
                    "change": item.get("f3", 0),
                    "source": "东财-概念"
                })
        return results
    except Exception as e:
        print(f"东财API错误: {e}")
        return []

# 雪球热股榜
def get_xueqiu():
    url = "https://xueqiu.com/stock/cata_stock/picklist.json"
    params = {
        "page": 1,
        "size": 10,
        "type": "10",
        "_": int(time.time() * 1000)
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        results = []
        if data.get("data") and data["data"].get("list"):
            for item in data["data"]["list"][:10]:
                results.append({
                    "name": item.get("name", ""),
                    "code": item.get("symbol", ""),
                    "change": item.get("change", 0),
                    "source": "雪球"
                })
        return results
    except Exception as e:
        print(f"雪球API错误: {e}")
        return []

def main():
    print("=" * 60)
    print("🔥 热点监控 - 超短线选股参考")
    print("=" * 60)
    
    print("\n📊 板块资金流 (东财):")
    hy = get_dongcai_hy()
    for i, h in enumerate(hy, 1):
        print(f"  {i}. {h['name']} {h['change']:.2f}%")
    
    print("\n📊 概念资金流 (东财):")
    gn = get_dongcai_gn()
    for i, g in enumerate(gn, 1):
        print(f"  {i}. {g['name']} {g['change']:.2f}%")
    
    print("\n🔥 雪球热股榜:")
    xq = get_xueqiu()
    for i, x in enumerate(xq, 1):
        print(f"  {i}. {x['name']} ({x['code']}) {x['change']:.2f}%")
    
    print("\n" + "=" * 60)
    print("💡 超短线选股思路:")
    print("  1. 从上方热点板块中选股")
    print("  2. 结合砖形图绿转红信号")
    print("  3. 只做转折点，不追高")
    print("=" * 60)

if __name__ == "__main__":
    main()
