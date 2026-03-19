#!/usr/bin/env python3
"""
B1选股 Step3: 计算技术指标
"""
import json
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/Users/nicky/.openclaw/workspace-stock-analysis')
from indicators.library import calc_kdj, calc_rsi, calc_ma

# 读取K线数据
input_file = "/Users/nicky/.openclaw/workspace-stock-analysis/b1_output/b1_kline.json"
output_file = "/Users/nicky/.openclaw/workspace-stock-analysis/b1_output/b1_indicators.json"

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

stocks_data = data['stocks']
date = data['date']
print(f"共读取 {len(stocks_data)} 只股票的K线数据")

# 统计
success_count = 0
error_count = 0
errors = []

# 结果存储
results = {
    "total": 0,
    "date": date,
    "stocks": []
}

def calculate_indicators(stock_code, stock_name, klines):
    """计算单只股票的技术指标"""
    try:
        # 构建DataFrame
        df = pd.DataFrame(klines)
        df['日期'] = pd.to_datetime(df['date'])
        df = df.sort_values('日期').reset_index(drop=True)
        
        # 重命名列为中文
        df = df.rename(columns={
            'open': '开盘',
            'close': '收盘',
            'high': '最高',
            'low': '最低',
            'volume': '成交量'
        })
        
        if len(df) < 20:
            return None
        
        # 计算均线
        ma5 = calc_ma(df, 5).iloc[-1]
        ma10 = calc_ma(df, 10).iloc[-1]
        ma20 = calc_ma(df, 20).iloc[-1]
        
        # MA20方向
        if len(df) >= 2:
            ma20_prev = calc_ma(df, 20).iloc[-2]
            if ma20 > ma20_prev * 1.001:  # 向上
                ma20_direction = "up"
            elif ma20 < ma20_prev * 0.999:  # 向下
                ma20_direction = "down"
            else:  # 走平
                ma20_direction = "flat"
        else:
            ma20_direction = "flat"
        
        # KDJ J值（最近3日）
        k, d, j = calc_kdj(df)
        j_value = j.iloc[-1]
        
        # RSI (14日)
        rsi14 = calc_rsi(df, 14).iloc[-1]
        
        # 成交量相关
        volume = df['成交量'].iloc[-1]
        
        # 20日均量
        ma20_avg_volume = df['成交量'].rolling(20).mean().iloc[-1]
        
        # 量比（今日成交量 / 昨日成交量）
        if len(df) >= 2:
            volume_yesterday = df['成交量'].iloc[-2]
            volume_ratio = volume / volume_yesterday if volume_yesterday > 0 else 1.0
        else:
            volume_ratio = 1.0
        
        # 地量信号：成交量 < 20日均量 * 0.5
        di_liang_signal = volume < ma20_avg_volume * 0.5
        
        # 倍量信号：成交量 > 昨日成交量 * 1.5
        if len(df) >= 2:
            bei_liang_signal = volume > volume_yesterday * 1.5
        else:
            bei_liang_signal = False
        
        # 收盘价与MA20距离（%）
        close_price = df['收盘'].iloc[-1]
        close_ma20_distance_pct = (close_price - ma20) / ma20 * 100
        
        return {
            "code": stock_code,
            "name": stock_name,
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "ma20_direction": ma20_direction,
            "j_value": round(j_value, 2),
            "rsi14": round(rsi14, 2),
            "volume": int(volume),
            "volume_ratio": round(volume_ratio, 2),
            "ma20_avg_volume": int(ma20_avg_volume),
            "di_liang_signal": bool(di_liang_signal),
            "bei_liang_signal": bool(bei_liang_signal),
            "close_ma20_distance_pct": round(close_ma20_distance_pct, 2)
        }
    except Exception as e:
        print(f"[错误] {stock_code} {stock_name}: {str(e)}")
        return None

# 遍历每只股票
for i, stock in enumerate(stocks_data):
    code = stock['code']
    name = stock['name']
    klines = stock.get('klines', [])
    
    if not klines or len(klines) == 0:
        error_count += 1
        errors.append(f"{code} {name} (无K线数据)")
        continue
    
    result = calculate_indicators(code, name, klines)
    
    if result:
        results['stocks'].append(result)
        success_count += 1
    else:
        error_count += 1
        errors.append(f"{code} {name} (计算失败)")
    
    if (i + 1) % 20 == 0:
        print(f"[进度] 已处理 {i + 1} 只")

# 保存结果
results['total'] = len(results['stocks'])
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# 输出统计
print(f"\n========== 任务完成 ==========")
print(f"成功: {success_count}")
print(f"错误: {error_count}")
print(f"总计: {len(stocks_data)}")
print(f"\n结果已保存至: {output_file}")

if errors:
    print(f"\n错误列表(共{len(errors)}只):")
    for err in errors[:10]:
        print(f"  - {err}")
