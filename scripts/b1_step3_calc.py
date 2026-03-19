#!/usr/bin/env python3
"""
Step 3: 技术指标计算
读取 b1_kline.json，计算MA5/MA10/MA20/J值/RSI/量比等指标
"""

import json
from pathlib import Path
import numpy

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
OUTPUT_DIR = WORKSPACE / "b1_output"


from typing import Optional, Tuple


def calc_trend_lines(closes: list) -> tuple:
    """趋势线计算：白线=EMA(EMA(C,10),10)，黄线=(MA14+MA28+MA57+MA114)/4"""
    if len(closes) < 114:
        return None, None
    import pandas as pd
    s = pd.Series(closes)
    ema1 = s.ewm(span=10, adjust=False).mean()
    white_line = ema1.ewm(span=10, adjust=False).mean().iloc[-1]
    ma14 = s.rolling(14).mean().iloc[-1]
    ma28 = s.rolling(28).mean().iloc[-1]
    ma57 = s.rolling(57).mean().iloc[-1]
    ma114 = s.rolling(114).mean().iloc[-1]
    yellow_line = (ma14 + ma28 + ma57 + ma114) / 4
    return round(white_line, 2), round(yellow_line, 2)


def calc_ma(closes: list, n: int) -> Optional[float]:
    """计算N日均线"""
    if len(closes) < n:
        return None
    return round(sum(closes[-n:]) / n, 4)


def calc_kdj(highs, lows, closes, n=9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """计算KDJ指标，返回最后一个K/D/J值"""
    if len(closes) < n:
        return None, None, None

    k, d = 50.0, 50.0
    for i in range(len(closes)):
        if i < n - 1:
            continue
        h = max(highs[max(0, i-n+1):i+1])
        l = min(lows[max(0, i-n+1):i+1])
        rsv = ((closes[i] - l) / (h - l) * 100) if h != l else 50
        k = 2/3 * k + 1/3 * rsv
        d = 2/3 * d + 1/3 * k

    j = 3 * k - 2 * d
    return round(k, 2), round(d, 2), round(j, 2)


def calc_rsi(closes, n=14):
    """计算RSI指标"""
    if len(closes) < n + 1:
        return None

    gains, losses = [], []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i-1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))

    if len(gains) < n:
        return None

    avg_gain = sum(gains[-n:]) / n
    avg_loss = sum(losses[-n:]) / n

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)


def calc_rsi3(closes):
    """
    计算RSI3（通达信B1公式）
    公式：SMA(MAX(CLOSE-LC,0),3,1)/SMA(ABS(CLOSE-LC),3,1)*100
    其中LC=前一根收盘价
    """
    if len(closes) < 4:
        return None
    
    # 计算CLOSE-LC (LC=前一根收盘价)
    max_close_lc = []  # MAX(CLOSE-LC,0)
    abs_close_lc = []  # ABS(CLOSE-LC)
    
    for i in range(1, len(closes)):
        close_lc = closes[i] - closes[i-1]
        max_close_lc.append(max(close_lc, 0))
        abs_close_lc.append(abs(close_lc))
    
    if len(max_close_lc) < 3:
        return None
    
    # SMA(X,3,1) = (X1+X2+X3)/3
    sma_max = sum(max_close_lc[-3:]) / 3
    sma_abs = sum(abs_close_lc[-3:]) / 3
    
    if sma_abs == 0:
        return 100.0
    
    rsi3 = (sma_max / sma_abs) * 100
    return round(rsi3, 2)


def detect_key_k(highs, lows, closes, vols, yellow_line):
    """
    检测关键K（知识库定义）
    关键K类型：
    1. 底部平地惊雷：横盘转上涨，放量涨停
    2. 紧急刹车：下跌转横盘
    3. 区域突破：突破前期高点的放量大阳线
    
    简化判断：近20日内涨幅>=5%且放量（量比>=1.5）的大阳线
    """
    if len(closes) < 20 or len(vols) < 20:
        return {"has_key_k": False, "key_k_count": 0, "has_biliang": False}
    
    key_k_count = 0
    biliang_count = 0
    avg_vol_20 = sum(vols[-20:]) / 20
    
    for i in range(-20, 0):  # 近20日
        idx = len(closes) + i
        if idx < 1:
            continue
        
        change = (closes[idx] - closes[idx-1]) / closes[idx-1] * 100
        vol_ratio = vols[idx] / avg_vol_20
        
        # 关键K：涨幅>=5% + 放量
        if change >= 5 and vol_ratio >= 1.5:
            key_k_count += 1
        
        # 倍量柱：成交量>=2倍
        if vols[idx] >= vols[idx-1] * 2:
            biliang_count += 1
    
    return {
        "has_key_k": bool(key_k_count > 0),
        "key_k_count": int(key_k_count),
        "has_biliang": bool(biliang_count > 0),
        "biliang_count": int(biliang_count),
    }


