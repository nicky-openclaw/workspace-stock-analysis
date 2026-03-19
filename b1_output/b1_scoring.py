#!/usr/bin/env python3
"""
B1五层评分筛选 - 更宽松版
尝试只使用MA5<MA10作为硬淘汰规则
"""
import json

with open('/Users/nicky/.openclaw/workspace-stock-analysis/b1_output/b1_indicators.json', 'r') as f:
    data = json.load(f)

stocks = data['stocks']
results = []

for stock in stocks:
    code = stock['code']
    name = stock['name']
    ma5 = stock['ma5']
    ma10 = stock['ma10']
    ma20 = stock['ma20']
    ma20_direction = stock['ma20_direction']
    j_value = stock['j_value']
    rsi14 = stock['rsi14']
    volume = stock['volume']
    volume_ratio = stock['volume_ratio']
    ma20_avg_volume = stock['ma20_avg_volume']
    di_liang_signal = stock['di_liang_signal']
    close_ma20_distance_pct = stock['close_ma20_distance_pct']
    
    # 估算收盘价
    close = ma20 * (1 + close_ma20_distance_pct / 100)
    
    # ===== 硬淘汰规则 - 只用MA5 < MA10 =====
    eliminated = False
    eliminate_reason = ""
    
    if ma5 < ma10:
        eliminated = True
        eliminate_reason = "MA5 < MA10"
    
    # 如果被淘汰
    if eliminated:
        results.append({
            "code": code,
            "name": name,
            "total_score": 0,
            "trend_score": 0,
            "b1_signal_score": 0,
            "volume_score": 0,
            "position_score": 0,
            "strength_score": 0,
            "eliminated": True,
            "eliminate_reason": eliminate_reason,
            "j_value": j_value,
            "rsi14": rsi14,
            "di_liang": di_liang_signal,
            "close_ma20_distance_pct": close_ma20_distance_pct,
            "b1_triggered": False
        })
        continue
    
    # ===== 五层评分 =====
    trend_score = 0
    b1_signal_score = 0
    volume_score = 0
    position_score = 0
    strength_score = 0
    
    # 第一层：趋势质量（20分）
    if ma20_direction == "up":
        trend_score += 10
    # 多头排列：MA5 > MA10 > MA20
    if ma5 > ma10 and ma10 > ma20:
        trend_score += 10
    
    # 第二层：B1信号质量（25分）
    if j_value < 14:
        b1_signal_score += 15
    if rsi14 < 23:
        b1_signal_score += 10
    
    # 第三层：量能质量（20分）
    volume_ratio_20d = volume / ma20_avg_volume
    if di_liang_signal:  # 地量信号
        volume_score += 15
    elif volume_ratio_20d < 0.7:  # 缩量信号
        volume_score += 8
    
    # 第四层：位置质量（20分）
    if abs(close_ma20_distance_pct) < 5:
        position_score += 10
    if close_ma20_distance_pct > 0:  # 收盘价在MA20上方
        position_score += 10
    
    # 第五层：强度确认（15分）- 缺少涨跌幅数据，设为0
    
    total_score = trend_score + b1_signal_score + volume_score + position_score + strength_score
    
    # B1触发判断
    b1_triggered = (j_value < 14 and rsi14 < 23 and (di_liang_signal or volume_ratio_20d < 0.7))
    
    results.append({
        "code": code,
        "name": name,
        "total_score": total_score,
        "trend_score": trend_score,
        "b1_signal_score": b1_signal_score,
        "volume_score": volume_score,
        "position_score": position_score,
        "strength_score": strength_score,
        "eliminated": False,
        "eliminate_reason": "",
        "j_value": j_value,
        "rsi14": rsi14,
        "di_liang": di_liang_signal,
        "close_ma20_distance_pct": close_ma20_distance_pct,
        "b1_triggered": b1_triggered
    })

# 按总分排序
results.sort(key=lambda x: x['total_score'], reverse=True)

# 统计
total_input = len(stocks)
total_eliminated = sum(1 for r in results if r['eliminated'])
survivors = [r for r in results if not r['eliminated']]
total_b1_triggered = sum(1 for r in survivors if r['b1_triggered'])

print(f"共{total_input}只股票")
print(f"淘汰: {total_eliminated}只")
print(f"幸存: {len(survivors)}只")
print(f"B1触发: {total_b1_triggered}只")

# 输出TOP15或所有幸存者
print(f"\n=== 评分结果 ({len(survivors)}只幸存) ===")
display_stocks = results[:15] if len(results) >= 15 else results
for i, s in enumerate(display_stocks, 1):
    b1_mark = "⭐B1" if s['b1_triggered'] else ""
    elim_mark = "[淘汰]" if s['eliminated'] else ""
    print(f"{i}. {s['code']} {s['name']}: 总分{s['total_score']} {b1_mark} {elim_mark}")
    if not s['eliminated']:
        print(f"   趋势:{s['trend_score']}/20 B1:{s['b1_signal_score']}/25 量能:{s['volume_score']}/20 位置:{s['position_score']}/20 强度:{s['strength_score']}/15")

# 保存完整结果
output = {
    "total": total_input,
    "date": data['date'],
    "eliminated_count": total_eliminated,
    "b1_triggered_count": total_b1_triggered,
    "stocks": display_stocks
}

output_path = '/Users/nicky/.openclaw/workspace-stock-analysis/b1_output/b1_scores.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n结果已保存到: {output_path}")
