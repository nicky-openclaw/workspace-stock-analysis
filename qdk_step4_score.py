#!/usr/bin/env python3
"""
Step 4: 五层评分 (v4.0 - 2026-03-10)
满分100分：
  * 第一层趋势质量15分
  * 第二层启动信号35分
  * 第三层位置质量20分
  * 第四层类型专属15分
  * 第五层涨幅确认15分
硬淘汰：白线<黄线/跌破白线/放量下跌/J>80
"""

import json
import pandas as pd
import os
import numpy as np
from json import JSONEncoder

class NumpyEncoder(JSONEncoder):
    """处理numpy类型的JSON序列化"""
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# 读取Step 3的数据
with open("qdk_output/qdk_indicators.json", "r", encoding="utf-8") as f:
    indicators = json.load(f)

# 读取K线数据用于分析启动K
with open("qdk_output/qdk_kline.json", "r", encoding="utf-8") as f:
    kline_data = json.load(f)

print(f"加载数据: {len(indicators)} 只股票")

def analyze_startup_signal(kline_list, j_value, change_pct):
    """
    分析启动K信号（v4.0）
    满分35分：
    - 涨幅>4%（B2标准）→ 20分
    - J<13 → 15分，J<30 → 10分，J<55 → 5分
    - 倍量（>2倍）→ 15分，放量（>1.5倍）→ 8分
    """
    if not kline_list or len(kline_list) < 5:
        return {"signal": 0, "details": "数据不足"}
    
    df = pd.DataFrame(kline_list)
    last1 = df.iloc[-1]
    last2 = df.iloc[-2] if len(df) >= 2 else last1
    
    # 成交量变化
    vol_now = last1['amount']
    vol_prev = last2['amount']
    vol_ratio = vol_now / vol_prev if vol_prev > 0 else 1
    
    score = 0
    details = []
    
    # 涨幅评分（B2标准>4%）
    if change_pct > 4:
        score += 20
        details.append("涨幅>4%+20")
    elif change_pct > 2:
        score += 10
        details.append("涨幅>2%+10")
    
    # J值评分（v4.0调整）
    if j_value is not None:
        if j_value < 13:
            score += 15
            details.append("J<13+15")
        elif j_value < 30:
            score += 10
            details.append("J<30+10")
        elif j_value < 55:
            score += 5
            details.append("J<55+5")
    
    # 量能评分
    if vol_ratio > 2:  # 倍量
        score += 15
        details.append("倍量+15")
    elif vol_ratio > 1.5:  # 放量
        score += 8
        details.append("放量+8")
    
    return {
        "signal": min(score, 35),  # 上限35分
        "details": details,
        "vol_ratio": round(vol_ratio, 2),
        "change": round(change_pct, 2),
        "j": j_value
    }

def score_trend_type(trend_type, trend_data, change_pct):
    """
    第四层：类型专属评分（满分15分）
    扭转型：前期跌幅 + 今天涨幅
    改变型：横盘天数 + 突破幅度
    延续型：趋势强度 + 回调幅度
    """
    score = 0
    details = []
    
    if trend_type == "扭转型":
        # 前期跌幅越大分越高
        change_20d = trend_data.get('change_20d', 0)
        if change_20d < -30:
            score += 15
            details.append(f"前期跌幅{change_20d:.1f}%+15")
        elif change_20d < -20:
            score += 12
            details.append(f"前期跌幅{change_20d:.1f}%+12")
        elif change_20d < -10:
            score += 8
            details.append(f"前期跌幅{change_20d:.1f}%+8")
        
        # 今日涨幅贡献
        if change_pct > 5:
            score += 5
            details.append("今日大涨+5")
    
    elif trend_type == "改变型":
        # 横盘振幅越小 + 突破幅度越大
        amplitude_20d = trend_data.get('amplitude_20d', 100)
        if amplitude_20d < 10:
            score += 8
            details.append(f"强横盘振幅{amplitude_20d:.1f}%+8")
        elif amplitude_20d < 15:
            score += 5
            details.append(f"横盘振幅{amplitude_20d:.1f}%+5")
        
        if change_pct > 5:
            score += 7
            details.append("突破大阳+7")
        elif change_pct > 3:
            score += 4
            details.append("突破中阳+4")
    
    elif trend_type == "延续型":
        # 前期上涨趋势 + 回调浅
        change_20d = trend_data.get('change_20d', 0)
        if change_20d > 20:
            score += 8
            details.append(f"前期涨幅{change_20d:.1f}%+8")
        elif change_10d := (change_20d * 0.5):  # 近似10日涨幅
            if change_10d > 10:
                score += 5
                details.append("趋势延续+5")
        
        # 回调幅度（从最高点回调多少）
        high_20d = trend_data.get('high_20d', 0)
        current_price = trend_data.get('price', 0)
        if high_20d > 0:
            pullback = (high_20d - current_price) / high_20d * 100
            if pullback < 5:
                score += 7
                details.append(f"回调浅{pullback:.1f}%+7")
            elif pullback < 10:
                score += 4
                details.append(f"回调{pullback:.1f}%+4")
    
    return {
        "signal": min(score, 15),  # 上限15分
        "details": details
    }