def calc_volume_stats(vols: list):
    """计算量能统计"""
    if len(vols) < 2:
        return {}

    today_vol = vols[-1]
    yesterday_vol = vols[-2]

    vols_20 = vols[-20:] if len(vols) >= 20 else vols
    avg_vol_20 = sum(vols_20) / len(vols_20)
    min_vol_20 = min(vols_20)
    max_vol_20 = max(vols_20)

    # 近20日是否出现过倍量柱
    has_double_vol = max_vol_20 >= avg_vol_20 * 2

    # 量能信号判断
    if today_vol <= min_vol_20 * 1.2:
        vol_signal = "地量"
    elif today_vol < yesterday_vol:
        vol_signal = "缩量"
    elif today_vol >= yesterday_vol * 2:
        vol_signal = "倍量"
    else:
        vol_signal = "正常"

    return {
        "today_vol": today_vol,
        "yesterday_vol": yesterday_vol,
        "avg_vol_20": round(avg_vol_20, 0),
        "min_vol_20": min_vol_20,
        "max_vol_20": max_vol_20,
        "vol_ratio": round(today_vol / yesterday_vol, 2) if yesterday_vol else 0,
        "has_double_vol_20d": has_double_vol,
        "vol_signal": vol_signal,
    }


def parse_kline(kline_list: list):
    """解析K线列表，返回OHLCV序列"""
    dates, opens, highs, lows, closes, vols = [], [], [], [], [], []
    for bar in kline_list:
        try:
            dates.append(bar[0])
            opens.append(float(bar[1]))
            closes.append(float(bar[2]))
            highs.append(float(bar[3]))
            lows.append(float(bar[4]))
            vols.append(float(bar[5]))
        except (IndexError, ValueError):
            continue
    return dates, opens, highs, lows, closes, vols


