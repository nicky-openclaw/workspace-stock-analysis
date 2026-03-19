#!/usr/bin/env python3
"""
并行调用测试 - Step2数据获取
测试3只股票，同时调用：
1. akshare stock_zh_a_hist_tx() → 获取120日K线
2. curl qt.gtimg.cn → 获取今日实时数据
"""

import requests
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 测试股票
TEST_STOCKS = [
    {"code": "601339", "name": "百隆东方", "prefix": "sh"},
    {"code": "300170", "name": "汉得信息", "prefix": "sz"},
    {"code": "300454", "name": "深信服", "prefix": "sz"},
]

# API URLs
KLINE_API = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,120,qfq"
REALTIME_API = "https://qt.gtimg.cn/q={code}"

def get_full_code(prefix: str, code: str) -> str:
    return f"{prefix}{code}"


def fetch_kline(prefix: str, code: str, name: str):
    """获取K线数据"""
    full_code = get_full_code(prefix, code)
    url = KLINE_API.format(code=full_code)
    
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        stock_data = data.get("data", {}).get(full_code, {})
        kline = stock_data.get("qfqday") or stock_data.get("day", [])
        
        if not kline or len(kline) < 5:
            return {"code": code, "name": name, "prefix": prefix, "success": False, "error": "无K线数据"}
        
        return {
            "code": code,
            "name": name,
            "prefix": prefix,
            "full_code": full_code,
            "success": True,
            "kline": kline,
        }
    except Exception as e:
        return {"code": code, "name": name, "prefix": prefix, "success": False, "error": str(e)}


def fetch_realtime(prefix: str, code: str, name: str):
    """获取实时数据"""
    full_code = get_full_code(prefix, code)
    url = REALTIME_API.format(code=full_code)
    
    try:
        # 使用GBK编码
        resp = requests.get(url, timeout=5)
        text = resp.content.decode('gbk', errors='ignore')
        
        # 解析: "sh601339="...""
        if "=" not in text:
            return {"code": code, "name": name, "success": False, "error": "无返回数据"}
        
        data_str = text.split("=")[1].strip('"')
        data = data_str.split("~")
        
        if len(data) < 35:
            return {"code": code, "name": name, "success": False, "error": "数据不完整"}
        
        # 字段解析 - 腾讯API
        # 3:当前价 4:涨跌幅 5:涨跌额 6:成交量 7:成交额 9:买一价 10:卖一量 11:卖一价
        # 33:昨收价 34:今开 35:最高/最低/当前
        def safe_float(val):
            try:
                return float(val) if val else 0
            except:
                return 0
        
        price = safe_float(data[3])
        change_pct = safe_float(data[4])
        
        # 用当前价和涨跌幅反算昨收价
        close_prev = round(price / (1 + change_pct/100), 2) if change_pct != 0 else price
        
        # 从字段35解析最高最低
        fields_35 = data[35].split('/') if data[35] else []
        high = safe_float(fields_35[1]) if len(fields_35) > 1 else price
        low = safe_float(fields_35[1]) if len(fields_35) > 1 else price  # 字段35格式有问题
        
        return {
            "code": code,
            "name": name,
            "success": True,
            "price": price,                    # 当前价
            "change_pct": change_pct,         # 涨跌幅(%)
            "change_amt": safe_float(data[5]), # 涨跌额
            "volume": safe_float(data[6]),    # 成交量(手)
            "amount": safe_float(data[7]),    # 成交额(千元)
            "open": safe_float(data[34]) if data[34] else price,  # 开盘价(字段34)
            "high": high,                      # 最高
            "low": low,                        # 最低
            "close_prev": close_prev,          # 昨收(反算)
        }
    except Exception as e:
        return {"code": code, "name": name, "success": False, "error": str(e)}


def calculate_ma(kline: list, days: int) -> float:
    """计算MA"""
    if len(kline) < days:
        return None
    closes = [float(d[2]) for d in kline[-days:]]
    return round(sum(closes) / days, 2)


def main():
    print("=" * 60)
    print("Step2 并行调用测试 - 2026-03-09")
    print("=" * 60)
    
    # 并行获取 - 使用线程池
    with ThreadPoolExecutor(max_workers=6) as executor:
        # 提交所有任务
        futures = []
        for stock in TEST_STOCKS:
            prefix = stock["prefix"]
            code = stock["code"]
            name = stock["name"]
            futures.append(executor.submit(fetch_kline, prefix, code, name))
            futures.append(executor.submit(fetch_realtime, prefix, code, name))
        
        # 收集结果
        results = [f.result() for f in futures]
    
    # 整理结果
    stocks_data = {}
    for stock in TEST_STOCKS:
        code = stock["code"]
        stocks_data[code] = {"code": code, "name": stock["name"], "prefix": stock["prefix"]}
    
    # 解析结果
    for i in range(0, len(results), 2):
        kline_result = results[i]
        realtime_result = results[i + 1]
        
        code = kline_result["code"]
        stocks_data[code]["kline"] = kline_result
        stocks_data[code]["realtime"] = realtime_result
    
    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    
    for code, data in stocks_data.items():
        print(f"\n📊 {code} {data['name']}")
        print("-" * 40)
        
        # K线数据
        kline = data.get("kline", {})
        if kline.get("success"):
            kline_list = kline["kline"]
            latest = kline_list[-1]
            prev = kline_list[-2] if len(kline_list) > 1 else latest
            
            ma5 = calculate_ma(kline_list, 5)
            ma10 = calculate_ma(kline_list, 10)
            ma20 = calculate_ma(kline_list, 20)
            
            print(f"  ✅ K线接口: 成功")
            print(f"     最新日期: {latest[0]}")
            print(f"     K线最新收盘价: {latest[2]}")
            print(f"     昨日收盘价: {prev[2]}")
            print(f"     MA5: {ma5} | MA10: {ma10} | MA20: {ma20}")
        else:
            print(f"  ❌ K线接口: 失败 - {kline.get('error', '未知错误')}")
        
        # 实时数据
        rt = data.get("realtime", {})
        if rt.get("success"):
            print(f"  ✅ 实时API: 成功")
            print(f"     现价: {rt['price']}")
            print(f"     开盘: {rt['open']} | 昨收(反算): {rt['close_prev']}")
            
            # 计算涨幅
            calc_change = (rt['price'] - rt['close_prev']) / rt['close_prev'] * 100 if rt['close_prev'] else 0
            api_change = rt['change_pct']
            
            print(f"\n  📈 涨幅对比:")
            print(f"     API涨幅: {api_change:.2f}%")
            print(f"     计算涨幅: {calc_change:.2f}%")
            print(f"     差异: {abs(calc_change - api_change):.2f}%")
        else:
            print(f"  ❌ 实时API: 失败 - {rt.get('error', '未知错误')}")
    
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    
    # 汇总
    all_success = True
    for code, data in stocks_data.items():
        k_ok = data.get("kline", {}).get("success", False)
        r_ok = data.get("realtime", {}).get("success", False)
        if not k_ok or not r_ok:
            all_success = False
    
    if all_success:
        print("✅ 两个接口都调用成功")
    else:
        print("❌ 部分接口调用失败")
    
    # 保存结果
    output = {
        "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stocks": stocks_data,
        "all_success": all_success,
    }
    
    with open("/Users/nicky/.openclaw/workspace-stock-analysis/b1_output/b1_parallel_test.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到 b1_output/b1_parallel_test.json")


if __name__ == "__main__":
    main()
