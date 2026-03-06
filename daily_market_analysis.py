#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日盘面分析脚本
数据源：腾讯财经API（首选） + 东方财富API（备用）
"""

import requests
import time
from datetime import datetime

# ============== 腾讯财经API ==============

def get_tencent_data(url):
    """获取腾讯财经数据"""
    try:
        r = requests.get(url, timeout=5)
        try:
            text = r.content.decode('gbk')
        except:
            text = r.text
        return text.strip('"').split('~')
    except:
        return None

def get_大盘_tencent():
    """腾讯财经获取大盘"""
    url = "https://qt.gtimg.cn/q=s_sh000001"
    data = get_tencent_data(url)
    if data and len(data) > 30:
        return {
            'name': '上证指数',
            'index': float(data[1]) if data[1] else 0,
            'change_pct': float(data[32]) if data[32] else 0
        }
    return None

def get_涨幅榜_tencent(limit=50):
    """腾讯财经获取涨幅榜"""
    # 腾讯API不支持涨跌幅排行，换一种方式
    # 尝试获取全部A股然后排序
    return None  # 暂不支持

# ============== 东方财富API（备用） ==============

def get_大盘_eastmoney():
    """东方财富获取大盘"""
    try:
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {"secid": "1.000001", "fields": "f2,f3,f14"}
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        if data.get("data"):
            d = data["data"]
            return {'name': d.get('f14'), 'index': float(d.get('f2',0)), 'change_pct': float(d.get('f3',0))}
    except:
        pass
    return None

def get_涨幅榜_eastmoney(limit=100):
    """东方财富获取涨幅榜"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1, "pz": limit, "po": 1, "np": 1,
            "fltt": 2, "invt": 2, "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f3,f12,f14"
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        stocks = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"]:
                stocks.append({
                    'code': item.get('f12'),
                    'name': item.get('f14'),
                    'price': item.get('f2', 0),
                    'change_pct': item.get('f3', 0),
                })
        return stocks
    except:
        return []

def get_板块_eastmoney():
    """东方财富获取板块排行"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1, "pz": 15, "po": 1, "np": 1,
            "fltt": 2, "invt": 2, "fid": "f3",
            "fs": "m:90+t:2",
            "fields": "f3,f14"
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        sectors = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"]:
                sectors.append({
                    'name': item.get('f14'),
                    'change_pct': item.get('f3', 0),
                })
        return sectors
    except:
        return []

def get_成交额榜_eastmoney(limit=20):
    """东方财富获取成交额榜"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1, "pz": limit, "po": 1, "np": 1,
            "fltt": 2, "invt": 2, "fid": "f62",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f3,f62,f12,f14"
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        stocks = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"]:
                stocks.append({
                    'code': item.get('f12'),
                    'name': item.get('f14'),
                    'price': item.get('f2', 0),
                    'change_pct': item.get('f3', 0),
                    'amount': item.get('f62', 0),
                })
        return stocks
    except:
        return []

