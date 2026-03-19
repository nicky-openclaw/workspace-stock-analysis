#!/usr/bin/env python3
"""
Step 4: B1选股四级筛选体系 v4.0（2026-03-12）
读取 b1_indicators.json，执行硬淘汰+三级筛选，输出 b1_scores.json

评分体系：满分117分
- 一级筛选：B1五条件（77分）
- 二级筛选：位置+趋势+量能（30分）
- 三级筛选：股性+弹性（10分）
"""

import json
from pathlib import Path

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
OUTPUT_DIR = WORKSPACE / "b1_output"


def score_stock_v4(s: dict) -> dict:
    """
    B1选股三级筛选体系（满分117分）
    
    硬淘汰：白线<黄线 或 收盘跌破白线 → 返回 None
    """
    code = s["code"]
    name = s["name"]
    
    # 基础数据
    ma5 = s.get("ma5")
    ma10 = s.get("ma10")
    ma20 = s.get("ma20")
    ma20_rising = s.get("ma20_rising")
    j = s.get("j_value")
    rsi3 = s.get("rsi3")
    rsi14 = s.get("rsi14")
    vol_signal = s.get("vol_signal", "")
    has_double_vol = s.get("has_double_vol_20d", False)
    change_pct = s.get("change_pct", 0)
    today_close = s.get("today_close", 0)
    
    # 趋势线
    white_line = s.get("white_line")
    yellow_line = s.get("yellow_line")
    
    # 关键K信息
    key_k_info = s.get("key_k_info", {})
    has_key_k = key_k_info.get("has_key_k", False)
    has_biliang = key_k_info.get("has_biliang", False)
    
    # 振幅（近20日）
    amplitude_20d = s.get("recent_amplitude", 0)
    
    # 20日最高量/最低量
    vol_max_20d = s.get("vol_max_20", 0)
    vol_min_20d = s.get("vol_min_20", 0)
    
    # 20日最高价
    highs_20 = s.get("highs_20", [])
    high_20d = max(highs_20) if highs_20 else 0
    today_vol = s.get("today_vol", 0)
    
    # 阈值
    J_B1_THRESHOLD = 13
    RSI_B1_THRESHOLD = 23
    AMPLITUDE_THRESHOLD = 15  # 振幅15%以上
    
    # ────────────── 硬淘汰 ──────────────
    if white_line and yellow_line and white_line < yellow_line:
        return None
    if white_line and today_close < white_line:
        return None
    
    # 计算距离
    yellow_dist_pct = None
    white_dist_pct = None
    if yellow_line:
        yellow_dist_pct = round((today_close - yellow_line) / yellow_line * 100, 2)
    if white_line:
        white_dist_pct = round((today_close - white_line) / white_line * 100, 2)
    
    # ────────────── 一级筛选：B1五条件（77分）─────────────
    level1 = 0
    level1_detail = []
    
    # 1. 白线≥黄线 +10
    if white_line and yellow_line and white_line >= yellow_line:
        level1 += 10
        level1_detail.append("白线≥黄线+10")
    
    # 2. J<13 +12
    if j is not None and j < J_B1_THRESHOLD:
        level1 += 12
        level1_detail.append(f"J<{J_B1_THRESHOLD}({j:.1f})+12")
    
    # 3. RSI3<23 +10
    rsi_use = rsi3 if rsi3 is not None else rsi14
    if rsi_use is not None and rsi_use < RSI_B1_THRESHOLD:
        level1 += 10
        level1_detail.append(f"RSI3<{RSI_B1_THRESHOLD}({rsi_use:.1f})+10")
    
    # 4. 振幅≥15% +10
    if amplitude_20d is not None and amplitude_20d >= AMPLITUDE_THRESHOLD:
        level1 += 10
        level1_detail.append(f"振幅≥{AMPLITUDE_THRESHOLD}%({amplitude_20d:.1f}%)+10")
    
    # 5. 缩量 +15
    # 缩量: VOL < 20日最高量 × 0.416
    if vol_max_20d and today_vol:
        vol_ratio = today_vol / vol_max_20d
        if vol_ratio < 0.416:
            level1 += 15
            level1_detail.append(f"缩量({vol_ratio:.2f})+15")
    
    # 6. B1完整触发（五条件全满足） +20
    b1_triggered = False
    if (white_line and yellow_line and white_line >= yellow_line and
        j is not None and j < J_B1_THRESHOLD and
        rsi_use is not None and rsi_use < RSI_B1_THRESHOLD and
        amplitude_20d is not None and amplitude_20d >= AMPLITUDE_THRESHOLD and
        vol_max_20d and today_vol and vol_ratio < 0.416):
        level1 += 20
        b1_triggered = True
        level1_detail.append("B1完整触发+20")
    
    # ────────────── 二级筛选：位置+趋势+量能（30分）─────────────
    level2 = 0
    level2_detail = []
    
    # 1. 黄线附近 ±5% +15
    if yellow_dist_pct is not None and abs(yellow_dist_pct) <= 5:
        level2 += 15
        level2_detail.append(f"黄线附近({yellow_dist_pct:+.1f}%)+15")
    # 2. 白线附近 ±3% +10
    elif white_dist_pct is not None and abs(white_dist_pct) <= 3:
        level2 += 10
        level2_detail.append(f"白线附近({white_dist_pct:+.1f}%)+10")
    # 3. 站上白线 +5
    elif white_dist_pct is not None and white_dist_pct > 3 and white_dist_pct <= 8:
        level2 += 5
        level2_detail.append(f"站上白线({white_dist_pct:+.1f}%)+5")
    
    # 4. 趋势强（白线-黄线差>5%）+5
    if white_line and yellow_line:
        diff_pct = (white_line - yellow_line) / yellow_line * 100
        if diff_pct > 5:
            level2 += 5
            level2_detail.append(f"趋势强({diff_pct:+.1f}%)+5")
    
    # 5. 地量 +10
    # 地量: VOL < 20日最低量 × 1.5
    if vol_min_20d and today_vol:
        vol_min_ratio = today_vol / vol_min_20d
        if vol_min_ratio < 1.5:
            level2 += 10
            level2_detail.append(f"地量({vol_min_ratio:.2f})+10")
    # 6. 缩量 +5（已在一级计分，此处不重复）
    
    level2 = min(level2, 30)  # 上限30
    
    # ────────────── 三级筛选：股性+弹性（10分）─────────────
    level3 = 0
    level3_detail = []
    
    # 1. 涨停基因（20日内有涨停） +5
    # 需要从指标数据中获取，此处暂时预留
    # if s.get("has_limit_up_20d", False):
    #     level3 += 5
    #     level3_detail.append("涨停基因+5")
    
    # 2. 回调深度（从20日高点回调>10%）+3
    high_20d = s.get("high_20d", 0)
    if high_20d and today_close:
        drawdown = (high_20d - today_close) / high_20d * 100
        if drawdown > 10:
            level3 += 3
            level3_detail.append(f"回调{drawdown:.1f}%+3")
    
    # 3. 白线斜率（10日涨幅>5%）+2
    # 需要计算10日涨幅，暂时预留
    # if s.get("white_line_gain_10d", 0) > 5:
    #     level3 += 2
    #     level3_detail.append("白线斜率+2")
    
    level3 = min(level3, 10)  # 上限10
    
    # ────────────── 总分 ──────────────
    total_score = level1 + level2 + level3
    
    # 位置标签
    position_label = ""
    if yellow_dist_pct is not None:
        if abs(yellow_dist_pct) <= 5:
            position_label = f"黄线附近({yellow_dist_pct:+.1f}%)"
        elif white_dist_pct is not None and abs(white_dist_pct) <= 3:
            position_label = f"白线附近({white_dist_pct:+.1f}%)"
        elif white_dist_pct is not None:
            position_label = f"站上白线({white_dist_pct:+.1f}%)"
    
    return {
        "code": code,
        "name": name,
        "score": total_score,
        "b1_triggered": b1_triggered,
        "change_pct": change_pct,
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20,
        "ma20_rising": ma20_rising,
        "j_value": j,
        "rsi3": rsi3,
        "vol_signal": vol_signal,
        "has_key_k": has_key_k,
        "has_biliang": has_biliang,
        "amplitude_20d": amplitude_20d,
        "position_label": position_label,
        "yellow_dist_pct": yellow_dist_pct,
        "white_dist_pct": white_dist_pct,
        "score_detail": " | ".join(level1_detail + level2_detail + level3_detail),
        "score_breakdown": {
            "level1": level1,
            "level2": level2,
            "level3": level3,
        }
    }


