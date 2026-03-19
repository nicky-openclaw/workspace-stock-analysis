#!/usr/bin/env python3
"""
patrol_review_data.py
选股复盘数据获取模块

功能：
1. 腾讯API批量获取基础数据
2. agent-browser获取详细数据（API失败时的备用）

使用方式：
在OpenClaw agent环境中调用
"""

import requests
import re
import json

# ==================== 腾讯API ====================

def get_basic_data_from_tencent(stock_codes: list) -> list:
    """
    腾讯API批量获取基础数据（快速）
    返回：代码、名称、收盘价、涨跌幅、开盘价
    """
    results = []
    
    # 批量查询
    codes = []
    for code, name, market in stock_codes:
        codes.append(f"{market}{code}")
    
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    
    try:
        resp = requests.get(url, timeout=10)
        content = resp.content.decode('gbk', errors='ignore')
        
        for code, name, market in stock_codes:
            search_key = f"v_{market}{code}="
            for line in content.split(';'):
                if search_key in line:
                    parts = line.split('~')
                    if len(parts) > 12:
                        results.append({
                            'code': code,
                            'name': parts[1],
                            'current': float(parts[3]) if parts[3] else 0,
                            'pre_close': float(parts[4]) if parts[4] else 0,
                            'open': float(parts[5]) if parts[5] else 0,
                            'volume': int(parts[6]) if parts[6] else 0,
                            'high': float(parts[12]) if parts[12] else 0,
                            'low': float(parts[9]) if parts[9] else 0,
                            'change': 0,
                        })
                        # 计算涨跌幅
                        if results[-1]['pre_close'] > 0:
                            results[-1]['change'] = (
                                results[-1]['current'] - results[-1]['pre_close']
                            ) / results[-1]['pre_close'] * 100
                        break
    except Exception as e:
        print(f"腾讯API错误: {e}")
    
    return results

# ==================== agent-browser ====================

AGENT_BROWSER_CMD = """
# 使用 agent-browser 获取股票详细数据的步骤

# Step 1: 打开股票页面
agent-browser open https://quote.eastmoney.com/sz{code}.html

# Step 2: 获取快照
agent-browser snapshot -i

# Step 3: 从输出中解析以下数据：
# - 最高价/最低价
# - 成交量、换手率
# - 量比
# - 龙虎榜信息
# - 成交额是否创历史新高
# - 所属板块
"""

def get_agent_browser_command(code: str) -> str:
    """
    返回获取指定股票数据的agent-browser命令
    """
    market = "sz" if code.startswith("3") or code.startswith("0") else "sh"
    url = f"https://quote.eastmoney.com/{market}{code}.html"
    
    return f"agent-browser open {url}\nagent-browser snapshot -i"


# ==================== 主流程 ====================

def get_patrol_review_data(stock_codes: list, use_browser=False) -> list:
    """
    获取复盘数据的主函数
    
    Args:
        stock_codes: 股票代码列表 [(code, name, market), ...]
        use_browser: 是否使用浏览器（当API失败时）
    
    Returns:
        股票数据列表
    """
    # 优先用腾讯API
    results = get_basic_data_from_tencent(stock_codes)
    
    if not results and use_browser:
        # API失败，标记需要用agent-browser获取
        for code, name, market in stock_codes:
            results.append({
                'code': code,
                'name': name,
                'need_browser': True,
                'agent_browser_cmd': get_agent_browser_command(code)
            })
    
    return results


if __name__ == "__main__":
    # 测试
    test_codes = [
        ("300051", "琏升科技", "sz"),
        ("300042", "朗科科技", "sz"),
    ]
    
    results = get_patrol_review_data(test_codes)
    print(json.dumps(results, ensure_ascii=False, indent=2))
