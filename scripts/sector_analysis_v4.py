#!/usr/bin/env python3
"""
板块效应分析 v4.2
数据获取优先级：
1. 腾讯API → 个股涨跌幅（免费）
2. eastmoney_financial_data → 行业归属+板块涨跌幅+主力净额（约1次/板块）
3. agent-browser → 补齐行业归属（eastmoney_financial_data失败时）
4. QVeris → 保底（仅当前三步都失败时使用）
"""

import json
import subprocess
import os
import sys
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
QVERIS_SCRIPT = Path.home() / ".openclaw/skills/qveris-official/scripts/qveris_tool.mjs"
QVERIS_API_KEY = "sk-PxV8UWOz7UcoaU6yt0rsAfrzmTpSAyW70Qge8jsj-8g"
EASTMONEY_APIKEY = "mkt_ed_FmsusuPQr6aZCpqc2Pgof6l7gGbnvS_riNSxtGeI"
EASTMONEY_DATA_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/query"


def get_stock_tencent(codes: list) -> dict:
    """腾讯API获取个股涨跌幅"""
    result = {}
    try:
        url = f"https://qt.gtimg.cn/q={','.join(codes)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('gbk', errors='ignore')
        for line in data.split(';'):
            if '~' not in line:
                continue
            if 'v_' in line:
                code = line.split('v_')[1].split('=')[0]
            else:
                continue
            parts = line.split('~')
            name = parts[1] if len(parts) > 1 else ""
            change = float(parts[32]) if len(parts) > 32 and parts[32] else 0
            result[code] = {"name": name, "change_pct": change}
    except Exception as e:
        print(f"  ⚠️ 腾讯API失败: {e}")
    return result


def get_industry_browser(code: str) -> str:
    """用agent-browser获取个股行业归属"""
    try:
        if code.startswith('6') or code.startswith('688'):
            url = f"https://quote.eastmoney.com/sh{code}.html"
        else:
            url = f"https://quote.eastmoney.com/sz{code}.html"
        
        r1 = subprocess.run(["agent-browser", "open", url], 
                           capture_output=True, text=True, timeout=15)
        subprocess.run(["agent-browser", "wait", "2000"], 
                      capture_output=True, text=True, timeout=5)
        r2 = subprocess.run(["agent-browser", "get", "text", "@e89"], 
                           capture_output=True, text=True, timeout=10)
        industry = r2.stdout.strip()
        if industry and len(industry) < 20:
            return industry
    except Exception as e:
        pass
    return ""


def get_sector_data_eastmoney(industry: str) -> dict:
    """用eastmoney_financial_data获取板块涨跌幅和主力净额"""
    try:
        query = f"{industry}板块今日涨跌幅主力净流入"
        payload = json.dumps({"toolQuery": query}).encode()
        req = urllib.request.Request(
            EASTMONEY_DATA_URL,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'apikey': EASTMONEY_APIKEY
            },
            method='POST'
        )
        resp = urllib.request.urlopen(req, timeout=15)
        d = json.loads(resp.read())
        tables = d.get('data',{}).get('data',{}).get('searchDataResultDTO',{}).get('dataTableDTOList',[])
        if not tables:
            return {}
        t = tables[0]
        table = t.get('table', {})
        return {
            'sector_change_pct': table.get('f3', [None])[0],
            'sector_main_inflow': table.get('f62', [None])[0],
        }
    except Exception as e:
        return {}


def format_money(val):
    if val is None or val == 'N/A':
        return "N/A"
    try:
        s = str(val)
        # 已经是格式化字符串（如 -3.161亿元）
        if '亿' in s or '万' in s:
            return s.replace('元','')
        f = float(s)
        if abs(f) >= 1e8: return f"{f/1e8:+.2f}亿"
        elif abs(f) >= 1e4: return f"{f/1e4:+.2f}万"
        return f"{f:+.0f}"
    except:
        return str(val)

def format_pct(val):
    if val is None or val == 'N/A':
        return "N/A"
    s = str(val)
    if '%' in s:
        return s
    try:
        return f"{float(s):+.2f}%"
    except:
        return s


