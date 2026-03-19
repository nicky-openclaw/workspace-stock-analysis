#!/usr/bin/env python3
"""
B1选股主控脚本 v2.0
按步骤调用子脚本，每步验证输出文件存在才继续
"""

import subprocess
import sys
import os
import json
from pathlib import Path

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
OUTPUT_DIR = WORKSPACE / "b1_output"
SCRIPTS_DIR = WORKSPACE / "scripts"

STEPS = [
    {
        "name": "Step 1: 图片识别",
        "script": "b1_step2_fetch.py",
        "output": "b1_stocks.json",
        "desc": "读取股票代码清单（需手动提供或由图片识别生成）"
    },
    {
        "name": "Step 2: K线数据拉取",
        "script": "b1_step2_fetch.py",
        "output": "b1_kline.json",
        "desc": "拉取120日K线，沪市用sh前缀，深市用sz前缀"
    },
    {
        "name": "Step 3: 指标计算",
        "script": "b1_step3_calc.py",
        "output": "b1_indicators.json",
        "desc": "计算MA5/MA10/MA20/J值/RSI/量比等指标"
    },
    {
        "name": "Step 4: 综合评分",
        "script": "b1_step4_score.py",
        "output": "b1_scores.json",
        "desc": "五层评分体系，硬淘汰+综合打分"
    },
]

def check_output(output_file):
    path = OUTPUT_DIR / output_file
    if not path.exists():
        return False, f"❌ 文件不存在: {path}"
    try:
        with open(path) as f:
            data = json.load(f)
        return True, f"✅ {output_file} ({len(str(data))} bytes)"
    except Exception as e:
        return False, f"❌ 文件损坏: {e}"

def run_step(step):
    script_path = SCRIPTS_DIR / step["script"]
    print(f"\n{'='*60}")
    print(f"🚀 {step['name']}")
    print(f"   {step['desc']}")
    print(f"{'='*60}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True, text=True
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"[STDERR] {result.stderr[:500]}")

    if result.returncode != 0:
        print(f"❌ 脚本执行失败 (code {result.returncode})")
        return False

    ok, msg = check_output(step["output"])
    print(f"输出验证: {msg}")
    return ok

def main():
    print("🏗️  B1选股主控脚本 v2.0")
    print(f"输出目录: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 检查 b1_stocks.json 是否已存在（Step 1 由Agent手动提供）
    stocks_file = OUTPUT_DIR / "b1_stocks.json"
    if not stocks_file.exists():
        print("\n⚠️  b1_stocks.json 不存在！")
        print("请先运行图片识别，生成股票代码清单。")
        print("格式参考: scripts/b1_stocks_template.json")
        sys.exit(1)

    ok, msg = check_output("b1_stocks.json")
    print(f"\n股票清单: {msg}")
    with open(stocks_file) as f:
        stocks = json.load(f)
    print(f"共 {stocks.get('total', '?')} 只股票待处理")

    # 依次执行 Step 2-4
    for step in STEPS[1:]:  # 跳过Step1（已有文件）
        success = run_step(step)
        if not success:
            print(f"\n❌ {step['name']} 失败，终止执行。请检查错误后重试。")
            sys.exit(1)

    # 最终输出
    print(f"\n{'='*60}")
    print("✅ 所有步骤完成！")
    scores_path = OUTPUT_DIR / "b1_scores.json"
    with open(scores_path) as f:
        scores = json.load(f)

    top10 = scores.get("top10", [])
    eliminated = scores.get("eliminated_count", 0)
    total = scores.get("total", 0)

    print(f"\n📊 B1选股结果")
    print(f"总股票数: {total} | 淘汰: {eliminated} | 进入评分: {total - eliminated}")
    print(f"\n{'排名':>4} {'代码':>6} {'名称':<8} {'涨幅%':>6} {'量能':>8} {'J值':>5} {'RSI':>5} {'B1':>4} {'评分':>5} 明细")
    print("-" * 90)
    for i, s in enumerate(top10, 1):
        print(
            f"{i:>4} {s.get('code','-'):>6} {s.get('name','-'):<8} "
            f"{s.get('change_pct', 0):>+6.2f}% "
            f"{s.get('volume_signal',''):>8} "
            f"{s.get('j_value', '-'):>5} "
            f"{s.get('rsi', '-'):>5} "
            f"{'✅' if s.get('b1_triggered') else '❌':>4} "
            f"{s.get('score', 0):>5} "
            f"{s.get('score_detail', '')}"
        )
    print(f"\n数据日期: {scores.get('data_date', '?')}")

if __name__ == "__main__":
    main()
