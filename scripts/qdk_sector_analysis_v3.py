#!/usr/bin/env python3
"""
启动K选股 - 板块效应分析一键脚本 v3.0
功能：自动获取个股所属板块、板块涨跌幅、板块主力净流入等数据
流程：
  1. API获取个股所属板块
  2. API获取个股资金流向
  3. 浏览器获取板块涨跌幅/主力净流入（需手动/外部调用）
  4. 合并数据
"""

import json
import time
import subprocess
import sys
from typing import Dict, List, Optional

# 东方财富API
EAST_MONEY_API = "https://push2.eastmoney.com/api/qt/stock/get"

# 申万行业到板块代码映射
INDUSTRY_CODE_MAP = {
    '电网设备': 'BK1031',
    '电力设备': 'BK1032',
    '通用设备': 'BK1030',
    '专用设备': 'BK1029',
    '装修装饰Ⅱ': 'BK1046',
    '环境治理': 'BK1226',
    '食品饮料': 'BK0438',
    '白酒Ⅱ': 'BK1277',
    '化学制品': 'BK0538',
    '医疗器械': 'BK1041',
    '半导体': 'BK1036',
    '元件': 'BK0459',
    '电池': 'BK1033',
    '汽车零部件': 'BK1011',
    '基础建设': 'BK1247',
    '风电设备': 'BK1032',
    '银行Ⅱ': 'BK0475',
    '白色家电': 'BK1239',
}

def get_stock_sector(stock_code: str) -> Dict:
    """获取个股所属板块"""
    secid = f"1.{stock_code}" if stock_code.startswith('6') else f"0.{stock_code}"
    url = f"{EAST_MONEY_API}?secid={secid}&fields=f127,f128"
    
    try:
        result = subprocess.run(['curl', '-s', url], capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        if data.get('data'):
            return {
                'industry': data['data'].get('f127', ''),
                'region': data['data'].get('f128', '')
            }
    except Exception as e:
        print(f"获取板块失败 {stock_code}: {e}")
    return {'industry': '', 'region': ''}

def get_stock_capital_flow(stock_code: str) -> Dict:
    """获取个股资金流向"""
    secid = f"1.{stock_code}" if stock_code.startswith('6') else f"0.{stock_code}"
    url = f"{EAST_MONEY_API}?secid={secid}&fields=f177"
    
    try:
        result = subprocess.run(['curl', '-s', url], capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        if data.get('data'):
            main_net = data['data'].get('f177', 0)
            return {'main_net_inflow': main_net if main_net else 0}
    except Exception as e:
        print(f"获取资金流失败 {stock_code}: {e}")
    return {'main_net_inflow': 0}

def format_money(amount: float) -> str:
    """格式化金额"""
    if not amount:
        return "0"
    amount = float(amount)
    if abs(amount) >= 100000000:
        return f"{amount/100000000:.2f}亿"
    elif abs(amount) >= 10000:
        return f"{amount/10000:.2f}万"
    return f"{amount:.2f}"

def main():
    """主函数"""
    
    # 读取TOP5股票（从qdk_scores.json）
    scores_file = '/Users/nicky/.openclaw/workspace-stock-analysis/qdk_output/qdk_scores.json'
    try:
        with open(scores_file) as f:
            data = json.load(f)
            stocks = [{'code': s['code'], 'name': s['name']} for s in data.get('top10', [])[:5]]
    except:
        # 默认TOP5
        stocks = [
            {"code": "605222", "name": "起帆电缆"},
            {"code": "002438", "name": "江苏神通"},
            {"code": "600234", "name": "科新发展"},
            {"code": "603029", "name": "天鹅股份"},
            {"code": "003027", "name": "同兴科技"},
        ]
    
    print("=" * 80)
    print("启动K选股 - 板块效应分析一键脚本")
    print("=" * 80)
    print()
    print("步骤1: 获取个股板块数据 (API)")
    print("-" * 40)
    
    results = []
    industries = set()
    
    for stock in stocks:
        code = stock['code']
        name = stock['name']
        
        print(f"获取 {code} {name} ...")
        
        # API获取板块和资金流
        sector = get_stock_sector(code)
        capital = get_stock_capital_flow(code)
        
        result = {
            'code': code,
            'name': name,
            'industry': sector['industry'],
            'region': sector['region'],
            'main_net_inflow': capital['main_net_inflow'],
            'sector_change_pct': 0,  # 待浏览器获取
            'sector_main_inflow': 0,  # 待浏览器获取
        }
        
        results.append(result)
        
        if sector['industry']:
            industries.add(sector['industry'])
        
        print(f"  行业: {sector['industry']}")
        print(f"  地域: {sector['region']}")
        print(f"  主力净流入: {format_money(capital['main_net_inflow'])}")
        
        time.sleep(0.3)
    
    # 保存中间结果
    output_file = '/Users/nicky/.openclaw/workspace-stock-analysis/qdk_output/sector_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 80)
    print("API数据获取完成！")
    print("=" * 80)
    print()
    print("步骤2: 浏览器获取板块涨跌幅/主力净流入")
    print("-" * 40)
    print()
    print("请在浏览器中打开以下页面获取板块数据:")
    print("  https://data.eastmoney.com/bkzj/hy.html")
    print()
    print("需要查询的行业板块:")
    for ind in industries:
        code = INDUSTRY_CODE_MAP.get(ind, '')
        if code:
            print(f"  - {ind}: https://data.eastmoney.com/bkzj/{code}.html")
        else:
            print(f"  - {ind}: (代码未映射)")
    print()
    print("获取后请手动补充到 sector_analysis.json")
    print()
    print("=" * 80)
    print("提示: 可运行 python3 scripts/qdk_merge_sector_data.py 合并最终报告")
    print("=" * 80)

if __name__ == "__main__":
    main()
