# 通达信砖型图指标
# 来源: 用户提供
# 日期: 2026-02-21

# ==================== 通达信公式 ====================
# VAR1A:=(HHV(HIGH,4)-CLOSE)/(HHV(HIGH,4)-LLV(LOW,4))*100-90;
# VAR2A:=SMA(VAR1A,4,1)+100;
# VAR3A:=(CLOSE-LLV(LOW,4))/(HHV(HIGH,4)-LLV(LOW,4))*100;
# VAR4A:=SMA(VAR3A,6,1);
# VAR5A:=SMA(VAR4A,6,1)+100;
# VAR6A:=VAR5A-VAR2A;
# 砖型图:=IF(VAR6A>4,VAR6A-4,0),COLORRED;
# STICKLINE(REF(砖型图,1)<砖型图 AND REF(砖型图,1)<=3*砖型图-2*REF(砖型图,2) AND REF(砖型图,1)<REF(砖型图,2),砖型图,REF(砖型图,1),3,0),COLORRED;
# STICKLINE(REF(砖型图,1)<砖型图 AND REF(砖型图,1)>3*砖型图-2*REF(砖型图,2) OR REF(砖型图,1)>REF(砖型图,2),砖型图,REF(砖型图,1),3,1),COLORRED;
# STICKLINE(REF(砖型图,1)>砖型图,砖型图,REF(砖型图,1),3,0),COLOR00FF00;

# ==================== 指标逻辑 ====================
# 砖型图是一个趋势动量指标
# - 当VAR6A>4时，显示VAR6A-4，否则为0
# - 红柱表示上涨趋势
# - 绿柱表示下跌趋势

# ==================== Python实现 ====================
import numpy as np
import pandas as pd

def calc_zhuantxing(df, period=4):
    """
    砖型图指标计算
    df需要包含: HIGH, LOW, CLOSE
    """
    high = df['HIGH']
    low = df['LOW']
    close = df['CLOSE']
    
    # VAR1A:=(HHV(HIGH,4)-CLOSE)/(HHV(HIGH,4)-LLV(LOW,4))*100-90
    hhv_high = high.rolling(window=period).max()
    llv_low = low.rolling(window=period).min()
    var1a = (hhv_high - close) / (hhv_high - llv_low) * 100 - 90
    
    # VAR2A:=SMA(VAR1A,4,1)+100
    var2a = var1a.rolling(window=period).mean() + 100
    
    # VAR3A:=(CLOSE-LLV(LOW,4))/(HHV(HIGH,4)-LLV(LOW,4))*100
    var3a = (close - llv_low) / (hhv_high - llv_low) * 100
    
    # VAR4A:=SMA(VAR3A,6,1)
    var4a = var3a.rolling(window=6).mean()
    
    # VAR5A:=SMA(VAR4A,6,1)+100
    var5a = var4a.rolling(window=6).mean() + 100
    
    # VAR6A:=VAR5A-VAR2A
    var6a = var5a - var2a
    
    # 砖型图:=IF(VAR6A>4,VAR6A-4,0)
    zhuanxing = np.where(var6a > 4, var6a - 4, 0)
    
    return pd.Series(zhuanxing, index=df.index)


def check_zhuanxing_signal(df):
    """
    砖型图信号检测
    返回: 1=买入信号, -1=卖出信号, 0=无信号
    """
    zz = calc_zhuantxing(df)
    
    # 计算前一根砖型图的值
    zz_prev = zz.shift(1)
    zz_prev2 = zz.shift(2)
    
    # 买入条件: 前一砖型图<当前砖型图 且 前一砖型图<=3*当前砖型图-2*前一砖型图(2) 且 前一砖型图<前一砖型图(2)
    buy_cond = (zz_prev < zz) & (zz_prev <= 3*zz - 2*zz_prev2) & (zz_prev < zz_prev2)
    
    # 卖出条件: 前一砖型图>当前砖型图
    sell_cond = zz_prev > zz
    
    signal = np.where(buy_cond, 1, np.where(sell_cond, -1, 0))
    
    return pd.Series(signal, index=df.index)
