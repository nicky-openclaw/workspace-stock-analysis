#!/usr/bin/env python3
"""
启动K选股 Step 3: 指标计算
读取 qdk_kline.json，计算MA/量比/RSI3/KDJ等指标

关键修改(2026-03-09):
- K线数据：不复权（adjust=''）
- 涨跌幅：来自实时API字段32
- RSI：使用通达信B1公式RSI3
"""

import json
import numpy as np
from pathlib import Path

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
OUTPUT_DIR = WORKSPACE / "qdk_output"


def calc_ma(closes: list, n: int):
    if len(closes) < n:
        return None
    return round(sum(closes[-n:]) / n, 4)


def tongda_sma(series, n, m):
    """通达信SMA: SMA(X,N,M) = (X * M + 前一日SMA * (N-M)) / N"""
    result = []
    for i in range(len(series)):
        if i == 0:
            result.append(series[i] if series[i] is not None else 0)
        else:
            prev = result[-1]
            curr = series[i] if series[i] is not None else 0
            result.append((curr * m + prev * (n - m)) / n)
    return result


def calc_rsi3(closes):
    """
    通达信B1公式的RSI3计算
    RSI:SMA(TEMP1,3,1)/SMA(TEMP2,3,1)*100
    TEMP1 = MAX(CLOSE-REF(CLOSE,1), 0)
    TEMP2 = ABS(CLOSE-REF(CLOSE,1))
    """
    if len(closes) < 4:
        return None
    
    # 计算TEMP1和TEMP2
    temp1 = []  # MAX(CLOSE-REF(CLOSE,1), 0)
    temp2 = []  # ABS(CLOSE-REF(CLOSE,1))
    
    for i in range(len(closes)):
        if i == 0:
            temp1.append(0)
            temp2.append(0)
        else:
            diff = closes[i] - closes[i-1]
            temp1.append(max(diff, 0))
            temp2.append(abs(diff))
    
    # 计算SMA
    n, m = 3, 1
    sma1 = tongda_sma(temp1, n, m)
    sma2 = tongda_sma(temp2, n, m)
    
    # RSI = SMA1 / SMA2 * 100
    if sma2[-1] == 0:
        return 0
    rsi = (sma1[-1] / sma2[-1]) * 100
    return round(rsi, 2)


def calc_kdj(highs, lows, closes):
    """
    KDJ计算
    """
    if len(closes) < 9:
        return None, None, None
    
    # 计算RSV
    rsv = []
    for i in range(len(closes)):
        if i < 8:
            rsv.append(50)  # 不足9天时设为50
        else:
            low_min = min(lows[i-8:i+1])
            high_max = max(highs[i-8:i+1])
            if high_max == low_min:
                rsv.append(50)
            else:
                rsv.append((closes[i] - low_min) / (high_max - low_min) * 100)
    
    # 计算K, D (EMA方式)
    k_values = []
    d_values = []
    for i in range(len(rsv)):
        if i == 0:
            k_values.append(rsv[i])
            d_values.append(rsv[i])
        else:
            # K = 2/3 * 前一日K + 1/3 * RSV
            k = 2/3 * k_values[-1] + 1/3 * rsv[i]
            d = 2/3 * d_values[-1] + 1/3 * k
            k_values.append(k)
            d_values.append(d)
    
    # J = 3*K - 2*D
    k = k_values[-1]
    d = d_values[-1]
    j = 3 * k - 2 * d
    
    return round(k, 2), round(d, 2), round(j, 2)


