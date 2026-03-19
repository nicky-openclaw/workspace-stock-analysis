#!/usr/bin/env python3
"""
启动K选股 Step 4: 综合评分（v4.3）
硬淘汰 + 趋势质量 + 启动K信号质量 + 启动位置质量 + 涨幅确认
与框架 qdk_framework_v4.3 同步
"""

import json
from pathlib import Path

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
OUTPUT_DIR = WORKSPACE / "qdk_output"


def score_stock(s: dict):
    """
    五层综合评分（满分100分）
    硬淘汰：白线(EMA(EMA(C,10),10)) < 黄线((MA14+MA28+MA57+MA114)/4)
           / 收盘跌破白线 / 放量下跌 → 返回 None
    """
    code = s["code"]
    name = s["name"]
    ma5 = s.get("ma5")
    ma10 = s.get("ma10")
    ma20 = s.get("ma20")
    ma20_rising = s.get("ma20_rising")
    change_pct = s.get("change_pct", 0)
    vol_ratio = s.get("vol_ratio", 0)
    today_close = s.get("today_close", 0)
    has_double_vol_5d = s.get("has_double_vol_5d", False)
    just_reclaimed_white = s.get("just_reclaimed_ma5", False)

    # B信号指标
    j = s.get("j")  # KDJ的J值
    rsi3 = s.get("rsi3")  # RSI3
    yesterday_vol = s.get("yesterday_vol", 0)
    today_vol = s.get("today_vol", 0)
    
    # 趋势线数据
    white_line = s.get("white_line")
    yellow_line = s.get("yellow_line")
    white_rising = s.get("white_rising")  # 保留作为参考
    yellow_rising = s.get("yellow_rising")  # 保留作为参考
    white_slope_60 = s.get("white_slope_60")  # 60天斜率
    yellow_slope_60 = s.get("yellow_slope_60")  # 60天斜率
    
    # 新增指标（2026-03-16）
    today_low = s.get("today_low")  # 今日最低价
    high_20 = s.get("high_20")  # 20日最高价
    high_60 = s.get("high_60")  # 60日最高价
    max_vol_20 = s.get("max_vol_20")  # 20日最大量
    
    # ────────────── 硬淘汰 ──────────────
    # 基础条件：白线 < 黄线 = 趋势向下，直接淘汰
    if white_line and yellow_line and white_line < yellow_line:
        return None
    # 收盘跌破白线 = 跌破生命线，淘汰
    if white_line and today_close < white_line:
        return None
    # 放量下跌 = 出货信号，淘汰
    if change_pct < 0 and vol_ratio >= 1.5:
        return None
    # 注意：不再硬淘汰"白线7天不向上"，因为启动K包括趋势扭转/改变型

    score = 0
    detail = []

    # 位置距离（相对白线/黄线）
    white_dist_pct = round((today_close - white_line) / white_line * 100, 2) if white_line else None
    yellow_dist_pct = round((today_close - yellow_line) / yellow_line * 100, 2) if yellow_line else None

    # 获取量能数据
    avg_vol_20 = s.get("avg_vol_20", 0)  # 20日均量
    vol_ratio_20d = vol_ratio if avg_vol_20 == 0 else vol_ratio  # 这里先用现有的vol_ratio（vs昨日），后面改进
    
    # ────────────── 第一层：趋势质量（20分）──────────────
    # 启动K使用白线=EMA(EMA(C,10),10)，黄线=(MA14+MA28+MA57+MA114)/4
    # 使用60天线性回归斜率判断趋势方向（2026-03-16修复）
    # 斜率阈值0.5：斜率>0.5才算明显上涨趋势
    layer1 = 0
    if white_line and yellow_line and white_line >= yellow_line:
        layer1 += 8
        detail.append("白线≥黄线+8")
    # 使用60天斜率判断趋势方向（阈值0.5）
    if white_slope_60 is not None and white_slope_60 > 0.5:
        layer1 += 7
        detail.append("白线60天向上+7")
    if yellow_slope_60 is not None and yellow_slope_60 > 0.5:
        layer1 += 5
        detail.append("黄线60天向上+5")
    score += layer1

    # ────────────── 第二层：启动K信号质量（40分，核心层）──────────────
    layer2 = 0

    # 量能信号：改用vs20日均量（更准确，2026-03-16修复）
    # 倍量：今日量 ≥ 20日均量 * 2.5
    # 放量：20日均量 * 1.5 <= 今日量 < 20日均量 * 2.5
    if avg_vol_20 > 0:
        vol_ratio_vs_20d = today_vol / avg_vol_20
    else:
        vol_ratio_vs_20d = vol_ratio
    
    if vol_ratio_vs_20d >= 2.5:
        layer2 += 30
        detail.append(f"倍量({vol_ratio_vs_20d:.1f}x)+30")
    elif vol_ratio_vs_20d >= 1.5:
        layer2 += 18
        detail.append(f"放量({vol_ratio_vs_20d:.1f}x)+18")

    # 大阳线确认（可叠加）
    if change_pct >= 5:
        layer2 += 10
        detail.append("大阳线+10")

    # 近5日启动余热（可叠加）：今日不是倍量但近5日有倍量
    if has_double_vol_5d and vol_ratio_vs_20d < 2.5:
        layer2 += 8
        detail.append("近5日倍量余热+8")

    layer2 = min(layer2, 40)
    score += layer2

    # ────────────── 启动位置质量（降低权重，2026-03-16修复）──────────────
    # 原权重：黄线附近+25，白线附近+15，站回白线+10
    # 新权重：黄线附近+10，白线附近+5，站回白线+3
    layer3 = 0
    position_label = ""

    if yellow_dist_pct is not None and abs(yellow_dist_pct) <= 5:
        layer3 = 10
        position_label = f"黄线附近({yellow_dist_pct:+.1f}%)"
        detail.append("黄线位置+10")
    elif white_dist_pct is not None and abs(white_dist_pct) <= 3:
        layer3 = 5
        position_label = f"白线附近({white_dist_pct:+.1f}%)"
        detail.append("白线位置+5")
    elif just_reclaimed_white:
        layer3 = 3
        position_label = "刚站回白线"
        detail.append("站回白线+3")

    score += layer3

    # ────────────── 新增：启动强度因子（2026-03-16）──────────────
    # 核心：开盘支撑 + 收盘确认 + 突破高点 + 量能突破
    layer_strength = 0
    
    # 1. 开盘支撑：最低价在黄线±5%
    if today_low and yellow_line:
        low_dist_pct = (today_low - yellow_line) / yellow_line * 100
        if abs(low_dist_pct) <= 5:
            layer_strength += 10
            detail.append(f"开盘支撑({low_dist_pct:+.1f}%)+10")
    
    # 2. 收盘在白线上方（更强的确认）
    if white_line and today_close > white_line:
        layer_strength += 5
        detail.append("收盘在白线上方+5")
    
    # 3. 启动强度：涨幅≥7%
    if change_pct >= 7:
        layer_strength += 10
        detail.append(f"启动强度({change_pct:.1f}%)+10")
    
    # 4. 突破20日高点
    if high_20 and today_close >= high_20:
        layer_strength += 15
        detail.append("突破20日高点+15")
    
    # 5. 突破60日高点
    if high_60 and today_close >= high_60:
        layer_strength += 20
        detail.append("突破60日高点+20")
    
    # 6. 量能突破：今日量≥20日最大量
    if max_vol_20 and today_vol >= max_vol_20:
        layer_strength += 15
        detail.append("量能突破+15")
    
    score += layer_strength

    # ────────────── 涨幅确认（15分）──────────────
    layer4 = 0
    if change_pct >= 9.9:
        layer4 = 15
        detail.append("涨停+15")
    elif change_pct >= 5:
        layer4 = 15
        detail.append("强势+15")
    elif change_pct >= 2:
        layer4 = 8
        detail.append("中势+8")
    elif change_pct >= 0:
        layer4 = 3
        detail.append("弱势+3")
    score += layer4

    score = min(score, 100)

    # 启动K类型判断（基于白线/黄线）
    if vol_ratio >= 2 and change_pct >= 5 and yellow_dist_pct is not None and abs(yellow_dist_pct) <= 5:
        launch_type = "趋势延续型"
    elif vol_ratio >= 2 and change_pct >= 5 and (white_line and yellow_line and white_line > yellow_line and ma20_rising is False):
        launch_type = "趋势扭转型"
    elif vol_ratio >= 1.5 and change_pct >= 3:
        launch_type = "趋势改变型"
    else:
        launch_type = "待观察"

    return {
        "code": code,
        "name": name,
        "score": score,
        "launch_type": launch_type,
        "position_label": position_label,
        "change_pct": change_pct,
        "vol_ratio": vol_ratio,
        "white_line": white_line,
        "yellow_line": yellow_line,
        "white_dist_pct": white_dist_pct,
        "yellow_dist_pct": yellow_dist_pct,
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20,
        "ma20_rising": ma20_rising,
        "score_detail": " | ".join(detail),
        "score_breakdown": {
            "trend": layer1,
            "launch_signal": layer2,
            "position": layer3,
            "momentum": layer4,
        },
        # 保留B信号供参考，但不计入总分
        "j": j,
        "rsi3": rsi3,
    }


