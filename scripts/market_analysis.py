#!/usr/bin/env python3
"""
大盘分析数据获取脚本
用于每日复盘中的大盘分析模块

数据来源：
- 新浪财经API：指数涨跌幅 + 成交量 + 成交额
- eastmoney_financial_data：板块资金流向

使用方式：
    python3 scripts/market_analysis.py
"""

import requests
import re
import json
from datetime import datetime

def get_index_data_sina():
    """
    新浪财经API获取指数数据
    返回：指数涨跌幅、成交量、成交额
    """
    result = {
        "上证": {},
        "深证": {},
        "沪深300": {}
    }
    
    try:
        url = "https://hq.sinajs.cn/list=s_sh000001,sz399001,sh000300"
        headers = {"Referer": "https://finance.sina.com.cn"}
        resp = requests.get(url, headers=headers, timeout=5)
        content = resp.content.decode('gbk', errors='ignore')
        
        for line in content.split("\n"):
            if "hq_str" not in line:
                continue
            
            parts = line.split("=")[1].replace('"', '').split(",")
            name = parts[0]
            
            if "上证" in name:
                # 格式：名称,当前价,涨跌额,涨跌幅,成交量(万手),成交额(万元)
                result["上证"] = {
                    "price": float(parts[1]),
                    "change": float(parts[3]),
                    "volume_wan": float(parts[4]),
                    "amount_wan": float(parts[5].split(";")[0]),
                    "date": parts[30] if len(parts) > 30 else "",
                    "time": parts[31] if len(parts) > 31 else ""
                }
            elif "深证" in name:
                # 格式：名称,昨收,今开,现价,最高,最低,...,成交量(股),成交额(元),...
                vol_shares = float(parts[8]) if parts[8] else 0
                amount_yuan = float(parts[9]) if parts[9] else 0
                change = (float(parts[3]) - float(parts[2])) / float(parts[2]) * 100 if float(parts[2]) > 0 else 0
                result["深证"] = {
                    "price": float(parts[3]),
                    "change": change,
                    "volume_wan": vol_shares / 10000,
                    "amount_yi": amount_yuan / 1e8,
                    "date": parts[30] if len(parts) > 30 else "",
                    "time": parts[31] if len(parts) > 31 else ""
                }
            elif "沪深300" in name:
                amount_yuan = float(parts[9]) if parts[9] else 0
                change = (float(parts[3]) - float(parts[2])) / float(parts[2]) * 100 if float(parts[2]) > 0 else 0
                result["沪深300"] = {
                    "price": float(parts[3]),
                    "change": change,
                    "volume_wan": float(parts[8]) / 10000 if parts[8] else 0,
                    "amount_yi": amount_yuan / 1e8,
                    "date": parts[30] if len(parts) > 30 else "",
                    "time": parts[31] if len(parts) > 31 else ""
                }
                
    except Exception as e:
        print(f"[错误] 新浪API获取失败: {e}")
    
    return result

def get_yesterday_volume():
    """
    获取昨日成交量（简单方式：读取patrol/market/目录下的昨日文档）
    """
    from datetime import datetime, timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    # 这里后续会从patrol/market/目录读取
    return None

def calculate_volume_compare(today_total, yesterday_total):
    """
    计算成交量对比
    """
    if yesterday_total is None or yesterday_total == 0:
        return "N/A"
    
    change_pct = (today_total - yesterday_total) / yesterday_total * 100
    
    if change_pct > 10:
        return f"放量{change_pct:.1f}%"
    elif change_pct < -10:
        return f"缩量{abs(change_pct):.1f}%"
    else:
        return f"持平{change_pct:+.1f}%"

def parse_market_sentiment(change_pct, zt_count):
    """
    判断市场情绪
    """
    if change_pct > 1.5 and zt_count > 80:
        return "活跃"
    elif change_pct > 0.5:
        return "偏暖"
    elif change_pct < -1:
        return "冷淡"
    else:
        return "中性"

def main():
    print("=" * 60)
    print("📊 大盘分析数据获取")
    print("=" * 60)
    
    # 获取指数数据
    print("\n🔍 获取指数数据...")
    index_data = get_index_data_sina()
    
    if not index_data["上证"]:
        print("[错误] 无法获取指数数据")
        return
    
    # 计算两市总成交额
    sh_amount = index_data["上证"].get("amount_wan", 0) / 10000  # 万元 → 亿元
    sz_amount = index_data["深证"].get("amount_yi", 0)  # 已经是亿元
    total_amount = sh_amount + sz_amount
    
    print(f"\n📈 指数表现：")
    for name, data in index_data.items():
        if data:
            print(f"  {name}: {data['price']:.2f} ({data['change']:+.2f}%)")
    
    print(f"\n📊 成交量：")
    print(f"  上证成交额: {sh_amount:.1f}亿元")
    print(f"  深证成交额: {sz_amount:.1f}亿元")
    print(f"  两市合计: {total_amount:.1f}亿元")
    
    # 输出JSON格式供脚本使用
    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "indices": index_data,
        "total_amount": total_amount,
        "sh_amount": sh_amount,
        "sz_amount": sz_amount
    }
    
    print(f"\n📦 JSON输出：")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
