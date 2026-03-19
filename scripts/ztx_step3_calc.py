#!/usr/bin/env python3
"""
砖型图选股 Step 3: 指标计算
读取 ztx_kline.json，计算MA/J/RSI/砖型值/B1/B2等指标
"""

import json
import sys
from pathlib import Path
from pathlib import Path

WORKSPACE = Path("/Users/nicky/.openclaw/workspace-stock-analysis")
OUTPUT_DIR = WORKSPACE / "ztx_output"
INDICATORS_DIR = WORKSPACE / "indicators"

sys.path.insert(0, str(INDICATORS_DIR))
try:
    from zhuantxing import calc_ztx
    HAS_ZTX = True
except ImportError:
    HAS_ZTX = False
    print("⚠️  zhuantxing.py 未找到，砖型值将用近似公式计算")

try:
    from library import check_b1, check_b2
    HAS_LIB = True
except ImportError:
    HAS_LIB = False
    print("⚠️  library.py 未找到，B1/B2将用内置公式计算")


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


def calc_ma(closes: list, n: int):
    if len(closes) < n:
        return None
    return round(sum(closes[-n:]) / n, 4)


def calc_kdj(highs, lows, closes, n=9):
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


def calc_rsi(closes, n=3):
    """
    RSI3公式: SMA(MAX(CLOSE-LC,0),3,1)/SMA(ABS(CLOSE-LC),3,1)*100
    LC = 上一根K线收盘价 (Wilder平滑)
    """
    if len(closes) < n + 1:
        return None
    
    # 计算每日涨跌 (CLOSE - LC)
    deltas = []
    for i in range(1, len(closes)):
        lc = closes[i - 1]  # 上一根收盘价
        c = closes[i]        # 当前收盘价
        deltas.append(c - lc)
    
    gains = [max(d, 0) for d in deltas]      # 上涨
    losses = [max(-d, 0) for d in deltas]     # 下跌
    abs_deltas = [abs(d) for d in deltas]
    
    if len(gains) < n:
        return None
    
    # Wilder平滑: avg = (prev_avg * (period - 1) + current) / period
    def sma_wilder(values, period):
        if len(values) < period:
            return None
        # 第一个值用简单平均
        avg = sum(values[:period]) / period
        for i in range(period, len(values)):
            avg = (avg * (period - 1) + values[i]) / period
        return avg
    
    avg_gain = sma_wilder(gains, n)
    avg_loss = sma_wilder(losses, n)
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)


def calc_ztx_approx(closes, vols, n=5):
    """砖型值近似计算（library.py不可用时的备用）"""
    if len(closes) < n or len(vols) < n:
        return None
    price_momentum = (closes[-1] - closes[-n]) / closes[-n] * 100
    vol_momentum = vols[-1] / (sum(vols[-n:]) / n)
    return round(price_momentum * vol_momentum * 10, 2)


def check_b1_builtin(ma5, ma20, vol, max_vol_20, j, rsi, amplitude):
    """内置B1判断（library.py不可用时）"""
    if not all([ma5, ma20, vol, max_vol_20, j, rsi]):
        return False
    return (
        ma5 >= ma20 and
        vol < max_vol_20 * 0.416 and
        j < 14 and
        rsi < 23 and
        amplitude >= 15
    )


def check_b2_builtin(j_yesterday, change_pct, vol, vol_yesterday, j_today):
    """内置B2判断"""
    if any(v is None for v in [j_yesterday, change_pct, vol, vol_yesterday, j_today]):
        return False
    return (
        j_yesterday < 0 and
        change_pct > 3.95 and
        vol > vol_yesterday * 1.5 and
        j_today < 55
    )