def get_跌幅榜_eastmoney(limit=100):
    """东方财富获取跌幅榜"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1, "pz": limit, "po": 0, "np": 1,
            "fltt": 2, "invt": 2, "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f3,f12,f14"
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        stocks = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"]:
                stocks.append({
                    'code': item.get('f12'),
                    'name': item.get('f14'),
                    'price': item.get('f2', 0),
                    'change_pct': item.get('f3', 0),
                })
        return stocks
    except:
        return []

# ============== 统一接口（腾讯优先，失败用东方财富） ==============

def get_大盘():
    """获取大盘 - 腾讯优先"""
    data = get_大盘_tencent()
    if data:
        return data
    print("  [备用] 腾讯大盘失败，使用东方财富")
    return get_大盘_eastmoney()

def get_涨幅榜(limit=100):
    """获取涨幅榜 - 腾讯失败用东方财富"""
    # 腾讯不支持，改用东方财富
    print("  [数据源] 东方财富-涨幅榜")
    return get_涨幅榜_eastmoney(limit)

def get_板块排行():
    """获取板块排行"""
    print("  [数据源] 东方财富-板块")
    return get_板块_eastmoney()

def get_成交额榜(limit=20):
    """获取成交额排行"""
    print("  [数据源] 东方财富-成交额")
    return get_成交额榜_eastmoney(limit)

def get_跌幅榜(limit=100):
    """获取跌幅榜"""
    return get_跌幅榜_eastmoney(limit)

# ============== 情绪判断 ==============

def 判断情绪阶段():
    """判断情绪阶段"""
    大盘 = get_大盘()
    sh_change = 大盘.get('change_pct', 0) if 大盘 else 0
    
    涨幅榜 = get_涨幅榜(100)
    
    if not 涨幅榜:
        return "数据获取失败", {'大盘涨跌': sh_change}
    
    涨停数 = len([x for x in 涨幅榜 if x['change_pct'] >= 9.9])
    涨幅5数 = len([x for x in 涨幅榜 if x['change_pct'] >= 5])
    红盘 = len([x for x in 涨幅榜 if x['change_pct'] > 0])
    红盘占比 = 红盘 / len(涨幅榜) * 100
    
    if sh_change < -2 or 红盘占比 < 25:
        阶段 = "冰点期"
        信号 = "恐慌蔓延，准备反弹"
    elif sh_change > 2 or 红盘占比 > 80:
        阶段 = "高潮期"
        信号 = "情绪过热，注意风险"
    elif sh_change > 0.5 and 涨停数 > 20:
        阶段 = "上升期"
        信号 = "赚钱效应好，主线清晰"
    elif -1 < sh_change < 1:
        阶段 = "轮动期"
        信号 = "分化震荡，板块轮动"
    else:
        阶段 = "回落期"
        信号 = "亏钱效应扩散"
    
    return 阶段, {
        '大盘涨跌': sh_change,
        '涨停数': 涨停数,
        '涨幅5+': 涨幅5数,
        '红盘占比': f"{红盘占比:.0f}%",
        '信号': 信号,
    }

def 分析主线():
    """分析主线板块和龙头"""
    板块 = get_板块排行()
    成交额 = get_成交额榜(20)
    涨幅榜 = get_涨幅榜(50)
    
    涨停票 = [x for x in 涨幅榜 if x['change_pct'] >= 9.9]
    
    return {
        '热门板块': 板块[:5],
        '成交额前列': 成交额[:10],
        '涨停股': 涨停票[:10],
    }

def 找调整到位老龙头():
    """找成交额大但跌幅较小的横盘股"""
    成交额 = get_成交额榜(50)
    横盘股 = [s for s in 成交额 if -5 < s.get('change_pct', 0) < 2]
    return 横盘股[:10]

# ============== 主函数 ==============

def main():
    print("=" * 60)
    print(f"📊 每日盘面分析 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 1. 情绪阶段
    print("\n🔍 情绪周期判断...")
    阶段, 情绪 = 判断情绪阶段()
    print(f"   当前阶段: {阶段}")
    print(f"   信号: {情绪.get('信号', '')}")
    print(f"   大盘涨跌: {情绪.get('大盘涨跌', 0):.2f}%")
    print(f"   涨停数: {情绪.get('涨停数', 0)}")
    print(f"   涨幅5+: {情绪.get('涨幅5+', 0)}")
    print(f"   红盘占比: {情绪.get('红盘占比', 'N/A')}")
    
    # 2. 主线分析
    print("\n📈 主线板块...")
    主线 = 分析主线()
    
    print("\n   热门板块:")
    for i, b in enumerate(主线['热门板块'][:3], 1):
        print(f"   {i}. {b['name']} {b['change_pct']:+.2f}%")
    
    print("\n   成交额前列:")
    for i, s in enumerate(主线['成交额前列'][:5], 1):
        amt = s.get('amount', 0)
        print(f"   {i}. {s['name']} {amt/1e8:.1f}亿")
    
    print("\n   涨停股:")
    for s in 主线['涨停股'][:5]:
        print(f"   {s['name']} {s['change_pct']:+.2f}%")
    
    # 3. 轮动期老龙头
    print(f"\n🔄 轮动期关注...")
    if 阶段 == "轮动期":
        老龙头 = 找调整到位老龙头()
        print("   成交额大且横盘的票:")
        for s in 老龙头[:5]:
            print(f"   {s['name']} {s.get('change_pct', 0):+.2f}%")
    else:
        print(f"   当前是{阶段}，跳过")
    
    print("\n" + "=" * 60)
    print("✅ 分析完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
