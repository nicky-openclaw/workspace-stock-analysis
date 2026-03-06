#!/usr/bin/env python3
"""
股票指标选股工具
用法:
    python screener.py --indicator b2 --limit 10
    python screener.py --indicator bldong --limit 10
    python screener.py --indicator danzhen --limit 10
"""

import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import akshare as ak
import pandas as pd
from indicators.library import (
    check_b2, check_bldong, check_chaoji_b1, 
    calc_dongnan, calc_danzhen, calc_qushixian
)

def get_stock_list(limit=None):
    """获取股票列表"""
    stock_info = ak.stock_info_a_code_name()
    stocks = stock_info[~stock_info['name'].str.contains('ST|退|退市')]['code']
    if limit:
        stocks = stocks[:limit]
    return stocks.tolist()

def fetch_stock_data(code, days=60):
    """获取股票数据"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=code, 
            period="daily", 
            start_date="20250101",
            adjust="qfq"
        )
        return df
    except:
        return None

def screen_b2(stock_list, limit=10):
    """B2选股"""
    results = []
    stock_info = ak.stock_info_a_code_name()
    
    for i, code in enumerate(stock_list):
        df = fetch_stock_data(code)
        if df is None or len(df) < 20:
            continue
            
        yesterday_df = df.iloc[:-1]
        
        try:
            match, data = check_b2(df, yesterday_df)
            if match:
                name = stock_info[stock_info['code'] == code]['name'].values[0]
                results.append({
                    'code': code,
                    'name': name,
                    '涨幅': f"{data['涨幅']:.2f}%",
                    'J值': f"{data['今日J']:.1f}"
                })
        except:
            pass
        
        if len(results) >= limit:
            break
            
        if (i+1) % 50 == 0:
            print(f"  已处理 {i+1} 只股票...")
    
    return results

def screen_bldong(stock_list, limit=10):
    """暴力动能选股"""
    results = []
    stock_info = ak.stock_info_a_code_name()
    
    for i, code in enumerate(stock_list):
        df = fetch_stock_data(code)
        if df is None or len(df) < 40:
            continue
            
        try:
            match, data = check_bldong(df)
            if match:
                name = stock_info[stock_info['code'] == code]['name'].values[0]
                signals = []
                if data.get('强动能'):
                    signals.append('强动能')
                if data.get('暴力动能'):
                    signals.append('暴力动能')
                if data.get('爆量动能'):
                    signals.append('爆量动能')
                if data.get('莫名其妙'):
                    signals.append('莫名其妙')
                    
                results.append({
                    'code': code,
                    'name': name,
                    '信号': ','.join(signals),
                    '黄柱': f"{data.get('黄柱', 0):.1f}"
                })
        except Exception as e:
            pass
        
        if len(results) >= limit:
            break
            
        if (i+1) % 50 == 0:
            print(f"  已处理 {i+1} 只股票...")
    
    return results

def screen_chaoji_b1(stock_list, limit=10):
    """超级B1选股"""
    results = []
    stock_info = ak.stock_info_a_code_name()
    
    for i, code in enumerate(stock_list):
        df = fetch_stock_data(code)
        if df is None or len(df) < 40:
            continue
            
        try:
            match, data = check_chaoji_b1(df)
            if match:
                name = stock_info[stock_info['code'] == code]['name'].values[0]
                results.append({
                    'code': code,
                    'name': name,
                    'J': f"{data.get('J', 0):.1f}",
                    'RSI': f"{data.get('RSI', 0):.1f}",
                    '缩量': '是' if data.get('缩量') else '否'
                })
        except:
            pass
        
        if len(results) >= limit:
            break
            
        if (i+1) % 50 == 0:
            print(f"  已处理 {i+1} 只股票...")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='股票指标选股工具')
    parser.add_argument('--indicator', '-i', choices=['b2', 'bldong', 'chaojib1', 'all'], 
                       default='b2', help='选择指标')
    parser.add_argument('--limit', '-l', type=int, default=10, help='结果数量')
    parser.add_argument('--stocks', '-s', type=int, default=200, help='检查股票数')
    
    args = parser.parse_args()
    
    print(f"📊 获取股票列表 (前{args.stocks}只)...")
    stock_list = get_stock_list(args.stocks)
    print(f"  共 {len(stock_list)} 只股票\n")
    
    if args.indicator == 'b2':
        print("🎯 B2选股...")
        results = screen_b2(stock_list, args.limit)
        print(f"\n结果: {len(results)} 只")
        for r in results:
            print(f"  {r['code']} {r['name']} | 涨幅:{r['涨幅']} | J:{r['J值']}")
            
    elif args.indicator == 'bldong':
        print("🎯 暴力动能选股...")
        results = screen_bldong(stock_list, args.limit)
        print(f"\n结果: {len(results)} 只")
        for r in results:
            print(f"  {r['code']} {r['name']} | 信号:{r['信号']} | 黄柱:{r['黄柱']}")
            
    elif args.indicator == 'chaojib1':
        print("🎯 超级B1选股...")
        results = screen_chaoji_b1(stock_list, args.limit)
        print(f"\n结果: {len(results)} 只")
        for r in results:
            print(f"  {r['code']} {r['name']} | J:{r['J']} | RSI:{r['RSI']} | 缩量:{r['缩量']}")
            
    elif args.indicator == 'all':
        print("🎯 执行全部指标选股...\n")
        
        print("=== B2选股 ===")
        results = screen_b2(stock_list, 5)
        for r in results:
            print(f"  {r['code']} {r['name']}")
            
        print("\n=== 暴力动能 ===")
        results = screen_bldong(stock_list, 5)
        for r in results:
            print(f"  {r['code']} {r['name']} ({r['信号']})")
            
        print("\n=== 超级B1 ===")
        results = screen_chaoji_b1(stock_list, 5)
        for r in results:
            print(f"  {r['code']} {r['name']}")

if __name__ == '__main__':
    main()