def score_stock(stock_code, data):
    """对单只股票评分（v4.0 - 满分100分）"""
    score = 0
    details = []
    eliminated = False
    eliminate_reason = ""
    
    # ===== 涨幅异常自检 =====
    change_pct = data['change_pct']
    abnormal_change = False
    if change_pct > 30:
        abnormal_change = True
        details.append(f"⚠️涨幅异常:{change_pct:+.2f}%")
    elif change_pct < -10:
        abnormal_change = True
        details.append(f"⚠️跌幅异常:{change_pct:+.2f}%")
    
    # ===== 硬淘汰条件 =====
    white = data['white_line']
    yellow = data['yellow_line']
    position = data['position']
    volume_up = data['volume_up']
    j_value = data.get('j')
    
    # 白线 < 黄线
    if white < yellow:
        eliminated = True
        eliminate_reason = "白线<黄线"
    # 跌破白线
    elif position == "跌破白线" or position == "跌破黄线":
        eliminated = True
        eliminate_reason = f"跌破白线({position})"
    # 放量下跌
    elif not volume_up and change_pct < 0:
        eliminated = True
        eliminate_reason = "放量下跌" if volume_up else "下跌"
    # J值过高（v4.0新增）
    elif j_value and j_value > 80:
        eliminated = True
        eliminate_reason = f"J值过高({j_value})"
    
    if eliminated:
        return {
            "stock_code": stock_code,
            "name": data['name'],
            "score": 0,
            "eliminated": True,
            "eliminate_reason": eliminate_reason,
            "details": details
        }
    
    # ===== 第一层：趋势质量 (15分) =====
    trend_score = 0
    if data['ma_bullish']:
        trend_score = 15
        details.append("MA多头排列+15")
    else:
        ma5 = data['MA5']
        ma10 = data['MA10']
        ma20 = data['MA20']
        if ma5 > ma10:
            trend_score += 5
            details.append("MA5>MA10+5")
        if ma10 > ma20:
            trend_score += 3
            details.append("MA10>MA20+3")
    
    score += trend_score
    
    # ===== 第二层：启动信号 (35分) =====
    kline = kline_data.get(stock_code, {}).get("kline", [])
    startup_signal = analyze_startup_signal(kline, j_value, change_pct)
    score += startup_signal['signal']
    if startup_signal['details']:
        details.extend(startup_signal['details'])
    
    # ===== 第三层：位置质量 (20分) =====
    position_score = 0
    if position == "白线附近":
        position_score = 20
        details.append("白线附近+20")
    elif position == "黄线附近":
        position_score = 20
        details.append("黄线附近+20")
    elif data['price'] > data['white_line']:
        position_score = 10
        details.append("站上白线+10")
    
    score += position_score
    
    # ===== 第四层：类型专属 (15分) =====
    trend_type = data.get('trend_type', '延续型')
    trend_data = data.get('trend_data', {})
    # 添加当前价到trend_data用于计算回调
    trend_data['price'] = data['price']
    type_score = score_trend_type(trend_type, trend_data, change_pct)
    score += type_score['signal']
    if type_score['details']:
        details.extend(type_score['details'])
    
    # ===== 第五层：涨幅确认 (15分) =====
    change_score = 0
    if change_pct > 9.9:  # 涨停
        change_score = 15
        details.append("涨停+15")
    elif change_pct > 5:
        change_score = 12
        details.append(">5%+12")
    elif change_pct > 0:
        change_score = 8
        details.append(">0%+8")
    elif change_pct > -3:
        change_score = 3
        details.append(">-3%+3")
    
    score += change_score
    
    return {
        "stock_code": stock_code,
        "name": data['name'],
        "score": score,
        "change_pct": round(change_pct, 2),
        "abnormal_change": abnormal_change,
        "trend_type": trend_type,
        "position": position,
        "vol_ratio": data['vol_ratio'],
        "ma_bullish": bool(data['ma_bullish']),
        "startup_signal": startup_signal,
        "type_score": type_score,
        "rsi14": data.get('rsi14'),
        "k": data.get('k'),
        "d": data.get('d'),
        "j": j_value,
        "eliminated": False,
        "details": details
    }

