#!/usr/bin/env python3
"""
Step 3: 计算技术指标 (v4.0 - 2026-03-10)
- 新增前期走势类型识别：扭转型/改变型/延续型
- 新增20日涨跌幅、振幅计算
"""

import json
import pandas as pd
import numpy as np
import os
from json import JSONEncoder

# 处理numpy类型的JSON序列化
class NumpyEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)

# 读取Step 2的数据
with open("qdk_output/qdk_kline.json", "r", encoding="utf-8") as f:
    kline_data = json.load(f)

print(f"加载数据: {len(kline_data)} 只股票")

def calculate_rsi(prices, period=3):
    """
    计算RSI指标
    period=3: RSI3日（通达信B1公式标准）
    period=14: RSI14日（标准）
    """
    if len(prices) < period + 1:
        return None
    
    # RSI3公式: SMA(MAX(CLOSE-LC,0),3,1)/SMA(ABS(CLOSE-LC),3,1)*100
    if period == 3:
        # RSI3特殊计算
        if len(prices) < 2:
            return None
        temp1 = []
        temp2 = []
        for i in range(1, len(prices)):
            lc = prices[i-1]
            diff = prices[i] - lc
            temp1.append(max(diff, 0))
            temp2.append(abs(diff))
        
        if len(temp1) < 3:
            return None
        
        # SMA(TEMP1,3,1) - 3日简单移动平均
        avg_gain = sum(temp1[-3:]) / 3
        avg_loss = sum(temp2[-3:]) / 3
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    else:
        # 标准RSI计算
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

