#!/usr/bin/env python3
"""
砖型图选股 Step 4: 五层综合评分
硬淘汰 + 趋势质量 + 砖型图信号（核心）+ B信号质量 + 量能验证 + 涨幅确认
"""

import json
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
OUTPUT_DIR = WORKSPACE / "ztx_output"


def get_limit_up_threshold(code: str) -> float:
    """根据代码判断涨停阈值"""
    if code.startswith("688") or code.startswith("300") or code.startswith("301"):
        return 19.9  # 科创板/创业板
    elif code.startswith("8") or code.startswith("4") or code.startswith("9"):
        return 28.0  # 北交所
    else:
        return 9.9   # 沪深主板


def score_stock(s: dict) -> Optional[dict]:
    """
    五层综合评分（满分100分）
    硬淘汰：白线<黄线 / 跌破白线 / 砖型持续走弱 → 返回 None
    """
    code = s["code"]
    name = s["name"]
    ma5 = s.get("ma5")
    ma10 = s.get("ma10")
    ma20 = s.get("ma20")
    ma20_rising = s.get("ma20_rising")
    j = s.get("j_value")
    rsi = s.get("rsi")
    change_pct = s.get("change_pct", 0)
    today_close = s.get("today_close", 0)
    vol_ratio = s.get("vol_ratio", 1.0)

    # 砖型图数据
    ztx_today = s.get("ztx_today")
    ztx_yesterday = s.get("ztx_yesterday")
    ztx_3d_rising = s.get("ztx_3d_consecutive_rising", False)
    green_to_red = s.get("green_to_red", False)  # 绿转红信号
    red_strength = s.get("red_strength", False)  # 红柱强化
    red_green_ratio = s.get("red_green_ratio", 0)  # 红绿比
    strong_red = s.get("strong_red", False)  # 强红信号（绿转红且红绿比≥0.666）

    # B信号
    b1_triggered = s.get("b1_triggered", False)
    b2_triggered = s.get("b2_triggered", False)

    # 趋势线（白线/黄线）
    white_line = s.get("white_line")
    yellow_line = s.get("yellow_line")

    # 20日最低量（地量判断）
    min_vol_20 = s.get("min_vol_20")
    today_vol = s.get("today_vol")

    limit_up_threshold = get_limit_up_threshold(code)

    # ────────────── 硬淘汰（使用真实白线/黄线）──────────────
    # 白线 < 黄线：趋势向下
    if white_line and yellow_line and white_line < yellow_line:
        return None
    # 收盘跌破白线
    if white_line and today_close < white_line:
        return None
    # 砖型图持续走弱：连续3日下降且今日砖型值<0
    if ztx_3d_rising is False and ztx_today is not None and ztx_today < 0:
        return None

    score = 0
    detail = []

    # ────────────── 第一层：趋势质量（20分）──────────────
    # 砖型图知识库：双线确认 = 股价在黄线之上，白线在黄线之上
    layer1 = 0
    if white_line and yellow_line and white_line >= yellow_line:
        layer1 += 8
        detail.append("白线≥黄线+8")
    if ma20_rising is True:
        layer1 += 7
        detail.append("MA20↑+7")
    if white_line and yellow_line and white_line >= yellow_line and ma20_rising is True:
        layer1 += 5
        detail.append("双线确认+5")
    score += layer1

    # ────────────── 第二层：砖型图信号（40分，核心层）──────────────
    # 砖型图是短线核心：强红信号（绿转红+红绿比≥0.666）是最强买入信号
    # 2026-03-17 优化：弱红降权（8分），强红保持30分
    layer2 = 0
    if ztx_today is not None and ztx_yesterday is not None:
        # 强红信号（知识库核心）：绿转红 且 红柱≥绿柱2/3
        if strong_red:
            layer2 += 30
            detail.append(f"强红(红绿比{red_green_ratio:.2f})+30")
        # 弱红（绿转红但红绿比不足2/3）：降权为8分，仅作参考
        elif green_to_red:
            layer2 += 8
            detail.append(f"弱红(红绿比{red_green_ratio:.2f})+8")
        # 红柱强化：今日上涨且砖型值>0（非绿转红）
        elif red_strength:
            layer2 += 15
            detail.append("红柱强化+15")

        # 砖型走强（可叠加）
        if ztx_today > ztx_yesterday and not strong_red:
            layer2 += 8
            detail.append(f"走强+8")

        # 砖型值>100强势区
        if ztx_today > 100:
            layer2 += 5
            detail.append(f">100+5")

        # 连续3日走强
        if ztx_3d_rising:
            layer2 += 5
            detail.append("连续走强+5")

    layer2 = min(layer2, 40)  # 上限40分
    score += layer2

    # ────────────── 第三层：量能验证（15分）──────────────
    # 2026-03-17 优化：量能层从10分提升至15分
    layer3 = 0
    vol_signal = "正常"
    if vol_ratio >= 1.5:
        layer3 = 15
        vol_signal = f"放量{vol_ratio:.1f}x"
        detail.append(f"放量+15")
    elif min_vol_20 and today_vol and today_vol < min_vol_20 * 1.2:
        layer3 = 10
        vol_signal = "地量"
        detail.append("地量+10")
    score += layer3

    # ────────────── 第四层：涨幅确认（15分）──────────────
    # 2026-03-17 优化：涨幅层从10分提升至15分
    layer4 = 0

    # ────────────── 第五层：涨幅确认（10分）──────────────
    layer5 = 0
    is_limit_up = change_pct >= limit_up_threshold
    if is_limit_up:
        layer4 = 15
        detail.append("涨停+15")
    elif change_pct >= 5:
        layer4 = 10
        detail.append("强势+10")
    elif change_pct >= 2:
        layer4 = 6
        detail.append("中势+6")
    elif change_pct >= 0:
        layer4 = 2
        detail.append("弱势+2")
    score += layer4

    # ────────────── B信号辅助加分（上限15分，可溢出至100）──────────────
    # 2026-03-17 优化：B信号从独立评分层改为辅助加分
    # 砖型图和B1/B2是两套独立体系，B信号作为锦上添花，不作为主要评分依据
    b_bonus = 0
    b_signal = "无"
    if b1_triggered:
        b_bonus = 15
        b_signal = "B1✅"
        detail.append("B1辅助+15")
    elif b2_triggered:
        b_bonus = 10
        b_signal = "B2✅"
        detail.append("B2辅助+10")
    else:
        if j is not None and j < 14:
            b_bonus += 5
            detail.append("J超卖+5")
        if rsi is not None and rsi < 23:
            b_bonus += 3
            detail.append("RSI超卖+3")
        b_bonus = min(b_bonus, 8)
    score += b_bonus

    score = min(score, 100)

    return {
        "code": code,
        "name": name,
        "score": score,
        "is_limit_up": is_limit_up,
        "b_signal": b_signal,
        "vol_signal": vol_signal,
        "white_line": s.get("white_line"),
        "yellow_line": s.get("yellow_line"),
        "white_above_yellow": s.get("white_line", 0) >= s.get("yellow_line", 0) if s.get("white_line") and s.get("yellow_line") else False,
        "b1_triggered": s.get("b1_triggered", False),
        "b2_triggered": s.get("b2_triggered", False),
        "change_pct": change_pct,
        "ztx_today": ztx_today,
        "ztx_yesterday": ztx_yesterday,
        "j_value": j,
        "rsi": rsi,
        "vol_ratio": vol_ratio,
        "ma5": ma5,
        "ma20": ma20,
        "ma20_rising": ma20_rising,
        "limit_up_threshold": limit_up_threshold,
        "score_detail": " | ".join(detail),
        "score_breakdown": {
            "trend": layer1,
            "ztx_signal": layer2,
            "volume": layer3,
            "momentum": layer4,
            "b_bonus": b_bonus,
        }
    }