# 评分所有股票
results = []
for stock_code, data in indicators.items():
    result = score_stock(stock_code, data)
    results.append(result)

# 按分数排序
results.sort(key=lambda x: x['score'], reverse=True)

# 统计
total = len(results)
eliminated = sum(1 for r in results if r.get('eliminated'))
qualified = total - eliminated

print(f"\n评分完成:")
print(f"  总股票: {total}")
print(f"  硬淘汰: {eliminated}")
print(f"  符合条件: {qualified}")

# 分类：涨停 vs 非涨停
limit_up = [r for r in results if not r.get('eliminated') and r.get('change_pct', 0) > 9.9]
non_limit_up = [r for r in results if not r.get('eliminated') and r.get('change_pct', 0) <= 9.9]

print(f"  涨停: {len(limit_up)}")
print(f"  非涨停: {len(non_limit_up)}")

# 统计走势类型
trend_types = {}
for r in results:
    if not r.get('eliminated'):
        t = r.get('trend_type', '未知')
        trend_types[t] = trend_types.get(t, 0) + 1

print(f"  走势类型: {trend_types}")

# 保存结果
output_path = "qdk_output/qdk_scores.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({
        "all_stocks": results,
        "limit_up": limit_up,
        "non_limit_up": non_limit_up,
        "stats": {
            "total": total,
            "eliminated": eliminated,
            "qualified": qualified,
            "limit_up_count": len(limit_up),
            "non_limit_up_count": len(non_limit_up),
            "trend_types": trend_types
        }
    }, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)

print(f"\n数据已保存到: {output_path}")

# 打印TOP10
print("\n" + "="*60)
print("TOP10 启动K选股 (v4.0 - 2026-03-10)")
print("="*60)

abnormal_stocks = []
for i, r in enumerate(results[:10], 1):
    if r.get('eliminated'):
        print(f"{i:2d}. {r['stock_code']} {r['name']:10s} - 淘汰: {r.get('eliminate_reason', 'N/A')}")
    else:
        abnormal_flag = ""
        if r.get('abnormal_change'):
            abnormal_flag = " ⚠️异常"
            abnormal_stocks.append(f"{r['name']}({r['change_pct']:+.2f}%)")
        
        trend_type = r.get('trend_type', '-')
        j = r.get('j', '-')
        
        print(f"{i:2d}. {r['stock_code']} {r['name']:10s} | "
              f"分数:{r['score']:3d} | 涨幅:{r['change_pct']:+6.2f}%{abnormal_flag} | "
              f"{trend_type} | J:{j}")

if abnormal_stocks:
    print("\n⚠️ 涨幅异常警告:")
    for s in abnormal_stocks:
        print(f"   - {s}")

# 打印TOP5详细评分明细
print("\n" + "="*60)
print("TOP5 评分明细")
print("="*60)
for i, r in enumerate(results[:5], 1):
    if not r.get('eliminated'):
        print(f"\n{i}. {r['name']} ({r['stock_code']}) - {r['score']}分")
        print(f"   涨幅:{r['change_pct']:+6.2f}% | 位置:{r['position']} | 类型:{r['trend_type']}")
        print(f"   J值:{r.get('j')} | 量比:{r['vol_ratio']}")
        print(f"   评分明细: {r.get('details', [])}")
