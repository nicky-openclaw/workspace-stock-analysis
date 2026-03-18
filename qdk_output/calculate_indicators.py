import json

# 加载K线数据
with open('qdk_kline.json', 'r', encoding='utf-8') as f:
    kline_data = json.load(f)

stocks = kline_data['stocks']

def calculate_indicators(code, name, data):
    """计算技术指标"""
    if not data or len(data) < 30:
        return None
    
    # 按日期排序（从旧到新）
    sorted_data = sorted(data, key=lambda x: x['date'])
    
    # 获取最新数据
    latest = sorted_data[-1]
    yesterday = sorted_data[-2] if len(sorted_data) >= 2 else None
    
    # 提取关键价格（字段是英文）
    close_prices = [float(d['close']) for d in sorted_data]
    volumes = [float(d.get('amount', 0)) for d in sorted_data]  # amount=成交额，成交量需要另外获取
    # 腾讯API返回的是成交额，我们估算成交量
    opens = [float(d['open']) for d in sorted_data]
    highs = [float(d['high']) for d in sorted_data]
    lows = [float(d['low']) for d in sorted_data]
    
    # 腾讯API没有成交量字段，用成交额/价格估算
    # 这里用amount作为近似成交量
    volumes = [float(d['amount']) for d in sorted_data]
    
    # 计算MA均线
    def ma(n, prices):
        if len(prices) < n:
            return None
        return sum(prices[-n:]) / n
    
    ma5 = ma(5, close_prices)
    ma10 = ma(10, close_prices)
    ma20 = ma(20, close_prices)
    ma30 = ma(30, close_prices) if len(close_prices) >= 30 else None
    
    # 多头排列判断（MA5 > MA10 > MA20 > MA30）
    多头排列 = all([ma5, ma10, ma20, ma30]) and ma5 > ma10 > ma20 > ma30
    
    # 计算量比和成交量变化
    latest_vol = volumes[-1]
    avg_vol_5 = sum(volumes[-6:-1]) / 5 if len(volumes) >= 6 else sum(volumes[:-1]) / max(len(volumes)-1, 1)
    量比 = latest_vol / avg_vol_5 if avg_vol_5 > 0 else 0
    成交量变化 = (latest_vol - avg_vol_5) / avg_vol_5 * 100 if avg_vol_5 > 0 else 0
    
    # 计算涨幅（用K线）
    if yesterday:
        收盘价 = float(latest['close'])
        昨日收盘 = float(yesterday['close'])
        涨幅 = (收盘价 - 昨日收盘) / 昨日收盘 * 100
    else:
        涨幅 = 0
    
    # 判断是否涨停
    涨停 = 涨幅 >= 9.9  # 近似涨停
    
    # 计算大阳线（涨幅>7%）
    大阳线 = 涨幅 > 7
    
    # 计算量能（倍量=2x，1.5-2x）
    倍量 = latest_vol >= 2 * avg_vol_5
    温和放量 = 1.5 <= (latest_vol / avg_vol_5) < 2
    
    # 启动K判断：需要最近3天有启动信号
    def check_startup_k():
        """检查最近是否有启动K信号"""
        if len(sorted_data) < 5:
            return {"has": False, "reason": "数据不足"}
        
        # 检查最近3天
        for i in range(-3, 0):
            day_vol = volumes[i]
            day_close = close_prices[i]
            day_open = opens[i]
            day_change = (day_close - day_open) / day_open * 100
            
            prev_vol = volumes[i-1] if i > -len(volumes) else volumes[-1]
            
            # 倍量启动
            if day_vol >= 2 * prev_vol:
                return {"has": True, "type": "倍量", "day": i}
            # 1.5-2x温和放量
            if 1.5 <= day_vol / prev_vol < 2 and day_change > 5:
                return {"has": True, "type": "温和放量", "day": i}
            # 大阳线
            if day_change > 7:
                return {"has": True, "type": "大阳线", "day": i}
        
        return {"has": False, "reason": "无启动信号"}
    
    启动K = check_startup_k()
    
    # 白线/黄线位置判断（简化：用MA5=白线，MA10=黄线）
    白线 = ma5
    黄线 = ma10
    
    if 白线 and 黄线:
        价格 = float(latest['close'])
        # 在黄线附近（±3%）
        黄线附近 = abs(价格 - 黄线) / 黄线 < 0.03
        # 在白线附近（±3%）
        白线附近 = abs(价格 - 白线) / 白线 < 0.03
        # 站回白线（价格 > 白线 > 黄线）
        站回白线 = 价格 > 白线 > 黄线
    else:
        黄线附近 = False
        白线附近 = False
        站回白线 = False
    
    # 硬淘汰判断
    白线大于黄线 = (白线 and 黄线 and 白线 > 黄线) or (not 白线 and not 黄线)  # 默认满足
    放量下跌 = 成交量变化 > 10 and 涨幅 < -2
    
    # 硬淘汰
    硬淘汰 = (not 白线大于黄线) or 放量下跌
    
    return {
        "code": code,
        "name": name,
        "收盘价": float(latest['close']),
        "涨幅": 涨幅,
        "涨停": 涨停,
        "大阳线": 大阳线,
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20,
        "ma30": ma30,
        "多头排列": 多头排列,
        "量比": round(量比, 2),
        "成交量变化": round(成交量变化, 2),
        "倍量": 倍量,
        "温和放量": 温和放量,
        "启动K": 启动K,
        "白线": 白线,
        "黄线": 黄线,
        "黄线附近": 黄线附近,
        "白线附近": 白线附近,
        "站回白线": 站回白线,
        "硬淘汰": 硬淘汰,
    }

# 计算所有股票指标
indicators = {}
for code, stock_data in stocks.items():
    result = calculate_indicators(code, stock_data['name'], stock_data['data'])
    if result:
        indicators[code] = result

# 保存结果
with open('qdk_indicators.json', 'w', encoding='utf-8') as f:
    json.dump(indicators, f, ensure_ascii=False, indent=2)

print(f"=== 技术指标计算完成 ===")
print(f"有效股票: {len(indicators)}")
print(f"硬淘汰股票: {sum(1 for i in indicators.values() if i['硬淘汰'])}")
print(f"多头排列: {sum(1 for i in indicators.values() if i['多头排列'])}")
print(f"有启动K信号: {sum(1 for i in indicators.values() if i['启动K']['has'])}")
print(f"涨停: {sum(1 for i in indicators.values() if i['涨停'])}")
print(f"数据已保存到 qdk_indicators.json")