def analyze(framework: str, top_n: int = 10):
    today = datetime.now().strftime("%Y-%m-%d")
    scores_file = WORKSPACE / f"{framework}_output" / f"{framework}_scores.json"
    if not scores_file.exists():
        print(f"❌ 找不到 {scores_file}"); sys.exit(1)

    with open(scores_file) as f:
        data = json.load(f)

    all_stocks = []
    if "top_limit_up" in data:
        all_stocks = data.get("top_limit_up", [])[:5] + data.get("top_non_limit_up", [])[:5]
    elif "top5" in data:
        all_stocks = data.get("top5", [])[:top_n]
    else:
        all_stocks = data.get("all_scored", [])[:top_n]

    print(f"\n{'='*70}")
    print(f"📊 板块效应分析 - {framework.upper()} | {today}")
    print(f"{'='*70}")
    print(f"分析股票数: {len(all_stocks)}")

    # Step 1: 腾讯API获取涨跌幅
    print("\n⏳ Step 1: 腾讯API获取涨跌幅...")
    codes = [s["code"] for s in all_stocks]
    tencent_codes = []
    for c in codes:
        if c.startswith('6') or c.startswith('688'):
            tencent_codes.append('sh' + c)
        else:
            tencent_codes.append('sz' + c)
    stock_data = get_stock_tencent(tencent_codes)
    print(f"  ✅ 获取 {len(stock_data)} 只股票涨跌幅")

    # 读取缓存
    cache_file = WORKSPACE / f"{framework}_output" / "sector_cache.json"
    sector_cache = {}
    if cache_file.exists():
        with open(cache_file) as f:
            sector_cache = json.load(f)

    # Step 2: eastmoney_financial_data获取行业+板块数据
    print("\n⏳ Step 2: eastmoney_financial_data获取板块数据...")
    em_count = 0
    for s in all_stocks:
        code, name = s["code"], s["name"]
        # 先用eastmoney_financial_data获取行业归属
        if code not in sector_cache or not sector_cache.get(code, {}).get("industry"):
            result = get_sector_data_eastmoney(f"{name}所属行业板块涨跌幅主力净流入")
            if result.get('industry'):
                sector_cache[code] = sector_cache.get(code, {})
                sector_cache[code].update(result)
                em_count += 1
                print(f"  ✅ {name}: {result.get('industry','')}, 涨跌={result.get('sector_change_pct','N/A')}, 主力={result.get('sector_main_inflow','N/A')}")
                continue
        # 已有行业，获取板块数据
        industry = sector_cache.get(code, {}).get("industry", "")
        if industry and not sector_cache.get(code, {}).get("sector_change_pct"):
            result = get_sector_data_eastmoney(f"{industry}板块今日涨跌幅主力净流入")
            if result:
                sector_cache[code].update(result)
                em_count += 1
                print(f"  ✅ {industry}: 涨跌={result.get('sector_change_pct','N/A')}, 主力={result.get('sector_main_inflow','N/A')}")
    print(f"  共获取 {em_count} 条数据（消耗约{em_count}次额度）")

    # Step 3: agent-browser补齐行业归属（eastmoney_financial_data失败时）
    print("\n⏳ Step 3: agent-browser补齐缺失行业...")
    browser_count = 0
    for s in all_stocks:
        code = s["code"]
        if not sector_cache.get(code, {}).get("industry"):
            industry = get_industry_browser(code)
            if industry:
                sector_cache[code] = sector_cache.get(code, {})
                sector_cache[code]["industry"] = industry
                browser_count += 1
                print(f"  ✅ {s['name']}({code}): {industry}")
    if browser_count:
        print(f"  共补齐 {browser_count} 只股票行业")
    else:
        print(f"  无需补齐")

    # 保存缓存
    with open(cache_file, "w") as f:
        json.dump(sector_cache, f, ensure_ascii=False, indent=2)

    # 输出结果
    print(f"\n{'─'*80}")
    print(f"{'代码':<8} {'名称':<10} {'涨跌%':>6} {'所属板块':<14} {'板块涨跌':>8} {'板块主力':>12}")
    print(f"{'─'*80}")
    for s in all_stocks:
        code, name = s["code"], s["name"]
        t = stock_data.get('sh'+code if code.startswith('6') else 'sz'+code, {})
        c = sector_cache.get(code, {})
        change = t.get("change_pct", s.get("change_pct", 0))
        industry = c.get("industry", "⚠️待获取")
        sector_change = c.get("sector_change_pct", "N/A")
        sector_inflow = c.get("sector_main_inflow", "N/A")
        print(f"{code:<8} {name:<10} {change:>+6.2f}% {industry:<14} {format_pct(sector_change):>8} {format_money(sector_inflow):>12}")

    print(f"\n✅ 分析完成！")
    print(f"  腾讯API: 获取涨跌幅")
    print(f"  eastmoney_financial_data: 获取板块数据 {em_count}条（约{em_count}次额度）")
    print(f"  agent-browser: 补齐行业 {browser_count}只")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--framework", choices=["ztx", "qdk", "b1"], default="ztx")
    p.add_argument("--top", type=int, default=10)
    args = p.parse_args()
    analyze(args.framework, args.top)