def calc_trend_lines(closes: list) -> tuple:
    """
    趋势线计算：白线=EMA(EMA(C,10),10)，黄线=(MA14+MA28+MA57+MA114)/4
    返回：白线, 黄线, 白线方向(7天), 黄线方向(7天), 是否近期金叉(3天内)
    """
    if len(closes) < 114:
        return None, None, None, None, False
    
    import pandas as pd
    s = pd.Series(closes)
    
    # 计算历史白线序列（用于判断方向）
    ema1 = s.ewm(span=10, adjust=False).mean()
    white_series = ema1.ewm(span=10, adjust=False).mean()
    
    # 黄线历史序列
    ma14 = s.rolling(14).mean()
    ma28 = s.rolling(28).mean()
    ma57 = s.rolling(57).mean()
    ma114 = s.rolling(114).mean()
    yellow_series = (ma14 + ma28 + ma57 + ma114) / 4
    
    # 今日值
    white_line = round(white_series.iloc[-1], 2)
    yellow_line = round(yellow_series.iloc[-1], 2)
    
    # 7天方向：连续7天白线上升
    if len(white_series) >= 8:
        white_7d = white_series.iloc[-8:].values
        white_rising_7d = all(white_7d[i] < white_7d[i+1] for i in range(6))
    else:
        white_rising_7d = False
    
    # 当天方向：白线今天 > 昨天
    if len(white_series) >= 2:
        white_rising = white_series.iloc[-1] > white_series.iloc[-2]
    else:
        white_rising = False
    
    # 7天方向：连续7天黄线上升
    if len(yellow_series) >= 8:
        yellow_7d = yellow_series.iloc[-8:].values
        yellow_rising_7d = all(yellow_7d[i] < yellow_7d[i+1] for i in range(6))
    else:
        yellow_rising_7d = False
    
    # 当天方向：黄线今天 > 昨天
    if len(yellow_series) >= 2:
        yellow_rising = yellow_series.iloc[-1] > yellow_series.iloc[-2]
    else:
        yellow_rising = False
    
    # 近期金叉（3天内）
    if len(white_series) >= 3:
        white_yesterday = white_series.iloc[-2]
        yellow_yesterday = yellow_series.iloc[-2]
        white_2days_ago = white_series.iloc[-3]
        yellow_2days_ago = yellow_series.iloc[-3]
        golden_cross_recent = (white_yesterday > yellow_yesterday) and (white_2days_ago <= yellow_2days_ago)
    else:
        golden_cross_recent = False
    
    # 60天趋势斜率（线性回归）
    def calc_slope(series, days=60):
        """计算线性回归斜率"""
        if len(series) < days:
            days = len(series)
        y = series[-days:].values
        x = np.arange(len(y))
        x_mean = x.mean()
        y_mean = y.mean()
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        return numerator / denominator if denominator != 0 else 0
    
    white_slope_60 = calc_slope(white_series, 60)
    yellow_slope_60 = calc_slope(yellow_series, 60) if len(yellow_series) >= 60 else 0
    
    return white_line, yellow_line, white_rising_7d, yellow_rising_7d, golden_cross_recent, white_slope_60, yellow_slope_60


