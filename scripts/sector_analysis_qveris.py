#!/usr/bin/env python3
"""
板块效应分析 - QVeris/iFinD 版本 v2.0
功能：通过 QVeris + 同花顺 iFinD 获取个股所属板块、板块涨跌幅、主力净流入
流程：
  1. smart_stock_picking：个股名称 → 申万行业（如"电子--半导体--数字芯片设计"）
  2. code_converter：行业名称 → THS 板块代码（如 881121.TI）
  3. money_flow（scope=sector）：板块涨跌幅 + 主力净流入
  4. money_flow（scope=stock）：个股主力净流入（批量）
用法：python3 scripts/sector_analysis_qveris.py --framework ztx|qdk|b1
"""

import json
import subprocess
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
QVERIS_SCRIPT = Path.home() / ".openclaw/skills/qveris-official/scripts/qveris_tool.mjs"
QVERIS_API_KEY = "sk-PxV8UWOz7UcoaU6yt0rsAfrzmTpSAyW70Qge8jsj-8g"

# Discovery IDs（已验证）
DID_MONEY_FLOW = "76fe554b-8bd6-4584-92e6-646cdb0fd33e"
DID_CODE_CONVERTER = "52383cf3-f5ac-49bd-aa2c-f90aa6e4bb05"
DID_SMART_PICK = "76fe554b-8bd6-4584-92e6-646cdb0fd33e"

# 缓存
SECTOR_CODE_CACHE = {}
INDUSTRY_CACHE = {}


def run_qveris(action: str, *args, params: dict = None) -> dict:
    """调用 QVeris CLI"""
    cmd = ["node", str(QVERIS_SCRIPT), action] + list(args)
    if params:
        cmd += ["--params", json.dumps(params, ensure_ascii=False)]
    cmd += ["--json"]

    env = os.environ.copy()
    env["QVERIS_API_KEY"] = QVERIS_API_KEY

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
        if result.returncode != 0:
            return {"error": result.stderr}
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}


def parse_result(raw: dict) -> dict:
    """统一解析 QVeris 返回结果"""
    return raw.get("result", raw)


def get_stock_sw_industry(stock_name: str) -> str:
    """通过 smart_stock_picking 获取个股申万行业（取二级行业）"""
    if stock_name in INDUSTRY_CACHE:
        return INDUSTRY_CACHE[stock_name]

    result = run_qveris(
        "call", "ths_ifind.smart_stock_picking.v1",
        "--discovery-id", DID_SMART_PICK,
        params={"searchstring": f"{stock_name}所属申万行业"}
    )
    try:
        data = parse_result(result)
        if data.get("status_code") == 200 and data.get("data"):
            industry_full = data["data"][0].get("所属申万行业", "")
            # 格式如 "电子--半导体--数字芯片设计"，取第二级
            parts = industry_full.split("--")
            industry = parts[1].strip() if len(parts) >= 2 else parts[0].strip()
            INDUSTRY_CACHE[stock_name] = industry
            return industry
    except Exception:
        pass
    return ""


def get_sector_code(industry_name: str) -> str:
    """通过行业名称获取 THS 板块代码（优先取 .TI 结尾）"""
    if industry_name in SECTOR_CODE_CACHE:
        return SECTOR_CODE_CACHE[industry_name]

    result = run_qveris(
        "call", "ths_ifind.code_converter.v1",
        "--discovery-id", DID_CODE_CONVERTER,
        params={"mode": "secname", "secname": industry_name, "isexact": "0"}
    )
    try:
        data = parse_result(result)
        if data.get("status_code") == 200:
            codes_str = data["data"][0]["table"]["thscode"][0]
            codes = [c.strip() for c in codes_str.split(",")]
            ti_codes = [c for c in codes if c.endswith(".TI")]
            code = ti_codes[0] if ti_codes else codes[0]
            SECTOR_CODE_CACHE[industry_name] = code
            return code
    except Exception:
        pass
    return ""


def get_sector_flow(sector_code: str, date: str) -> dict:
    """获取板块涨跌幅 + 主力净流入"""
    result = run_qveris(
        "call", "ths_ifind.money_flow.v1",
        "--discovery-id", DID_MONEY_FLOW,
        params={"scope": "sector", "codes": sector_code, "startdate": date, "enddate": date}
    )
    try:
        data = parse_result(result)
        if data.get("status_code") == 200:
            return data["data"][0][0]
    except Exception:
        pass
    return {}


def get_stock_flow(codes: list, date: str) -> dict:
    """批量获取个股主力净流入"""
    codes_str = ",".join(codes)
    result = run_qveris(
        "call", "ths_ifind.money_flow.v1",
        "--discovery-id", DID_MONEY_FLOW,
        params={"scope": "stock", "codes": codes_str, "startdate": date, "enddate": date}
    )
    stock_flow = {}
    try:
        data = parse_result(result)
        if data.get("status_code") == 200:
            for item_list in data["data"]:
                for item in item_list:
                    stock_flow[item["code"]] = item
    except Exception:
        pass
    return stock_flow