def main():
    indicators_file = OUTPUT_DIR / "ztx_indicators.json"
    with open(indicators_file, encoding="utf-8") as f:
        data = json.load(f)

    stocks = data["stocks"]
    total = len(stocks)
    print(f"共 {total} 只股票，开始五层评分...")

    limit_up_stocks = []
    non_limit_up_stocks = []
    eliminated = []

    for s in stocks:
        result = score_stock(s)
        if result is None:
            white_line = s.get("white_line")
            yellow_line = s.get("yellow_line")
            today_close = s.get("today_close", 0)
            if white_line and yellow_line and white_line < yellow_line:
                reason = "白线<黄线"
            elif white_line and today_close < white_line:
                reason = "跌破白线"
            elif s.get("ztx_today", 0) < 0:
                reason = "砖型持续走弱"
            else:
                reason = "其他"
            eliminated.append({"code": s["code"], "name": s["name"], "reason": reason})
        elif result["is_limit_up"]:
            limit_up_stocks.append(result)
        else:
            non_limit_up_stocks.append(result)

    limit_up_stocks.sort(key=lambda x: x["score"], reverse=True)
    non_limit_up_stocks.sort(key=lambda x: x["score"], reverse=True)

    top_lu = limit_up_stocks[:10]
    top_non = non_limit_up_stocks[:10]

    def print_table(title, stocks_list):
        print(f"\n{'='*100}")
        print(f"📊 {title}（共{len(stocks_list)}只）")
        print(f"{'='*100}")
        print(f"{'排名':>4} {'代码':>6} {'名称':<8} {'涨幅%':>6} {'砖型值':>6} {'J值':>5} {'RSI':>5} {'B信号':>5} {'量能':>8} {'评分':>5} 明细")
        print("-" * 100)
        for i, s in enumerate(stocks_list[:10], 1):
            ztx = f"{s.get('ztx_today', '-'):.1f}" if s.get('ztx_today') is not None else "-"
            print(
                f"{i:>4} {s['code']:>6} {s['name']:<8} "
                f"{s['change_pct']:>+6.2f}% "
                f"{ztx:>6} "
                f"{str(s.get('j_value') or '-'):>5} "
                f"{str(s.get('rsi') or '-'):>5} "
                f"{s['b_signal']:>5} "
                f"{s['vol_signal']:>8} "
                f"{s['score']:>5} "
                f"{s['score_detail']}"
            )

    print_table(f"涨停TOP10（阈值按市场分类）", top_lu)
    print_table("非涨停TOP10", top_non)
    print(f"\n淘汰: {len(eliminated)} 只 | 涨停: {len(limit_up_stocks)} 只 | 非涨停: {len(non_limit_up_stocks)} 只")

    output = {
        "total": total,
        "eliminated_count": len(eliminated),
        "limit_up_count": len(limit_up_stocks),
        "non_limit_up_count": len(non_limit_up_stocks),
        "data_date": data.get("data_date", "unknown"),
        "top_limit_up": top_lu,
        "top_non_limit_up": top_non,
        "all_limit_up": limit_up_stocks,
        "all_non_limit_up": non_limit_up_stocks,
        "eliminated": eliminated[:20],
    }

    output_file = OUTPUT_DIR / "ztx_scores.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 评分完成，输出: {output_file}")


if __name__ == "__main__":
    main()