def parse_kline(kline_list: list):
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
    kline_file = OUTPUT_DIR / "qdk_kline.json"
    with open(kline_file, encoding="utf-8") as f:
        kline_data = json.load(f)

    stocks = kline_data["stocks"]
    total = len(stocks)
    print(f"共 {total} 只股票，开始计算启动K指标...")

    results = []
    errors = []

    for i, stock in enumerate(stocks):
        code = stock["code"]
        name = stock.get("name", code)
        kline = stock.get("kline", [])

        if not kline or len(kline) < 6:
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

            # 价格 - 优先用实时API的涨跌幅！
            # 关键：涨跌幅用实时API字段32，不自己计算！
            today_close = closes[-1]
            yesterday_close = closes[-2] if len(closes) > 1 else today_close

            # 优先用实时API的涨幅
            stock_realtime = stock.get("realtime", {})
            if stock_realtime and "change_pct" in stock_realtime:
                change_pct = stock_realtime["change_pct"]  # 直接用字段32！
                current_price = stock_realtime.get("current_price", today_close)
                # 如果实时价格比K线收盘价更新，用实时价格
                if current_price and current_price != today_close:
                    today_close = current_price
            else:
                # 没有实时数据才自己计算（后备方案）
                change_pct = round((today_close - yesterday_close) / yesterday_close * 100, 2) if yesterday_close else 0

            # 量能
            today_vol = vols[-1]
            yesterday_vol = vols[-2] if len(vols) > 1 else today_vol
            vol_ratio = round(today_vol / yesterday_vol, 2) if yesterday_vol else 0

            vols_20 = vols[-20:] if len(vols) >= 20 else vols
            avg_vol_20 = sum(vols_20) / len(vols_20)
            
            # 20日最大量
            max_vol_20 = max(vols_20)
            
            # 近5日最大量（含今日）
            vols_5 = vols[-5:] if len(vols) >= 5 else vols
            max_vol_5d = max(vols_5)
            has_double_vol_5d = max_vol_5d >= avg_vol_20 * 2

            # 今日最低价（用于判断开盘位置）
            today_low = lows[-1] if lows else None
            
            # 20日/60日最高价（用于判断是否突破）
            closes_20 = closes[-20:] if len(closes) >= 20 else closes
            closes_60 = closes[-60:] if len(closes) >= 60 else closes
            high_20 = max(closes_20)
            high_60 = max(closes_60)

            # MA20方向
            ma20_rising = (ma20 > ma20_prev) if (ma20 and ma20_prev) else None

            # RSI3（通达信B1公式）
            rsi3 = calc_rsi3(closes)

            # KDJ
            k, d, j = calc_kdj(highs, lows, closes)

            # 趋势线（白线=EMA(EMA(C,10),10)，黄线=(MA14+MA28+MA57+MA114)/4）
            # 返回：白线, 黄线, 白线7天方向, 黄线7天方向, 近期金叉, 60天斜率
            white_line, yellow_line, white_rising_7d, yellow_rising_7d, golden_cross_recent, white_slope_60, yellow_slope_60 = calc_trend_lines(closes)
            
            # 当天方向：白线/黄线今天vs昨天（保留作为参考）
            if len(closes) >= 2:
                import pandas as pd
                s = pd.Series(closes)
                ema1 = s.ewm(span=10, adjust=False).mean()
                white_series = ema1.ewm(span=10, adjust=False).mean()
                ma14 = s.rolling(14).mean()
                ma28 = s.rolling(28).mean()
                ma57 = s.rolling(57).mean()
                ma114 = s.rolling(114).mean()
                yellow_series = (ma14 + ma28 + ma57 + ma114) / 4
                white_rising = white_series.iloc[-1] > white_series.iloc[-2] if len(white_series) >= 2 else False
                yellow_rising = yellow_series.iloc[-1] > yellow_series.iloc[-2] if len(yellow_series) >= 2 else False
            else:
                white_rising = False
                yellow_rising = False

            # 位置判断
            ma20_dist_pct = round((today_close - ma20) / ma20 * 100, 2) if ma20 else None
            ma5_dist_pct = round((today_close - ma5) / ma5 * 100, 2) if ma5 else None

            # 昨日收盘 vs 白线（判断是否刚站回白线）
            yesterday_below_white = (yesterday_close < white_line) if white_line else False
            today_above_white = (today_close > white_line) if white_line else False
            just_reclaimed_white = yesterday_below_white and today_above_white

            # 转为Python原生类型，避免numpy bool/float JSON序列化报错
            def to_py(v):
                if v is None:
                    return None
                if isinstance(v, (bool,)):
                    return bool(v)
                try:
                    return float(v)
                except Exception:
                    return v

            results.append({
                "code": code,
                "name": name,
                "today_close": today_close,
                "yesterday_close": yesterday_close,
                "change_pct": change_pct,  # 来自实时API字段32
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
                "ma20_prev": ma20_prev,
                "ma20_rising": bool(ma20_rising) if ma20_rising is not None else None,
                "ma20_dist_pct": ma20_dist_pct,
                "ma5_dist_pct": ma5_dist_pct,
                "today_vol": today_vol,
                "yesterday_vol": yesterday_vol,
                "avg_vol_20": round(avg_vol_20, 0),
                "vol_ratio": vol_ratio,
                "has_double_vol_5d": bool(has_double_vol_5d),
                "just_reclaimed_ma5": bool(just_reclaimed_white),  # 字段名保持兼容，实际用white_line判断
                "rsi3": rsi3,  # 通达信B1公式RSI3
                "k": k,
                "d": d,
                "j": j,
                "white_line": white_line,  # EMA(EMA(C,10),10)
                "yellow_line": yellow_line,  # (MA14+MA28+MA57+MA114)/4
                "white_rising": bool(white_rising) if white_rising is not None else None,  # 白线当天方向向上
                "yellow_rising": bool(yellow_rising) if yellow_rising is not None else None,  # 黄线当天方向向上
                "white_rising_7d": bool(white_rising_7d) if white_rising_7d is not None else None,  # 白线7天连续向上
                "yellow_rising_7d": bool(yellow_rising_7d) if yellow_rising_7d is not None else None,  # 黄线7天连续向上
                "golden_cross_recent": bool(golden_cross_recent) if golden_cross_recent is not None else False,  # 近期金叉(3天内)
                "white_slope_60": round(white_slope_60, 4) if white_slope_60 is not None else None,  # 白线60天线性回归斜率
                "yellow_slope_60": round(yellow_slope_60, 4) if yellow_slope_60 is not None else None,  # 黄线60天线性回归斜率
                "today_low": today_low,  # 今日最低价（判断开盘位置）
                "high_20": round(high_20, 2),  # 20日最高价
                "high_60": round(high_60, 2),  # 60日最高价
                "max_vol_20": round(max_vol_20, 0),  # 20日最大量
            })

        except Exception as e:
            errors.append(f"{code}:{e}")

        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{total} | 已计算: {len(results)}")

    # 自检：涨幅异常检查
    abnormal = []
    for s in results:
        cp = s.get("change_pct", 0)
        # 涨幅超过30%或小于-10%视为异常（可能是数据问题）
        if cp > 30 or cp < -10:
            abnormal.append(f"{s['code']}: {cp}%")

    output = {
        "total": total,
        "success_count": len(results),
        "error_count": len(errors),
        "data_date": kline_data.get("data_date", "unknown"),
        "stocks": results,
        "errors": errors[:20],
        "abnormal_change_pct": abnormal,  # 自检结果
    }

    output_file = OUTPUT_DIR / "qdk_indicators.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 指标计算完成: 成功{len(results)} | 错误{len(errors)}")

    # 自检提醒
    if abnormal:
        print(f"\n⚠️ 涨幅异常提醒: {abnormal[:5]}")
        print("   注意：涨幅>30%或<-10%可能是数据问题，请检查！")


if __name__ == "__main__":
    main()