def format_money(amount) -> str:
    """格式化金额"""
    if amount is None:
        return "N/A"
    amount = float(amount)
    if abs(amount) >= 1e8:
        return f"{amount/1e8:+.2f}亿"
    elif abs(amount) >= 1e4:
        return f"{amount/1e4:+.2f}万"
    return f"{amount:+.0f}"


def get_ths_code(stock_code: str) -> str:
    """将股票代码转换为 THS 格式"""
    if "." in stock_code:
        return stock_code
    if stock_code.startswith("688") or stock_code.startswith("6"):
        return f"{stock_code}.SH"
    return f"{stock_code}.SZ"


def analyze(framework: str, top_n: int = 10):
    """主分析函数"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 读取对应框架的 scores.json
    scores_file = WORKSPACE / f"{framework}_output" / f"{framework}_scores.json"
    if not scores_file.exists():
        print(f"❌ 找不到 {scores_file}")
        sys.exit(1)

    with open(scores_file, encoding="utf-8") as f:
        data = json.load(f)

    # 兼容不同框架的数据结构
    if "top_limit_up" in data or "top_non_limit_up" in data:
        # ztx 格式
        all_stocks = data.get("top_limit_up", [])[:5] + data.get("top_non_limit_up", [])[:5]
    elif "top5" in data:
        # qdk / b1 格式
        all_stocks = data.get("top5", [])[:top_n]
    else:
        all_stocks = data.get("all_scored", data.get("scored", []))[:top_n]

    print(f"\n{'='*70}")
    print(f"📊 板块效应分析 - {framework.upper()} | {today}")
    print(f"{'='*70}")
    print(f"分析股票数: {len(all_stocks)}")

    # Step 1: 批量获取个股资金流向
    print("\n⏳ Step 1: 获取个股资金流向...")
    ths_codes = [get_ths_code(s["code"]) for s in all_stocks]
    stock_flows = get_stock_flow(ths_codes, today)

    # Step 2: 获取申万行业 + 板块数据
    print("⏳ Step 2: 获取申万行业 + 板块资金流向...")
    sector_results = {}
    seen_industries = {}

    for stock in all_stocks:
        code = stock["code"]
        name = stock["name"]
        ths_code = get_ths_code(code)

        # 获取申万行业
        industry = get_stock_sw_industry(name)

        # 获取板块资金流向（同一行业只查一次）
        sector_flow = {}
        if industry:
            if industry not in seen_industries:
                sector_code = get_sector_code(industry)
                if sector_code:
                    sector_flow = get_sector_flow(sector_code, today)
                    seen_industries[industry] = sector_flow
                    print(f"  {name} → {industry} ({sector_code}) 涨跌:{sector_flow.get('change_pct', 'N/A')}%")
                else:
                    seen_industries[industry] = {}
            else:
                sector_flow = seen_industries[industry]

        # 个股资金流向
        stock_flow = stock_flows.get(ths_code, {})

        sector_results[code] = {
            "code": code,
            "name": name,
            "industry": industry,
            "change_pct": stock.get("change_pct", 0),
            "score": stock.get("score", 0),
            "stock_main_inflow": stock_flow.get("main_net_inflow"),
            "sector_name": sector_flow.get("sector_name", industry),
            "sector_change_pct": sector_flow.get("change_pct"),
            "sector_main_inflow": sector_flow.get("main_net_inflow"),
            "sector_rise_count": sector_flow.get("rise_count"),
            "sector_fall_count": sector_flow.get("fall_count"),
        }

    # 输出结果
    print(f"\n{'─'*90}")
    print(f"{'代码':<8} {'名称':<10} {'涨跌%':>6} {'个股主力':>10} {'申万行业':<10} {'板块涨跌%':>8} {'板块主力':>10} {'涨/跌家数':>8}")
    print(f"{'─'*90}")

    for stock in all_stocks:
        r = sector_results.get(stock["code"], {})
        rise = r.get("sector_rise_count")
        fall = r.get("sector_fall_count")
        rise_fall = f"{rise}↑{fall}↓" if rise is not None else "N/A"
        print(
            f"{r.get('code',''):<8} "
            f"{r.get('name',''):<10} "
            f"{r.get('change_pct', 0):>+6.2f}% "
            f"{format_money(r.get('stock_main_inflow')):>10} "
            f"{r.get('industry', 'N/A'):<10} "
            f"{r.get('sector_change_pct') or 0:>+8.2f}% "
            f"{format_money(r.get('sector_main_inflow')):>10} "
            f"{rise_fall:>8}"
        )

    # 保存结果
    output_file = WORKSPACE / f"{framework}_output" / "sector_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(list(sector_results.values()), f, ensure_ascii=False, indent=2)

    print(f"\n✅ 板块分析完成，已保存到 {output_file}")
    return sector_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", choices=["ztx", "qdk", "b1"], default="ztx")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()
    analyze(args.framework, args.top)
