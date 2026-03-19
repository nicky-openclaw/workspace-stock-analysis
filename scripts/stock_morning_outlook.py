#!/usr/bin/env python3
"""
今日前瞻（开盘前）
执行时间：周一至周五 08:45

功能：
1. 获取隔夜外盘/大宗商品/新闻
2. 获取昨日A股全景（含成交量）
3. 获取昨日选股回顾
4. 生成前瞻内容并发送飞书
"""

import subprocess
import json
import urllib.request
import urllib.parse
import os
import re
from datetime import datetime, timedelta

# === 配置 ===
WORKSPACE = "/Users/nicky/.openclaw/workspace-stock-analysis"
FEISHU_GROUP = "oc_5079867a1fd5155704772dc651c7d230"

# === 工具函数 ===
def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_date_info():
    """获取日期信息，处理周一特殊逻辑"""
    today = datetime.now()
    weekday = today.weekday()  # 0=周一
    
    if weekday == 0:  # 周一
        # 上周五
        target_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")
        date_label = "上周五"
    else:
        # 昨天
        target_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        date_label = "昨日"
    
    return today, target_date, date_label

def fetch_aqii_data():
    """获取A股收盘数据（腾讯API）"""
    # 上证指数
    url = "https://qt.gtimg.cn/q=s_sh000001"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = response.read().decode('gbk')
            parts = data.split('~')
            return {
                "index": "上证指数",
                "price": parts[1],
                "change": parts[2],
                "volume": parts[3]
            }
    except Exception as e:
        return {"error": str(e)}

def fetch_global_markets():
    """获取隔夜外盘（从浏览器/东方财富）"""
    # TODO: 后续通过浏览器自动化获取
    return {
        "dow": {"price": "46677.85", "change": "-1.56%"},
        "nasdaq": {"price": "22311.98", "change": "-1.78%"},
        "sp500": {"price": "6672.62", "change": "-1.52%"},
        "nikkei": {"price": "54024.70", "change": "-0.79%"}
    }

def fetch_commodities():
    """获取大宗商品"""
    # TODO: 通过浏览器获取
    return {
        "oil": "突破100美元，+10%"
    }

def read_patrol_record(target_date):
    """读取昨日选股记录"""
    filepath = f"{WORKSPACE}/memory/patrol/{target_date}.md"
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    return None

def parse_volume_data(patrol_content):
    """从 patrol 内容中解析成交量数据"""
    if not patrol_content:
        return None
    
    # 匹配 "上证：X.XX万亿" 格式
    sh_match = re.search(r'上证[：:]\s*([\d.]+)万亿', patrol_content)
    sz_match = re.search(r'深证[：:]\s*([\d.]+)万亿', patrol_content)
    total_match = re.search(r'合计[：:]\s*([\d.]+)万亿', patrol_content)
    
    if sh_match or sz_match or total_match:
        return {
            "sh": sh_match.group(1) + "万亿" if sh_match else "N/A",
            "sz": sz_match.group(1) + "万亿" if sz_match else "N/A",
            "total": total_match.group(1) + "万亿" if total_match else "N/A"
        }
    return None

def generate_outlook(today, target_date, date_label, global_data, commodities, aqi_data, patrol_data, volume_data):
    """生成前瞻内容"""
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_names[today.weekday()]
    
    # 成交量部分
    volume_section = ""
    if volume_data:
        volume_section = f"""
## 昨日两市成交量

- 上证：{volume_data.get('sh', 'N/A')}
- 深证：{volume_data.get('sz', 'N/A')}
- 合计：{volume_data.get('total', 'N/A')}
"""
    else:
        volume_section = """
## 昨日两市成交量

（数据获取中...）
"""
    
    content = f"""🌅 【今日前瞻】{today.strftime('%Y年%m月%d日')} {weekday}

---

## 隔夜外盘

| 指数 | 涨跌幅 |
|------|--------|
| 道琼斯 | {global_data['dow']['change']} |
| 纳斯达克 | {global_data['nasdaq']['change']} |
| 标普500 | {global_data['sp500']['change']} |
| 日经225 | {global_data['nikkei']['change']} |

## 大宗商品

- 油价：{commodities['oil']}

{volume_section}
## 昨日A股

- 上证指数：{aqi_data.get('price', 'N/A')} ({aqi_data.get('change', 'N/A')})

## 昨日选股回顾

{patrol_data if patrol_data else '（暂无选股记录）'}

## 今日预判

（待分析）

## 开盘策略

（待分析）

---

⚠️ 风险提示：以上为个人观点，不构成投资建议
"""
    return content

def send_feishu(message):
    """发送飞书消息"""
    # TODO: 实现飞书发送
    print(message)

def main():
    today, target_date, date_label = get_date_info()
    print(f"今日: {today.strftime('%Y-%m-%d')}, 对标日期: {target_date} ({date_label})")
    
    # Step1: 获取隔夜外盘
    global_data = fetch_global_markets()
    
    # Step2: 获取大宗商品
    commodities = fetch_commodities()
    
    # Step3: 获取A股数据
    aqi_data = fetch_aqii_data()
    
    # Step4: 读取选股记录（含成交量）
    patrol_data = read_patrol_record(target_date)
    volume_data = parse_volume_data(patrol_data)
    
    # Step5: 生成内容
    content = generate_outlook(today, target_date, date_label, global_data, commodities, aqi_data, patrol_data, volume_data)
    
    # Step6: 发送
    send_feishu(content)
    print("发送完成")

if __name__ == "__main__":
    main()