def main():
    indicators_file = OUTPUT_DIR / "qdk_indicators.json"
    with open(indicators_file, encoding="utf-8") as f:
        data = json.load(f)

    stocks = data["stocks"]
    total = len(stocks)
    print(f"共 {total} 只股票，开始四层评分...")

    scored = []
    eliminated = []

    for s in stocks:
        result = score_stock(s)
        if result is None:
            wl = s.get("white_line")
            yl = s.get("yellow_line")
            cp = s.get("change_pct", 0)
            vr = s.get("vol_ratio", 0)
            tc = s.get("today_close", 0)
            wr_7d = s.get("white_rising_7d", True)  # 默认为True避免误判
            
            if wl and yl and wl < yl:
                reason = "白线<黄线"
            elif tc and wl and tc < wl:
                reason = "跌破白线"
            elif wr_7d is False:
                reason = "白线7天不向上"
            elif cp < 0 and vr >= 1.5:
                reason = "放量下跌"
            else:
                reason = "其他"
            eliminated.append({"code": s["code"], "name": s["name"], "reason": reason})
        else:
            scored.append(result)

    scored.sort(key=lambda x: x["score"], reverse=True)
    top5 = scored[:5]

    print(f"\n淘汰: {len(eliminated)} 只 | 进入评分: {len(scored)} 只")
    print(f"\n📊 启动K TOP5:")
    print(f"{'排名':>4} {'代码':>6} {'名称':<8} {'涨幅%':>6} {'量比':>5} {'位置':<12} {'启动类型':<8} {'评分':>5} 明细")
    print("-" * 100)
    for i, s in enumerate(top5, 1):
        print(
            f"{i:>4} {s['code']:>6} {s['name']:<8} "
            f"{s['change_pct']:>+6.2f}% "
            f"{s['vol_ratio']:>5.1f}x "
            f"{s['position_label']:<12} "
            f"{s['launch_type']:<8} "
            f"{s['score']:>5} "
            f"{s['score_detail']}"
        )

    output = {
        "total": total,
        "eliminated_count": len(eliminated),
        "scored_count": len(scored),
        "data_date": data.get("data_date", "unknown"),
        "top5": top5,
        "all_scored": scored,
        "eliminated": eliminated[:20],
    }

    output_file = OUTPUT_DIR / "qdk_scores.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 评分完成，输出: {output_file}")


if __name__ == "__main__":
    main()