def calculate_kdj(highs, lows, closes, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    if len(closes) < n + 1:
        return None, None, None
    
    # 计算RSV
    rsv = []
    for i in range(n, len(closes)):  # 从第n个开始，确保有n个数据
        high_n = max(highs[i-n:i])
        low_n = min(lows[i-n:i])
        close = closes[i]
        if high_n != low_n:
            rsv_val = (close - low_n) / (high_n - low_n) * 100
        else:
            rsv_val = 50
        rsv.append(rsv_val)
    
    if not rsv:
        return None, None, None
    
    # 计算K、D、J值
    k = 50.0
    d = 50.0
    k_values = []
    d_values = []
    
    for rsv_val in rsv:
        k = (2/3) * k + (1/3) * rsv_val
        d = (2/3) * d + (1/3) * k
        k_values.append(k)
        d_values.append(d)
    
    j = 3 * k - 2 * d
    
    return round(k_values[-1], 2), round(d_values[-1], 2), round(j, 2)

def calculate_b1_b2_signals(kline_list, j_value=None, white_line=None, yellow_line=None):
    """
    计算B1/B2信号（按通达信公式）
    B1: 白线>黄线 + J<13 + 缩量
    B2: 前日J<0 + 涨幅>3.95% + 放量 + 当日J<55
    """
    if not kline_list or len(kline_list) < 5:
        return {"b1": False, "b2": False, "details": {}}
    
    df = pd.DataFrame(kline_list)
    
    # 最新几根K线
    last1 = df.iloc[-1]
    prev1 = df.iloc[-2] if len(df) >= 2 else None
    
    # 成交量判断
    vol_today = last1.get('amount', 0)
    vol_prev = prev1.get('amount', 0) if prev1 is not None else vol_today
    vol_ratio = vol_today / vol_prev if vol_prev > 0 else 1
    
    # 放量: 成交量 > 昨日
    vol_increase = vol_today > vol_prev
    
    # 缩量: 成交量 < 20日均量的50%
    vol_ma20 = df['amount'].rolling(window=20).mean()
    is_shrinking = vol_today < vol_ma20.iloc[-1] * 0.5 if len(df) >= 20 else False
    
    # ===== B1信号: 白线>黄线 + J<13 + 缩量 =====
    b1_conditions = {}
    b1 = False
    
    # 条件1: 白线>黄线
    if white_line and yellow_line:
        b1_conditions['白线>黄线'] = white_line > yellow_line
    
    # 条件2: J<13
    b1_conditions['J<13'] = j_value is not None and j_value < 13
    
    # 条件3: 缩量
    b1_conditions['缩量'] = is_shrinking
    
    # B1需要三个条件都满足
    b1 = all([b1_conditions.get('白线>黄线', False), 
              b1_conditions.get('J<13', False), 
              b1_conditions.get('缩量', False)])
    
    # ===== B2信号: 按B2.txt公式 =====
    # COND1: 前一交易日J值为负 (J_LAST < 0)
    # COND2: 涨幅>3.95%
    # COND3: 放量 (VOL > VOL_LAST)
    # COND4: 当日J值<55
    
    # 计算前一天的J值
    prev_j = None
    if len(df) >= 10:  # 需要足够数据计算KDJ
        highs = df['high'].tolist()[:-1]  # 除了今天
        lows = df['low'].tolist()[:-1]
        closes = df['close'].tolist()[:-1]
        
        n = 9
        rsv = []
        for i in range(n, len(closes)):
            high_n = max(highs[i-n:i])
            low_n = min(lows[i-n:i])
            close = closes[i]
            if high_n != low_n:
                rsv_val = (close - low_n) / (high_n - low_n) * 100
            else:
                rsv_val = 50
            rsv.append(rsv_val)
        
        if rsv:
            k = 50.0
            d = 50.0
            for rsv_val in rsv:
                k = (2/3) * k + (1/3) * rsv_val
                d = (2/3) * d + (1/3) * k
            prev_j = 3 * k - 2 * d
    
    # 计算涨幅
    change_pct = 0
    if prev1 is not None:
        change_pct = (last1['close'] - prev1['close']) / prev1['close'] * 100
    
    b2_conditions = {}
    b2 = False
    
    # B2四个条件
    b2_conditions['前日J<0'] = prev_j is not None and prev_j < 0
    b2_conditions['涨幅>3.95%'] = change_pct > 3.95
    b2_conditions['放量'] = vol_increase
    b2_conditions['当日J<55'] = j_value is not None and j_value < 55
    
    if (prev_j is not None and prev_j < 0 and 
        change_pct > 3.95 and vol_increase and 
        j_value is not None and j_value < 55):
        b2 = True
    
    return {
        "b1": b1,
        "b2": b2,
        "prev_j": round(prev_j, 2) if prev_j else None,
        "vol_increase": vol_increase,
        "is_shrinking": is_shrinking,
        "vol_ratio": round(vol_ratio, 2),
        "change_pct": round(change_pct, 2),
        "j_value": j_value,
        "details": {
            "b1_conditions": b1_conditions,
            "b2_conditions": b2_conditions
        }
    }
    


def calculate_indicators(stock_code, data):
    """计算技术指标（v4.0 - 新增前期走势类型识别）"""
    kline = data.get("kline", [])
    if not kline or len(kline) < 30:
        return None
    
    df = pd.DataFrame(kline)
    
    # 计算基础MA
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA30'] = df['close'].rolling(window=30).mean()
    
    # ===== v3.0 趋势线公式 =====
    # 白线 = EMA(EMA(C,10),10) - 双重指数移动平均
    df['EMA10'] = df['close'].ewm(span=10, adjust=False).mean()
    df['white_line'] = df['EMA10'].ewm(span=10, adjust=False).mean()  # EMA(EMA(C,10),10)
    
    # 黄线 = (MA14 + MA28 + MA57 + MA114) / 4（动态调整，数据不够时减少均线数量）
    df['MA14'] = df['close'].rolling(window=14).mean()
    df['MA28'] = df['close'].rolling(window=28).mean()
    df['MA57'] = df['close'].rolling(window=57).mean() if len(df) >= 57 else pd.Series([np.nan]*len(df), index=df.index)
    df['MA114'] = df['close'].rolling(window=114).mean() if len(df) >= 114 else pd.Series([np.nan]*len(df), index=df.index)
    
    # 动态计算黄线（根据可用数据）
    def calc_yellow_line(row):
        vals = []
        if pd.notna(row['MA14']): vals.append(row['MA14'])
        if pd.notna(row['MA28']): vals.append(row['MA28'])
        if pd.notna(row['MA57']): vals.append(row['MA57'])
        if pd.notna(row['MA114']): vals.append(row['MA114'])
        return sum(vals) / len(vals) if vals else np.nan
    
    df['yellow_line'] = df.apply(calc_yellow_line, axis=1)
    
    # 最新的趋势线值
    latest = df.iloc[-1]
    white_line = latest['white_line']
    yellow_line = latest['yellow_line']
    
    # MA多头排列: MA5 > MA10 > MA20 > MA30
    ma_bullish = bool(latest['MA5'] > latest['MA10'] > latest['MA20'] > latest['MA30'])
    
    # 趋势线位置判断（白线/黄线）
    current_price = data['today_close']
    
    # 判断白线黄线关系和价格位置
    if white_line > yellow_line:
        # 多头趋势
        if current_price > white_line:
            position = "白线附近"
        elif current_price > yellow_line:
            position = "黄线附近"
        else:
            position = "跌破黄线"
    else:
        # 空头趋势
        position = "白线<黄线"
    
    # 计算量比 (今日成交量 / 5日平均成交量)
    df['vol_ma5'] = df['amount'].rolling(window=5).mean()
    current_vol = df.iloc[-1]['amount']
    avg_vol5 = df.iloc[-1]['vol_ma5']
    vol_ratio = current_vol / avg_vol5 if avg_vol5 and avg_vol5 > 0 else 0
    
    # 成交量变化 (今日成交量 vs 昨日)
    vol_change = (df.iloc[-1]['amount'] - df.iloc[-2]['amount']) / df.iloc[-2]['amount'] * 100 if len(df) >= 2 else 0
    
    # 判断是否放量上涨
    up_or_down = "上涨" if data['change_pct'] > 0 else "下跌"
    volume_up = bool(vol_change > 0)
    
    # ===== 新增 v3.0 指标 =====
    
    # RSI3（通达信B1公式标准）
    rsi = calculate_rsi(df['close'].tolist(), 3)
    
    # KDJ
    k, d, j = calculate_kdj(df['high'].tolist(), df['low'].tolist(), df['close'].tolist())
    
    # B1/B2信号（传入J值和趋势线用于判断）
    b_signals = calculate_b1_b2_signals(kline, j_value=j, white_line=white_line, yellow_line=yellow_line)
    
    # ===== v4.0 新增：前期走势类型识别 =====
    # 20日涨跌幅
    close_20d_ago = df.iloc[-20]['close'] if len(df) >= 20 else df.iloc[0]['close']
    change_20d = (current_price - close_20d_ago) / close_20d_ago * 100 if close_20d_ago > 0 else 0
    
    # 20日振幅
    high_20d = df['high'].tail(20).max()
    low_20d = df['low'].tail(20).min()
    amplitude_20d = (high_20d - low_20d) / low_20d * 100 if low_20d > 0 else 0
    
    # 识别走势类型
    trend_type = "延续型"  # 默认
    if change_20d < -10:
        trend_type = "扭转型"  # 前期下跌超10%
    elif amplitude_20d < 15:
        trend_type = "改变型"  # 前期横盘振幅<15%
    elif change_20d > 5:
        trend_type = "延续型"  # 前期上涨
    
    # 前期走势详细数据
    trend_data = {
        "type": trend_type,
        "change_20d": round(change_20d, 2),
        "amplitude_20d": round(amplitude_20d, 2),
        "close_20d_ago": round(close_20d_ago, 2),
        "high_20d": round(high_20d, 2),
        "low_20d": round(low_20d, 2)
    }
    
    return {
        "stock_code": stock_code,
        "name": data['name'],
        "change_pct": data['change_pct'],
        "ma_bullish": ma_bullish,
        "MA5": round(latest['MA5'], 2),
        "MA10": round(latest['MA10'], 2),
        "MA20": round(latest['MA20'], 2),
        "MA30": round(latest['MA30'], 2) if pd.notna(latest['MA30']) else None,
        "white_line": round(white_line, 2),   # v3.0: EMA(EMA(C,10),10)
        "yellow_line": round(yellow_line, 2), # v3.0: (MA14+MA28+MA57+MA114)/4
        "position": position,
        "price": current_price,
        "vol_ratio": round(vol_ratio, 2),
        "vol_change": round(vol_change, 2),
        "up_or_down": up_or_down,
        "volume_up": volume_up,
        # v3.0 新增
        "rsi14": rsi,
        "k": k,
        "d": d,
        "j": j,
        "b1": b_signals.get("b1", False),
        "b2": b_signals.get("b2", False),
        # v4.0 新增
        "trend_type": trend_type,
        "trend_data": trend_data
    }

# 计算所有股票的技术指标
indicators = {}
for stock_code, data in kline_data.items():
    result = calculate_indicators(stock_code, data)
    if result:
        indicators[stock_code] = result

print(f"计算完成: {len(indicators)} 只股票")

# 统计多头排列
bullish_count = sum(1 for v in indicators.values() if v['ma_bullish'])
print(f"MA多头排列: {bullish_count} 只")

# 统计B1/B2信号
b1_count = sum(1 for v in indicators.values() if v.get('b1'))
b2_count = sum(1 for v in indicators.values() if v.get('b2'))
print(f"B1信号: {b1_count} 只")
print(f"B2信号: {b2_count} 只")

# 保存到文件
output_path = "qdk_output/qdk_indicators.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(indicators, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)

print(f"\n数据已保存到: {output_path}")
