#!/usr/bin/env python3
"""
Step 2: K线数据拉取
读取 b1_stocks.json，批量拉取120日K线
沪市/科创板用 sh 前缀，深市/创业板用 sz 前缀，北交所跳过（需浏览器）
自动调用 b1_auto_recognize.py 进行识图
"""

import requests
import json
import time
import subprocess
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
OUTPUT_DIR = WORKSPACE / "b1_output"
SCRIPTS_DIR = WORKSPACE / "scripts"

KLINE_API = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,120,qfq"


def auto_recognize():
    """自动调用识别脚本"""
    print("🔍 检查是否需要自动识图...")
    
    stocks_file = OUTPUT_DIR / "b1_stocks.json"
    
    # 检查文件是否存在
    if not stocks_file.exists():
        print("  b1_stocks.json 不存在，调用识别脚本...")
    else:
        # 检查日期是否匹配今天
        with open(stocks_file) as f:
            data = json.load(f)
            file_date = data.get("date", "")
            from datetime import datetime
            today = datetime.now().strftime("%Y%m%d")
            if file_date != today:
                print(f"  日期不匹配({file_date} vs {today})，调用识别脚本...")
            else:
                print(f"  b1_stocks.json 已存在且日期匹配，跳过识别")
                return
    
    # 调用识别脚本
    script_path = SCRIPTS_DIR / "b1_auto_recognize.py"
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


def get_latest_trading_day() -> str:
    """获取最近交易日（A股）"""
    today = datetime.now()
    weekday = today.weekday()
    if weekday == 5:  # 周六
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif weekday == 6:  # 周日
        return (today - timedelta(days=2)).strftime("%Y-%m-%d")
    else:
        return today.strftime("%Y-%m-%d")

def get_prefix(code: str) -> str:
    """根据股票代码确定市场前缀"""
    if code.startswith("688") or code.startswith("6"):
        return "sh"
    elif code.startswith("0") or code.startswith("3"):
        return "sz"
    else:
        return "bj"  # 北交所

from typing import Optional

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

def main():
    # 自动调用识别脚本
    auto_recognize()
    
    # 读取股票清单
    stocks_file = OUTPUT_DIR / "b1_stocks.json"
    with open(stocks_file) as f:
        stocks_data = json.load(f)

    # 支持数组格式和字典格式
    if isinstance(stocks_data, list):
        stocks = stocks_data
    else:
        stocks = stocks_data["stocks"]
    
    # 获取最近交易日
    latest_trading_day = get_latest_trading_day()
    print(f"📅 最近交易日: {latest_trading_day}")
    
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
            results.append(data)
        else:
            failed.append({"code": code, "name": name, "prefix": prefix})

        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{total} | 成功: {len(results)} | 失败: {len(failed)}")

        time.sleep(0.08)

    # 输出结果
    data_date = stocks_data[0].get("date") if isinstance(stocks_data, list) and len(stocks_data) > 0 else "unknown"
    
    output = {
        "total": total,
        "success_count": len(results),
        "failed_count": len(failed),
        "bj_skipped_count": len(bj_skipped),
        "latest_trading_day": latest_trading_day,
        "data_date": data_date,
        "stocks": results,
        "failed": failed,
        "bj_skipped": bj_skipped,
        "date_warnings": date_warnings,
    }

    output_file = OUTPUT_DIR / "b1_kline.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ K线拉取完成")
    print(f"   成功: {len(results)} | 失败: {len(failed)} | 北交所跳过: {len(bj_skipped)}")
    print(f"   输出: {output_file}")

    if date_warnings:
        print(f"\n⚠️  日期校验警告: {len(date_warnings)} 只股票的K线日期不是 {latest_trading_day}")
        print(f"   示例: {date_warnings[:3]}")

    if failed:
        print(f"\n⚠️  失败列表（前10）: {[s['code'] for s in failed[:10]]}")

if __name__ == "__main__":
    main()