def main():
    kline_file = OUTPUT_DIR / "b1_kline.json"
    with open(kline_file, encoding="utf-8") as f:
        kline_data = json.load(f)

    stocks = kline_data["stocks"]
    total = len(stocks)
    print(f"共 {total} 只股票，开始计算指标...")

    results = []
    errors = []

    for i, stock in enumerate(stocks):
        code = stock["code"]
        name = stock.get("name", code)
        kline = stock.get("kline", [])

        if not kline or len(kline) < 10:
            errors.append(code)
            continue

        try:
            dates, opens, highs, lows, closes, vols = parse_kline(kline)

            if len(closes) < 5:
                errors.append(code)
                continue

            # 均线
            ma5 = calc_ma(closes, 5)
            ma10 = calc_ma(closes, 10)
            ma20 = calc_ma(closes, 20)
            ma20_prev = calc_ma(closes[:-1], 20) if len(closes) > 20 else None

            # KDJ
            _, _, j = calc_kdj(highs, lows, closes)

            # RSI（标准RSI14 + RSI3通达信B1公式）
            rsi14 = calc_rsi(closes, 14)
            rsi3 = calc_rsi3(closes)
            
            # 趋势线（白线/黄线）- 需要提前计算供其他函数使用
            white_line, yellow_line = calc_trend_lines(closes)
            if white_line is None:
                white_line = 0
            if yellow_line is None:
                yellow_line = 0
            
            # 今日收盘价（先取K线收盘价，后面会被实时API覆盖）
            today_close = closes[-1]
            
            # 关键K检测
            key_k_info = detect_key_k(highs, lows, closes, vols, yellow_line)

            # 量能
            vol_stats = calc_volume_stats(vols)

            # 振幅计算（根据超级B1公式）
            # 近期振幅：近20日
            highs_20 = highs[-20:] if len(highs) >= 20 else highs
            lows_20 = lows[-20:] if len(lows) >= 20 else lows
            recent_amplitude = round((max(highs_20) - min(lows_20)) / min(lows_20) * 100, 2) if min(lows_20) else 0
            
            # 远期振幅：近50日
            highs_50 = highs[-50:] if len(highs) >= 50 else highs
            lows_50 = lows[-50:] if len(lows) >= 50 else lows
            far_amplitude = round((max(highs_50) - min(lows_50)) / min(lows_50) * 100, 2) if min(lows_50) else 0
            
            # 近期异动：近期振幅>=15%
            recent_active = recent_amplitude >= 15
            
            # 远期异动：远期振幅>=30%
            far_active = far_amplitude >= 30

            # 回踩白线判断（根据公式）
            # 回踩白线: 收盘>=白线且距离<=2% 或 收盘<白线且距离<0.8%
            if white_line:
                white_dist_pct = round(abs(today_close - white_line) / white_line * 100, 2)
                pullback_white = (today_close >= white_line and white_dist_pct <= 2) or \
                                 (today_close < white_line and white_dist_pct < 0.8)
            else:
                white_dist_pct = None
                pullback_white = False
            
            # 回踩黄线判断
            # 回踩黄线: 收盘>=黄线且距离<=1.5% 或 收盘<黄线且距离<0.8%
            if yellow_line:
                yellow_dist_pct = round(abs(today_close - yellow_line) / yellow_line * 100, 2)
                pullback_yellow = (today_close >= yellow_line and yellow_dist_pct <= 1.5) or \
                                  (today_close < yellow_line and yellow_dist_pct < 0.8)
            else:
                yellow_dist_pct = None
                pullback_yellow = False

            # 价格信息 - 优先用实时API涨跌幅！
            today_close = closes[-1]
            yesterday_close = closes[-2] if len(closes) > 1 else today_close
            
            # 优先用实时API的涨跌幅字段32
            stock_realtime = stock.get("realtime", {})
            if stock_realtime and "change_pct" in stock_realtime:
                change_pct = stock_realtime["change_pct"]
                current_price = stock_realtime.get("current_price", today_close)
                if current_price and current_price != today_close:
                    today_close = current_price
            else:
                # 后备：自己计算
                change_pct = round((today_close - yesterday_close) / yesterday_close * 100, 2) if yesterday_close else 0

            # MA20方向
            ma20_rising = (ma20 > ma20_prev) if (ma20 and ma20_prev) else None

            # 今日收盘与MA20的距离
            ma20_distance_pct = round((today_close - ma20) / ma20 * 100, 2) if ma20 else None

            # 趋势线（白线/黄线）
            white_line, yellow_line = calc_trend_lines(closes)
            if white_line is None:
                white_line = 0
            if yellow_line is None:
                yellow_line = 0

            results.append({
                "code": code,
                "name": name,
                "today_close": today_close,
                "yesterday_close": yesterday_close,
                "change_pct": change_pct,
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
                "ma20_prev": ma20_prev,
                "ma20_rising": ma20_rising,
                "ma20_distance_pct": ma20_distance_pct,
                "white_line": white_line,
                "yellow_line": yellow_line,
                "white_dist_pct": white_dist_pct,
                "yellow_dist_pct": yellow_dist_pct,
                "recent_amplitude": recent_amplitude,
                "far_amplitude": far_amplitude,
                "recent_active": recent_active,
                "far_active": far_active,
                "pullback_white": pullback_white,
                "pullback_yellow": pullback_yellow,
                "j_value": j,
                "rsi14": rsi14,
                "rsi3": rsi3,
                "key_k_info": key_k_info,
                "highs_20": highs_20,
                **vol_stats,
            })

        except Exception as e:
            errors.append(f"{code}:{e}")

        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{total} | 已计算: {len(results)}")

    output = {
        "total": total,
        "success_count": len(results),
        "error_count": len(errors),
        "data_date": kline_data.get("data_date", "unknown"),
        "stocks": results,
        "errors": errors[:20],
    }

    output_file = OUTPUT_DIR / "b1_indicators.json"
    
    # 添加default函数处理numpy类型
    def convert_numpy(obj):
        import numpy as np
        if isinstance(obj, (np.bool_, np.integer)):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=convert_numpy)

    print(f"\n✅ 指标计算完成")
    print(f"   成功: {len(results)} | 错误: {len(errors)}")
    print(f"   输出: {output_file}")


if __name__ == "__main__":
    main()
