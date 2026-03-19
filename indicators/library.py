# 股票指标库
# 基于通达信公式翻译为Python
# 作者: 小蓝

import pandas as pd
import numpy as np

def calc_kdj(df, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    low_n = df['最低'].rolling(window=n, min_periods=1).min()
    high_n = df['最高'].rolling(window=n, min_periods=1).max()
    
    rsv = (df['收盘'] - low_n) / (high_n - low_n) * 100
    rsv = rsv.fillna(50)
    
    k = pd.Series(50.0, index=df.index)
    d = pd.Series(50.0, index=df.index)
    
    for i in range(1, len(df)):
        k.iloc[i] = (2/3) * k.iloc[i-1] + (1/3) * rsv.iloc[i]
        d.iloc[i] = (2/3) * d.iloc[i-1] + (1/3) * k.iloc[i]
    
    j = m1 * k - m2 * d
    return k, d, j

def calc_rsi(df, period=3):
    """计算RSI指标"""
    delta = df['收盘'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)
    return rsi

def calc_ma(df, period):
    """计算移动平均线"""
    return df['收盘'].rolling(window=period).mean()

def calc_ema(df, period):
    """计算指数移动平均"""
    return df['收盘'].ewm(span=period, adjust=False).mean()

# ============ B2 选股指标 ============
def check_b2(df, yesterday_df):
    """
    B2选股条件:
    - 昨日J值 < 0
    - 今日涨幅 > 3.95%
    - 今日成交量 > 昨日成交量
    - 今日J值 < 55
    """
    k, d, j = calc_kdj(df)
    
    if len(df) < 2 or len(yesterday_df) < 1:
        return False, {}
    
    today = df.iloc[-1]
    yesterday = yesterday_df.iloc[-1]
    
    j_today = j.iloc[-1]
    j_yesterday = j.iloc[-2] if len(j) > 1 else 50
    
    change_pct = (today['收盘'] - yesterday['收盘']) / yesterday['收盘'] * 100
    
    cond1 = j_yesterday < 0
    cond2 = change_pct > 3.95
    cond3 = today['成交量'] > yesterday['成交量']
    cond4 = j_today < 55
    
    result = cond1 and cond2 and cond3 and cond4
    
    return result, {
        '涨幅': change_pct,
        '昨日J': j_yesterday,
        '今日J': j_today,
        'K': k.iloc[-1],
        'D': d.iloc[-1]
    }

# ============ 动能指标 ============
def calc_dongnan(df):
    """
    JRX动能指标
    - J动能: KDJ.J的差值
    - R动能: RSI3日的差值
    - 黄柱: (J动能+R动能)/2 * 影线系数 * 倍量系数
    - X动能: 洗盘判定
    """
    k, d, j = calc_kdj(df)
    rsi = calc_rsi(df, 3)
    
    j_dong = j - j.shift(1)
    rsi_dong = rsi - rsi.shift(1)
    
    # 成交量系数
    vol_yesterday = df['成交量'].shift(1)
    vol_ratio = df['成交量'] / vol_yesterday
    vol_coef = np.where(
        df['成交量'] < vol_yesterday * 0.99,
        (1 - 5 * (vol_yesterday - df['成交量']) / vol_yesterday) * 0.8,
        1
    )
    
    # 倍量系数
    bei_ratio = np.where(vol_ratio >= 4, 1.4, 0.1 * vol_ratio + 1)
    bei_coef = np.where(
        (df['收盘'] > df['开盘']) & 
        (df['收盘'] > df['收盘'].shift(1)) & 
        (df['成交量'] > df['成交量'].shift(1) * 1.8),
        bei_ratio,
        1
    )
    
    # 影线系数
    open_prev = df['开盘'].shift(1).fillna(df['收盘'])
    h = df['最高']
    c = df['收盘']
    o = df['开盘']
    min_o_prev = np.minimum(o, open_prev)
    
    yingxian_coef = np.where(
        (c > df['收盘'].shift(1)) & (c > o),
        (0.75 - (h - c) / (h - min_o_prev + 0.001)) * 1.3,
        1
    )
    
    # 黄柱
    yellow = (j_dong + rsi_dong) / 2 * yingxian_coef * bei_coef
    
    # X动能
    x_dong = np.where(
        (c > o) & 
        (c > df['收盘'].shift(1)) &
        ((j_dong + rsi_dong) > (j_dong.shift(1) + rsi_dong.shift(1))),
        ((j_dong + rsi_dong) - (j_dong.shift(1) + rsi_dong.shift(1))) / 2 * 
        yingxian_coef * vol_coef * bei_coef,
        0
    )
    
    return {
        'J动能': j_dong,
        'R动能': rsi_dong,
        '黄柱': yellow,
        'X动能': x_dong
    }

# ============ 单针下30 指标 ============
def calc_danzhen(df):
    """
    单针下30指标
    - 短期: 3日周期
    - 中期: 10日周期
    - 中长期: 21日周期
    - 长期: 31日周期
    """
    短期 = 100 * (df['收盘'] - df['最低'].rolling(3).min()) / (df['最高'].rolling(3).max() - df['最低'].rolling(3).min() + 0.001)
    中期 = 100 * (df['收盘'] - df['最低'].rolling(10).min()) / (df['最高'].rolling(10).max() - df['最低'].rolling(10).min() + 0.001)
    中长期 = 100 * (df['收盘'] - df['最低'].rolling(21).min()) / (df['最高'].rolling(21).max() - df['最低'].rolling(21).min() + 0.001)
    长期 = 100 * (df['收盘'] - df['最低'].rolling(31).min()) / (df['最高'].rolling(31).max() - df['最低'].rolling(31).min() + 0.001)
    
    # 买入信号
    四线归零买 = (短期 <= 6) & (中期 <= 6) & (中长期 <= 6) & (长期 <= 6)
    白线下20买 = (短期 <= 20) & (长期 >= 70)
    白穿红线买 = (短期 > 长期) & (长期.shift(1) < 20)
    白穿黄线买 = (短期 > 中期) & (中期.shift(1) < 30)
    
    return {
        '短期': 短期,
        '中期': 中期,
        '中长期': 中长期,
        '长期': 长期,
        '四线归零买': 四线归零买,
        '白线下20买': 白线下20买,
        '白穿红线买': 白穿红线买,
        '白穿黄线买': 白穿黄线买
    }

# ============ 暴力动能选股 ============
def check_bldong(df):
    """
    暴力动能选股条件:
    1. 强动能: V>REF(V,1) AND (黄柱>=45 OR X动能>60) AND MA(C,60)>REF(MA(C,60),1) AND MA(C,20)>=MA(C,60)
    2. 暴力动能: 倍量 AND (黄柱>40 OR X动能>55)
    3. 爆量动能: 超倍量 AND (黄柱>20 OR X动能>30)
    4. 莫名其妙: 巨量 OR (EXIST(巨量,25) AND KDJ.J<20 AND (不是大绿棒 OR 大绿棒离得远))
    """
    if len(df) < 30:
        return False, {}
    
    dong = calc_dongnan(df)
    
    # 均线
    ma20 = calc_ma(df, 20)
    ma60 = calc_ma(df, 60)
    
    # 倍量条件
    vol_ratio = df['成交量'] / df['成交量'].shift(1)
    倍量 = (vol_ratio > 1.8) & (df['收盘'] > df['收盘'].shift(1)) & ((df['收盘'] - df['收盘'].shift(1)) / df['收盘'].shift(1) * 100 > 3.5) & (df['成交量'] > df['成交量'].rolling(5).mean() * 1.6)
    超倍量 = vol_ratio > 4
    巨量 = (vol_ratio > 8) & (df['收盘'] > df['开盘'])
    
    # 大绿棒判断
    vol_40max_day = df['成交量'].rolling(40).apply(lambda x: x.argmax(), raw=True)
    不是大绿棒 = df['收盘'].shift(1) >= df['收盘'].shift(2)
    大绿棒离得远 = (vol_40max_day >= 15) & (~不是大绿棒)
    
    # 各条件
    强动能 = (df['成交量'] > df['成交量'].shift(1)) & ((dong['黄柱'] >= 45) | (dong['X动能'] > 60)) & (ma60 > ma60.shift(1)) & (ma20 >= ma60)
    暴力动能 = 倍量 & ((dong['黄柱'] > 40) | (dong['X动能'] > 55))
    爆量动能 = 超倍量 & ((dong['黄柱'] > 20) | (dong['X动能'] > 30))
    
    k, d, j = calc_kdj(df)
    巨量历史 = df['成交量'].rolling(25).apply(lambda x: (x / x.max() if x.max() > 0 else 0) > 8, raw=False)
    莫名其妙 = 巨量 | (巨量历史 & (j < 20) & (不是大绿棒 | 大绿棒离得远))
    
    result = 强动能.iloc[-1] or 暴力动能.iloc[-1] or 爆量动能.iloc[-1] or 莫名其妙.iloc[-1]
    
    return result, {
        '强动能': 强动能.iloc[-1],
        '暴力动能': 暴力动能.iloc[-1],
        '爆量动能': 爆量动能.iloc[-1],
        '莫名其妙': 莫名其妙.iloc[-1],
        '黄柱': dong['黄柱'].iloc[-1],
        'X动能': dong['X动能'].iloc[-1]
    }

# ============ 趋势线指标 ============
def calc_qushixian(df):
    """
    趋势线指标
    - 知行短期趋势线: EMA(EMA(C,10),10)
    - 知行多空线: (MA(C,M1)+MA(C,M2)+MA(C,M3)+MA(C,M4))/4
    """
    短期趋势线 = calc_ema(calc_ema(df, 10), 10)
    
    # 多空线 (默认参数)
    M1, M2, M3, M4 = 5, 10, 20, 60
    多空线 = (calc_ma(df, M1) + calc_ma(df, M2) + calc_ma(df, M3) + calc_ma(df, M4)) / 4
    
    return {
        '短期趋势线': 短期趋势线,
        '多空线': 多空线,
        '多头': 短期趋势线 > 多空线,
        '空头': 短期趋势线 < 多空线
    }

# ============ 超级B1指标 (简化版) ============
def check_chaoji_b1(df):
    """
    超级B1选股条件 (简化版):
    - 做上涨趋势: 趋势白线>=大哥黄线
    - 缩量: VOL < 20日最高量 * 0.416
    - KDJ超卖: J < 14
    - RSI超卖: RSI < 23
    - 异动: 近期振幅 >= 15%
    """
    if len(df) < 30:
        return False, {}
    
    k, d, j = calc_kdj(df)
    rsi = calc_rsi(df, 3)
    
    # 均线
    趋势白线 = calc_ema(calc_ema(df, 10), 10)
    大哥黄线 = (calc_ma(df, 14) + calc_ma(df, 28) + calc_ma(df, 57) + calc_ma(df, 114)) / 4
    
    # 缩量
    vol_20max = df['成交量'].rolling(20).max()
    缩量 = df['成交量'] < vol_20max * 0.416
    
    # 短期/长期
    短期 = 100 * (df['收盘'] - df['最低'].rolling(3).min()) / (df['最高'].rolling(3).max() - df['最低'].rolling(3).min() + 0.001)
    长期 = 100 * (df['收盘'] - df['最低'].rolling(21).min()) / (df['最高'].rolling(21).max() - df['最低'].rolling(21).min() + 0.001)
    
    # 振幅
    振幅 = (df['最高'] - df['最低']) / df['最低'] * 100
    近期振幅 = 振幅.rolling(12).max()
    
    # 上涨趋势
    做上涨趋势 = 趋势白线 >= 大哥黄线
    
    # 异动
    近期异动 = 近期振幅 >= 15
    
    # B1买入条件
    B1信号 = 做上涨趋势 & (j < 14) & (rsi < 23) & 缩量 & 近期异动
    
    result = B1信号.iloc[-1]
    
    return result, {
        'J': j.iloc[-1],
        'RSI': rsi.iloc[-1],
        '趋势白线': 趋势白线.iloc[-1],
        '大哥黄线': 大哥黄线.iloc[-1],
        '缩量': 缩量.iloc[-1],
        '近期异动': 近期异动.iloc[-1],
        '做上涨趋势': 做上涨趋势.iloc[-1]
    }

# ============ 砖型图指标 ============
def calc_zhuantxing(df, period=4):
    """
    砖型图指标计算
    基于通达信公式翻译
    VAR1A:=(HHV(HIGH,4)-CLOSE)/(HHV(HIGH,4)-LLV(LOW,4))*100-90
    VAR2A:=SMA(VAR1A,4,1)+100
    VAR3A:=(CLOSE-LLV(LOW,4))/(HHV(HIGH,4)-LLV(LOW,4))*100
    VAR4A:=SMA(VAR3A,6,1)
    VAR5A:=SMA(VAR4A,6,1)+100
    VAR6A:=VAR5A-VAR2A
    砖型图:=IF(VAR6A>4,VAR6A-4,0)
    """
    high = df['最高']
    low = df['最低']
    close = df['收盘']
    
    # HHV(HIGH,4) 和 LLV(LOW,4)
    hhv_high = high.rolling(window=period, min_periods=1).max()
    llv_low = low.rolling(window=period, min_periods=1).min()
    
    # VAR1A
    var1a = (hhv_high - close) / (hhv_high - llv_low) * 100 - 90
    
    # VAR2A: SMA(VAR1A,4,1)+100
    var2a = var1a.rolling(window=period, min_periods=1).mean() + 100
    
    # VAR3A
    var3a = (close - llv_low) / (hhv_high - llv_low) * 100
    
    # VAR4A: SMA(VAR3A,6,1)
    var4a = var3a.rolling(window=6, min_periods=1).mean()
    
    # VAR5A: SMA(VAR4A,6,1)+100
    var5a = var4a.rolling(window=6, min_periods=1).mean() + 100
    
    # VAR6A
    var6a = var5a - var2a
    
    # 砖型图
    zhuanxing = np.where(var6a > 4, var6a - 4, 0)
    
    return pd.Series(zhuanxing, index=df.index), var6a

def check_zhuantxing_buy(df, yesterday_df):
    """
    砖型图短期买入信号
    
    买入条件:
    - 砖型图从低位上涨
    - 红柱连续放大
    - 适用于短线/超短线
    
    返回: (bool, dict)
    """
    if len(df) < 2 or len(yesterday_df) < 1:
        return False, {}
    
    # 计算砖型图
    zz_today, _ = calc_zhuantxing(df)
    zz_yesterday = zz_today.shift(1)
    zz_yesterday2 = zz_today.shift(2)
    
    # 合并昨日数据计算
    combined = pd.concat([yesterday_df, df])
    zz_combined, _ = calc_zhuantxing(combined)
    zz_combined_prev = zz_combined.shift(1)
    zz_combined_prev2 = zz_combined.shift(2)
    
    # 当前砖型图值
    zz = zz_combined.iloc[-1]
    zz_prev = zz_combined_prev.iloc[-1]
    zz_prev2 = zz_combined_prev2.iloc[-1]
    
    # 买入条件1: 砖型图上升
    cond1 = zz > zz_prev
    
    # 买入条件2: 放量上涨（成交量放大）
    vol_today = df.iloc[-1]['成交量']
    vol_yesterday = yesterday_df.iloc[-1]['成交量']
    cond2 = vol_today > vol_yesterday * 1.2  # 放量20%以上
    
    # 买入条件3: 涨幅适中（2%-8%）
    change_pct = (df.iloc[-1]['收盘'] - yesterday_df.iloc[-1]['收盘']) / yesterday_df.iloc[-1]['收盘'] * 100
    cond3 = 2 < change_pct < 8
    
    # 综合信号
    buy_signal = cond1 and cond2 and cond3
    
    return buy_signal, {
        '砖型图': zz,
        '昨日砖型图': zz_prev,
        '涨幅': change_pct,
        '成交量放大': vol_today / vol_yesterday if vol_yesterday > 0 else 0
    }

def check_zhuantxing_sell(df):
    """
    砖型图卖出信号
    
    卖出条件:
    - 砖型图下降
    - 出现绿柱
    """
    if len(df) < 2:
        return False, {}
    
    zz, _ = calc_zhuantxing(df)
    zz_prev = zz.shift(1)
    
    # 卖出条件: 砖型图下降
    sell_signal = zz.iloc[-1] < zz_prev.iloc[-1]
    
    return sell_signal, {
        '砖型图': zz.iloc[-1],
        '昨日砖型图': zz_prev.iloc[-1]
    }

# ============ 知行多空线指标 ============
def calc_zhixing_duokong(df, m1=14, m2=28, m3=57, m4=114):
    """
    知行多空线
    M1:=14; M2:=28; M3:=57; M4:=114;
    知行多空线:=(MA(CLOSE,M1)+MA(CLOSE,M2)+MA(CLOSE,M3)+MA(CLOSE,M4))/4;
    黄线达标:=CLOSE > 知行多空线;
    """
    ma1 = df['收盘'].rolling(window=m1).mean()
    ma2 = df['收盘'].rolling(window=m2).mean()
    ma3 = df['收盘'].rolling(window=m3).mean()
    ma4 = df['收盘'].rolling(window=m4).mean()
    
    知行多空线 = (ma1 + ma2 + ma3 + ma4) / 4
    黄线达标 = df['收盘'] > 知行多空线
    
    return 知行多空线, 黄线达标


def calc_zhixing反转强度(df):
    """
    反转强度判断
    今天红柱:=砖型图 > REF(砖型图,1);
    昨天绿柱:=REF(砖型图,1) < REF(砖型图,2);
    红柱高度:=砖型图 - REF(砖型图,1);
    绿柱高度:=REF(砖型图,2) - REF(砖型图,1);
    高度达标:=红柱高度 >= 绿柱高度 * 2 / 3;
    """
    zz, _ = calc_zhuantxing(df)
    
    今天红柱 = zz > zz.shift(1)
    昨天绿柱 = (zz.shift(1) < zz.shift(2)) & (zz.shift(1) < 0)
    红柱高度 = zz - zz.shift(1)
    绿柱高度 = zz.shift(2) - zz.shift(1)
    高度达标 = 红柱高度 >= 绿柱高度 * 2 / 3
    
    return 今天红柱, 昨天绿柱, 红柱高度, 绿柱高度, 高度达标


def check_知行短线(df, yesterday_df):
    """
    知行多空线 + 砖型图 短线选股
    
    选股条件:
    1. 知行多空线: 黄线达标 (收盘价 > 知行多空线)
    2. 昨天绿柱
    3. 今天红柱
    4. 高度达标: 红柱高度 >= 绿柱高度 * 2/3
    5. 去ST
    6. 去停牌
    7. 去新股: 上市60天以上
    
    返回: (bool, dict)
    """
    if len(df) < 3:
        return False, {}
    
    # 条件1: 黄线达标
    _, 黄线达标 = calc_zhixing_duokong(df)
    cond1 = 黄线达标.iloc[-1]
    
    # 条件2-4: 反转强度
    今天红柱, 昨天绿柱, 红柱高度, 绿柱高度, 高度达标 = calc_zhixing反转强度(df)
    cond2 = 昨天绿柱.iloc[-1]  # 昨天绿柱
    cond3 = 今天红柱.iloc[-1]   # 今天红柱
    cond4 = 高度达标.iloc[-1]   # 高度达标
    
    # 条件5-7: 过滤条件（需要基本面数据，这里简化处理）
    # 实际使用时需要通过tushare等获取
    cond5 = True  # 去ST
    cond6 = True   # 去停牌
    cond7 = True   # 去新股
    
    # 综合信号
    buy_signal = cond1 and cond2 and cond3 and cond4 and cond5 and cond6 and cond7
    
    return buy_signal, {
        '知行多空线达标': cond1,
        '昨天绿柱': cond2,
        '今天红柱': cond3,
        '高度达标': cond4,
        '砖型图': calc_zhuantxing(df)[0].iloc[-1],
        '红柱高度': 红柱高度.iloc[-1],
        '绿柱高度': 绿柱高度.iloc[-1]
    }