def parse_kline(kline_list):
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
    kline_file = OUTPUT_DIR / "ztx_kline.json"
    with open(kline_file, encoding="utf-8") as f:
        kline_data = json.load(f)

    stocks = kline_data["stocks"]
    total = len(stocks)
    print(f"共 {total} 只股票，开始计算砖型图指标...")

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
            ma20_rising = (ma20 > ma20_prev) if (ma20 and ma20_prev) else None

            # KDJ & RSI
            k_val, d_val, j_val = calc_kdj(highs, lows, closes)
            _, _, j_yesterday = calc_kdj(highs[:-1], lows[:-1], closes[:-1]) if len(closes) > 1 else (None, None, None)
            rsi = calc_rsi(closes, 3)

            # 价格 - 优先用实时API涨跌幅！
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

            # 振幅（近20日高低点）
            highs_20 = highs[-20:] if len(highs) >= 20 else highs
            lows_20 = lows[-20:] if len(lows) >= 20 else lows
            amplitude = round((max(highs_20) - min(lows_20)) / min(lows_20) * 100, 2) if min(lows_20) else 0

            # 量能
            today_vol = vols[-1]
            yesterday_vol = vols[-2] if len(vols) > 1 else today_vol
            vol_ratio = round(today_vol / yesterday_vol, 2) if yesterday_vol else 0
            vols_20 = vols[-20:] if len(vols) >= 20 else vols
            max_vol_20 = max(vols_20)
            min_vol_20 = min(vols_20)

            # 砖型值
            if HAS_ZTX:
                ztx_today = calc_ztx(closes, vols)
                ztx_yesterday = calc_ztx(closes[:-1], vols[:-1])
                ztx_2days_ago = calc_ztx(closes[:-2], vols[:-2]) if len(closes) > 2 else 0
            else:
                ztx_today = calc_ztx_approx(closes, vols)
                ztx_yesterday = calc_ztx_approx(closes[:-1], vols[:-1])
                ztx_2days_ago = calc_ztx_approx(closes[:-2], vols[:-2]) if len(closes) > 2 else 0

            # 红绿比计算（根据通达信公式）
            # 昨绿 := 昨日砖型值 ≤ 前日砖型值
            # 红柱长度 := 今日砖型值 - 昨日砖型值
            # 昨绿长度 := 昨日砖型值 - 前日砖型值（负值）
            # 红绿比 := 红柱长度 / |昨绿长度|
            # 强红 := 绿转红 且 红绿比 > 0.666
            ztx_change = ztx_today - ztx_yesterday  # 今日增量
            ztx_yesterday_change = ztx_yesterday - ztx_2days_ago  # 昨日增量
            was_green_yesterday = ztx_yesterday_change <= 0  # 昨日走弱（绿）
            red_green_ratio = round(ztx_change / abs(ztx_yesterday_change), 2) if ztx_yesterday_change != 0 else 0
            strong_red = was_green_yesterday and ztx_change > 0 and red_green_ratio >= 0.666  # 强红信号

            # 绿转红判断（核心短线信号）
            # 绿转红：昨日≤0，今日>0
            green_to_red = (ztx_yesterday <= 0) and (ztx_today > 0)
            # 红柱强化：今日砖型值 > 昨日砖型值 且 今日>0
            red_strength = (ztx_today > ztx_yesterday) and (ztx_today > 0)
            
            # 近3日砖型值连续走强
            ztx_3d = None
            if HAS_ZTX:
                ztx_3d = all(
                    calc_ztx(closes[:-(2-k)], vols[:-(2-k)]) < calc_ztx(closes[:-(1-k)], vols[:-(1-k)])
                    for k in range(2)
                ) if len(closes) > 4 else False

            # B1/B2
            if HAS_LIB:
                b1 = check_b1(ma5, ma20, today_vol, max_vol_20, j_val, rsi, amplitude)
                b2 = check_b2(j_yesterday, change_pct, today_vol, yesterday_vol, j_val)
            else:
                b1 = check_b1_builtin(ma5, ma20, today_vol, max_vol_20, j_val, rsi, amplitude)
                b2 = check_b2_builtin(j_yesterday, change_pct, today_vol, yesterday_vol, j_val)

            # 趋势线（白线/黄线）
            white_line, yellow_line = calc_trend_lines(closes)

            results.append({
                "code": code, "name": name,
                "today_close": today_close, "yesterday_close": yesterday_close,
                "change_pct": change_pct,
                "ma5": ma5, "ma10": ma10, "ma20": ma20,
                "ma20_prev": ma20_prev, "ma20_rising": ma20_rising,
                "j_value": j_val, "j_yesterday": j_yesterday, "rsi": rsi,
                "ztx_today": ztx_today, "ztx_yesterday": ztx_yesterday,
                "ztx_3d_consecutive_rising": ztx_3d,
                "green_to_red": green_to_red,  # 绿转红信号
                "red_strength": red_strength,  # 红柱强化
                "red_green_ratio": red_green_ratio,  # 红绿比（红柱/绿柱）
                "strong_red": strong_red,  # 强红信号（绿转红且红绿比≥0.666）
                "white_line": white_line,  # 趋势线白线
                "yellow_line": yellow_line,  # 趋势线黄线
                "today_vol": today_vol, "yesterday_vol": yesterday_vol,
                "vol_ratio": vol_ratio, "max_vol_20": max_vol_20, "min_vol_20": min_vol_20,
                "b1_triggered": b1, "b2_triggered": b2,
            })

        except Exception as e:
            errors.append(f"{code}:{e}")

        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{total} | 已计算: {len(results)}")

    output = {
        "total": total, "success_count": len(results), "error_count": len(errors),
        "data_date": kline_data.get("data_date", "unknown"),
        "stocks": results, "errors": errors[:20],
    }

    output_file = OUTPUT_DIR / "ztx_indicators.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 砖型图指标计算完成: 成功{len(results)} | 错误{len(errors)}")


if __name__ == "__main__":
    main()