def main():
    indicators_file = OUTPUT_DIR / "b1_indicators.json"
    with open(indicators_file, encoding="utf-8") as f:
        data = json.load(f)

    stocks = data["stocks"]
    total = len(stocks)
    print(f"共 {total} 只股票，开始评分（四级筛选体系v4.0）...")

    scored = []
    eliminated = []

    for s in stocks:
        result = score_stock_v4(s)
        if result is None:
            eliminated.append({"code": s["code"], "name": s["name"],
                                "reason": "白线<黄线或跌破白线"})
        else:
            scored.append(result)

    # 按总分降序排列
    scored.sort(key=lambda x: x["score"], reverse=True)
    top15 = scored[:15]

    print(f"\n淘汰: {len(eliminated)} 只（白线<黄线或跌破白线）")
    print(f"进入评分: {len(scored)} 只")
    print(f"\n📊 TOP15 (四级筛选体系v4.0 - 满分117分):")
    print(f"{'排名':>4} {'代码':>6} {'名称':<8} {'涨幅%':>6} {'J值':>5} {'RSI3':>5} {'位置':>14} {'一级':>4} {'二级':>4} {'三级':>4} {'总分':>5}")
    print("-" * 85)
    for i, s in enumerate(top15, 1):
        breakdown = s.get("score_breakdown", {})
        print(
            f"{i:>4} {s['code']:>6} {s['name']:<8} "
            f"{s['change_pct']:>+6.2f}% "
            f"{str(s['j_value'] or '-'):>5} "
            f"{str(s['rsi3'] or '-'):>5} "
            f"{s.get('position_label', '-'):<14} "
            f"{breakdown.get('level1', 0):>4} "
            f"{breakdown.get('level2', 0):>4} "
            f"{breakdown.get('level3', 0):>4} "
            f"{s['score']:>5}"
        )

    output = {
        "total": total,
        "eliminated_count": len(eliminated),
        "scored_count": len(scored),
        "data_date": data.get("data_date", "unknown"),
        "scoring_version": "v4.0_117",
        "top15": top15,
        "all_scored": scored,
        "eliminated": eliminated[:20],
    }

    output_file = OUTPUT_DIR / "b1_scores.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 评分完成，输出: {output_file}")


if __name__ == "__main__":
    main()
