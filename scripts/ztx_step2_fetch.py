#!/usr/bin/env python3
"""
Step 2: K线数据拉取
读取 ztx_stocks.json，批量拉取120日K线
沪市/科创板用 sh 前缀，深市/创业板用 sz 前缀，北交所跳过（需浏览器）
自动调用 ztx_auto_recognize.py 进行识图
"""

import requests
import json
import time
import re
import subprocess
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
OUTPUT_DIR = WORKSPACE / "ztx_output"
SCRIPTS_DIR = WORKSPACE / "scripts"

KLINE_API = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,120,qfq"
REALTIME_API = "https://qt.gtimg.cn/q={code}"


def get_latest_trading_day() -> str:
    """获取最近交易日（A股）- 修复版"""
    now = datetime.now()
    today = now.date()
    weekday = now.weekday()
    
    # 周末判断
    if weekday == 5:  # 周六
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    elif weekday == 6:  # 周日
        return (now - timedelta(days=2)).strftime("%Y-%m-%d")
    
    # 周一到周五：判断当前是否在交易时段
    # A股交易时间：9:30-11:30, 13:00-15:00
    current_time = now.time()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0).time()
    market_close = now.replace(hour=15, minute=0, second=0, microsecond=0).time()
    morning_open = now.replace(hour=9, minute=30, second=0, microsecond=0).time()
    morning_close = now.replace(hour=11, minute=30, second=0, microsecond=0).time()
    afternoon_open = now.replace(hour=13, minute=0, second=0, microsecond=0).time()
    afternoon_close = now.replace(hour=15, minute=0, second=0, microsecond=0).time()
    
    # 在交易时段内，返回今天
    if (morning_open <= current_time <= morning_close) or (afternoon_open <= current_time <= afternoon_close):
        return now.strftime("%Y-%m-%d")
    # 非交易时段，返回昨天
    else:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")


def get_prefix(code: str) -> str:
    """根据股票代码确定市场前缀"""
    if code.startswith("688") or code.startswith("6"):
        return "sh"
    elif code.startswith("0") or code.startswith("3"):
        return "sz"
    else:
        return "bj"  # 北交所


def fetch_realtime(prefix: str, code: str) -> Optional[dict]:
    """获取实时行情数据，包括涨跌幅字段32"""
    if prefix == "bj":
        return None

    full_code = f"{prefix}{code}"
    url = REALTIME_API.format(code=full_code)

    try:
        resp = requests.get(url, timeout=3)
        text = resp.text
        match = re.search(r'v_\w+="(.+)"', text)
        if not match:
            return None

        fields = match.group(1).split('~')
        if len(fields) < 33:
            return None

        return {
            "current_price": float(fields[3]) if fields[3] else 0,
            "yesterday_close": float(fields[4]) if fields[4] else 0,
            "change_pct": float(fields[32]) if fields[32] else 0,
            "change_amount": float(fields[31]) if fields[31] else 0,
            "volume": float(fields[6]) if fields[6] else 0,
        }
    except Exception:
        return None

def fetch_kline(prefix: str, code: str) -> Optional[dict]:
    """拉取单只股票120日K线"""
    if prefix == "bj":
        return None  # 北交所需要浏览器，跳过

    full_code = f"{prefix}{code}"
    url = KLINE_API.format(code=full_code)

    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        stock_data = data.get("data", {}).get(full_code, {})

        # 获取K线数据
        kline = stock_data.get("qfqday") or stock_data.get("day", [])
        qt = stock_data.get("qt", {})

        if not kline or len(kline) < 5:
            return None

        return {
            "code": code,
            "prefix": prefix,
            "full_code": full_code,
            "kline": kline,  # [[date, open, close, high, low, vol], ...]
            "qt": qt,
        }
    except Exception as e:
        return None

def auto_recognize():
    """自动调用识别脚本"""
    print("🔍 检查是否需要自动识图...")
    
    stocks_file = OUTPUT_DIR / "ztx_stocks.json"
    
    if not stocks_file.exists():
        print("  ztx_stocks.json 不存在，调用识别脚本...")
    else:
        with open(stocks_file) as f:
            data = json.load(f)
            file_date = data.get("date", "")
            from datetime import datetime
            today = datetime.now().strftime("%Y%m%d")
            if file_date != today:
                print(f"  日期不匹配({file_date} vs {today})，调用识别脚本...")
            else:
                print(f"  ztx_stocks.json 已存在且日期匹配，跳过识别")
                return
    
    script_path = SCRIPTS_DIR / "ztx_auto_recognize.py"
    if script_path.exists():
        print("  执行自动识别...")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  ✅ 自动识别完成")
        else:
            print(f"  ⚠️ 识别失败: {result.stderr}")
    else:
        print(f"  ⚠️ 识别脚本不存在: {script_path}")

def main():
    # 自动调用识别脚本
    auto_recognize()
    
    # 读取股票清单
    stocks_file = OUTPUT_DIR / "ztx_stocks.json"
    with open(stocks_file) as f:
        stocks_data = json.load(f)

    # 获取最近交易日
    latest_trading_day = get_latest_trading_day()
    print(f"📅 最近交易日: {latest_trading_day}")

    stocks = stocks_data["stocks"]
    total = len(stocks)
    print(f"共 {total} 只股票，开始拉取120日K线...")

    results = []
    failed = []
    bj_skipped = []
    date_warnings = []

    for i, stock in enumerate(stocks):
        code = stock["code"]
        name = stock.get("name", code)
        prefix = get_prefix(code)

        if prefix == "bj":
            bj_skipped.append({"code": code, "name": name})
            if (i + 1) % 50 == 0:
                print(f"  进度: {i+1}/{total} | 成功: {len(results)} | 失败: {len(failed)} | 北交所跳过: {len(bj_skipped)}")
            continue

        data = fetch_kline(prefix, code)

        if data:
            data["name"] = name
            
            # 日期校验
            kline = data.get("kline", [])
            if kline:
                kline_date = kline[-1][0]
                if kline_date != latest_trading_day:
                    date_warnings.append({"code": code, "kline_date": kline_date, "expected": latest_trading_day})
                data["kline_date"] = kline_date
            
            # 获取实时涨跌幅（字段32）
            realtime = fetch_realtime(prefix, code)
            if realtime:
                data["realtime"] = realtime
                data["change_pct"] = realtime["change_pct"]
                data["current_price"] = realtime["current_price"]
            
            results.append(data)
        else:
            failed.append({"code": code, "name": name, "prefix": prefix})

        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{total} | 成功: {len(results)} | 失败: {len(failed)}")

        time.sleep(0.08)

    # 输出结果
    output = {
        "total": total,
        "success_count": len(results),
        "failed_count": len(failed),
        "bj_skipped_count": len(bj_skipped),
        "latest_trading_day": latest_trading_day,
        "data_date": stocks_data.get("date", "unknown"),
        "stocks": results,
        "failed": failed,
        "bj_skipped": bj_skipped,
        "date_warnings": date_warnings,
    }

    output_file = OUTPUT_DIR / "ztx_kline.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ K线拉取完成")
    print(f"   成功: {len(results)} | 失败: {len(failed)} | 北交所跳过: {len(bj_skipped)}")
    print(f"   输出: {output_file}")

    if date_warnings:
        print(f"\n⚠️  日期校验警告: {len(date_warnings)} 只股票的K线日期不是 {latest_trading_day}")

    if failed:
        print(f"\n⚠️  失败列表（前10）: {[s['code'] for s in failed[:10]]}")

if __name__ == "__main__":
    main()
