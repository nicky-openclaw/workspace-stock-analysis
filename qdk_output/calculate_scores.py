import json

# 加载技术指标数据
with open('qdk_indicators.json', 'r', encoding='utf-8') as f:
    indicators = json.load(f)

def calculate_score(stock):
    """四层评分体系"""
    score = 0
    details = []
    
    # 硬淘汰检查
    if stock.get('硬淘汰'):
        return 0, ["硬淘汰"], "淘汰"
    
    # 第一层：趋势质量 (20分)
    trend_score = 0
    if stock.get('多头排列'):
        trend_score = 20
    elif stock.get('ma5') and stock.get('ma10'):
        if stock['ma5'] > stock['ma10']:
            trend_score = 15
        else:
            trend_score = 5
    score += trend_score
    details.append(f"趋势:{trend_score}")
    
    # 第二层：启动K信号 (40分)
    startup_score = 0
    if stock.get('启动K', {}).get('has'):
        startup_type = stock['启动K'].get('type', '')
        if startup_type == '倍量':
            startup_score = 30
        elif startup_type == '温和放量':
            startup_score = 18
        elif startup_type == '大阳线':
            startup_score = 10
        else:
            startup_score = 8  # 余热
    score += startup_score
    details.append(f"启动K:{startup_score}")
    
    # 第三层：启动位置 (25分)
    position_score = 0
    if stock.get('黄线附近'):
        position_score = 25
    elif stock.get('白线附近'):
        position_score = 15
    elif stock.get('站回白线'):
        position_score = 10
    score += position_score
    details.append(f"位置:{position_score}")
    
    # 第四层：涨幅确认 (15分)
    change_score = 0
    涨幅 = stock.get('涨幅', 0)
    if 涨幅 > 7:  # 大阳线
        change_score = 15
    elif 涨幅 > 5:
        change_score = 12
    elif 涨幅 > 3:
        change_score = 8
    elif 涨幅 > 0:
        change_score = 5
    score += change_score
    details.append(f"涨幅:{change_score}")
    
    return score, details, "通过"

# 计算所有股票分数
results = []
for code, stock in indicators.items():
    score, details, status = calculate_score(stock)
    results.append({
        "code": code,
        "name": stock['name'],
        "score": score,
        "details": details,
        "status": status,
        "涨幅": stock['涨幅'],
        "涨停": stock['涨停'],
        "收盘价": stock['收盘价'],
        "量比": stock['量比'],
        "成交量变化": stock['成交量变化'],
        "多头排列": stock['多头排列'],
        "启动K": stock['启动K'],
    })

# 按分数降序排序
results.sort(key=lambda x: x['score'], reverse=True)

# 分类输出
top10 = results[:10]
涨停_stocks = [r for r in results if r['涨停']]
非涨停_stocks = [r for r in results if not r['涨停']]

# 保存完整结果
output = {
    "total": len(results),
    "top10": top10,
    "涨停": 涨停_stocks,
    "非涨停": 非涨停_stocks,
    "all_scores": results
}

with open('qdk_scores.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# 打印TOP
print("=" * 6010)
print("【启动K选股结果 - 2026-03-09】")
print("=" * 60)
print("\n📊 TOP10 排名（按分数降序）：")
print("-" * 60)
for i, r in enumerate(top10, 1):
    print(f"{i:2}. {r['code']} {r['name']:<10} 分数:{r['score']:3} 涨幅:{r['涨幅']:>6.2f}% 收盘:{r['收盘价']:.2f}")

print("\n" + "=" * 60)
print(f"📈 涨停股票 ({len(涨停_stocks)}只)：")
print("-" * 60)
if 涨停_stocks:
    for r in 涨停_stocks[:10]:
        print(f"  {r['code']} {r['name']:<10} 分数:{r['score']:3} 涨幅:{r['涨幅']:>6.2f}%")
else:
    print("  无涨停股票")

print("\n" + "=" * 60)
print(f"📉 非涨停TOP10 ({len(非涨停_stocks)}只)：")
print("-" * 60)
for i, r in enumerate(非涨停_stocks[:10], 1):
    print(f"{i:2}. {r['code']} {r['name']:<10} 分数:{r['score']:3} 涨幅:{r['涨幅']:>6.2f}%")

print("\n" + "=" * 60)
print("数据已保存到 qdk_scores.json")
print("=" * 60)
