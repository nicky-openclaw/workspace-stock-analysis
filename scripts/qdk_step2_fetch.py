#!/usr/bin/env python3
"""
Step 2: K线数据拉取
读取 qdk_stocks.json，批量拉取120日K线 + 实时数据
沪市/科创板用 sh 前缀，深市/创业板用 sz 前缀，北交所跳过（需浏览器）
自动调用 qdk_auto_recognize.py 进行识图

关键：涨幅必须用实时API字段32，不自己计算！
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
OUTPUT_DIR = WORKSPACE / "qdk_output"
SCRIPTS_DIR = WORKSPACE / "scripts"

KLINE_API = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,120,"
REALTIME_API = "https://qt.gtimg.cn/q={code}"


def get_latest_trading_day() -> str:
    """
    获取最近交易日（A股）
    周末返回上周五，节假日返回前一交易日
    """
    today = datetime.now()
    weekday = today.weekday()
    
    # Saturday = 5, Sunday = 6
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


def fetch_realtime(prefix: str, code: str) -> Optional[dict]:
    """获取实时行情数据，包括涨跌幅字段32"""
    if prefix == "bj":
        return None  # 北交所需要浏览器

    full_code = f"{prefix}{code}"
    url = REALTIME_API.format(code=full_code)

    try:
        resp = requests.get(url, timeout=3)
        text = resp.text

        # 解析 v_xxx="1~名称~代码~现价~昨收..."
        match = re.search(r'v_\w+="(.+)"', text)
        if not match:
            return None

        fields = match.group(1).split('~')
        if len(fields) < 33:
            return None

        # 字段32是涨跌幅%（直接使用）
        current_price = float(fields[3]) if fields[3] else 0
        yesterday_close = float(fields[4]) if fields[4] else 0
        change_pct = float(fields[32]) if fields[32] else 0
        change_amount = float(fields[31]) if fields[31] else 0
        volume = float(fields[6]) if fields[6] else 0

        return {
            "current_price": current_price,
            "yesterday_close": yesterday_close,
            "change_pct": change_pct,  # 字段32，直接使用！
            "change_amount": change_amount,
            "volume": volume,
        }
    except Exception as e:
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
    """
    自动检查股票清单状态，并自动调用识图脚本
    
    重要逻辑（2026-03-17修复）：
    - 如果 qdk_stocks.json 不存在 → 自动调用识图脚本
    - 如果日期不匹配 → 自动调用识图脚本，然后重新检查
    - 只有日期匹配时才继续执行
    
    修复：不再要求 Agent 手动执行识图，改为自动调用
    """
    print("🔍 检查股票清单状态...")
    
    stocks_file = OUTPUT_DIR / "qdk_stocks.json"
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    
    # 检查文件是否存在
    if not stocks_file.exists():
        print("  qdk_stocks.json 不存在，自动调用识图脚本...")
        run_recognize_script()
        # 再次检查
        if not stocks_file.exists():
            print("❌ 错误: 识图脚本执行后仍不存在！")
            sys.exit(1)
    
    # 检查日期是否匹配
    with open(stocks_file) as f:
        data = json.load(f)
        file_date = data.get("date", "")
        
        if file_date != today:
            print(f"  qdk_stocks.json 日期不匹配（{file_date} vs {today}），自动调用识图脚本...")
            run_recognize_script()
            # 重新检查日期
            with open(stocks_file) as f2:
                data2 = json.load(f2)
                file_date2 = data2.get("date", "")
                if file_date2 != today:
                    print(f"❌ 错误: 识图后日期仍不匹配！")
                    print(f"   识图后日期: {file_date2}")
                    print(f"   当前日期: {today}")
                    sys.exit(1)
        
        print(f"  ✅ qdk_stocks.json 已存在，日期匹配: {file_date}")


def run_recognize_script():
    """自动调用识图脚本"""
    import subprocess
    recognize_script = SCRIPTS_DIR / "qdk_auto_recognize.py"
    print(f"  执行: python3 {recognize_script}")
    try:
        result = subprocess.run(
            ["python3", str(recognize_script)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(WORKSPACE)
        )
        if result.returncode != 0:
            print(f"  ⚠️ 识图脚本执行失败: {result.stderr}")
        else:
            print(f"  ✅ 识图完成")
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"     {line}")
    except Exception as e:
        print(f"  ⚠️ 调用识图脚本异常: {e}")

def main():
    # 自动调用识别脚本
    auto_recognize()
    
    # 读取股票清单
    stocks_file = OUTPUT_DIR / "qdk_stocks.json"
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
    date_warnings = []  # 日期校验警告

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
            
            # ===== 日期校验 =====
            kline = data.get("kline", [])
            if kline:
                kline_date = kline[-1][0]  # K线最后一条日期
                # 校验K线日期是否匹配最近交易日
                if kline_date != latest_trading_day:
                    # 可能是周五数据（周末）或更早
                    date_warnings.append({
                        "code": code, 
                        "kline_date": kline_date, 
                        "expected": latest_trading_day
                    })
                data["kline_date"] = kline_date  # 记录K线实际日期
            
            # 关键：同时获取实时数据（涨跌幅）
            realtime = fetch_realtime(prefix, code)
            if realtime:
                data["realtime"] = realtime
                data["change_pct"] = realtime["change_pct"]  # 字段32，直接使用
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
        "latest_trading_day": latest_trading_day,  # 记录最近交易日
        "data_date": stocks_data.get("date", "unknown"),
        "stocks": results,
        "failed": failed,
        "bj_skipped": bj_skipped,
        "date_warnings": date_warnings,  # 日期校验结果
    }

    output_file = OUTPUT_DIR / "qdk_kline.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ K线拉取完成")
    print(f"   成功: {len(results)} | 失败: {len(failed)} | 北交所跳过: {len(bj_skipped)}")
    print(f"   输出: {output_file}")

    # 日期校验警告
    if date_warnings:
        print(f"\n⚠️  日期校验警告: {len(date_warnings)} 只股票的K线日期不是 {latest_trading_day}")
        print(f"   示例: {date_warnings[:3]}")
        print(f"   提示: 这可能是周末（非交易日），K线数据为最近交易日的收盘数据")

    if failed:
        print(f"\n⚠️  失败列表（前10）: {[s['code'] for s in failed[:10]]}")

if __name__ == "__main__":
    main()
