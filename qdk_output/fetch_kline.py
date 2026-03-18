import akshare as ak
import json
import time
from datetime import datetime

# 股票列表（代码, 名称）
stocks = [
    ("sh688316", "青云科技-U"),
    ("sh688229", "博睿数据"),
    ("sh688158", "优刻得-W"),
    ("sh603138", "海量数据"),
    ("sh601339", "百隆东方"),
    ("sh600851", "海欣股份"),
    ("sz301606", "绿联科技"),
    ("sz301396", "宏景科技"),
    ("sz300846", "首都在线"),
    ("sz300571", "平治信息"),
    ("sz300369", "绿盟科技"),
    ("sz300352", "北信源"),
    ("sz300166", "东方国信"),
    ("sz300113", "顺网科技"),
    ("sz300017", "网宿科技"),
    ("sz002930", "宏川智慧"),
    ("sz002730", "电光科技"),
    ("sz002229", "鸿博股份"),
    ("sz000973", "佛塑科技"),
    ("sh688207", "格灵深瞳"),
    ("sh688052", "纳芯微"),
    ("sh688023", "安恒信息"),
    ("sh603876", "鼎胜新材"),
    ("sh600845", "宝信软件"),
    ("sz301358", "湖南裕能"),
    ("sz300608", "思特奇"),
    ("sz300226", "上海钢联"),
    ("sz300170", "汉得信息"),
    ("sz002812", "恩捷股份"),
    ("sz002575", "群兴玩具"),
    ("sz002151", "北斗星通"),
    ("sz001203", "大中矿业"),
    ("sz000066", "中国长城"),
    ("bj920670", "数字人"),
    ("sh688599", "天合光能"),
    ("sh688327", "云从科技-UW"),
    ("sz301292", "海科新源"),
    ("sz300921", "南凌科技"),
    ("sz300738", "奥飞数据"),
    ("sz300624", "万兴科技"),
    ("sz300454", "深信服"),
    ("sh603881", "数据港"),
    ("sh601360", "三六零"),
    ("sz300383", "光环新网"),
]

results = {}
errors = []

def convert_to_serializable(obj):
    """Convert pandas/numpy types to JSON serializable types"""
    if hasattr(obj, 'item'):  # numpy types
        return obj.item()
    elif hasattr(obj, 'isoformat'):  # date/datetime
        return obj.isoformat()
    return obj

def process_dataframe(df):
    """Convert DataFrame to JSON-serializable dict"""
    records = []
    for row in df.to_dict('records'):
        clean_row = {}
        for k, v in row.items():
            clean_row[str(k)] = convert_to_serializable(v)
        records.append(clean_row)
    return records

print(f"开始获取 {len(stocks)} 只股票K线数据...")
print(f"日期范围: 20250101 - 20250309")

for i, (code, name) in enumerate(stocks):
    try:
        print(f"[{i+1}/{len(stocks)}] 获取 {code} {name}...", end=" ", flush=True)
        df = ak.stock_zh_a_hist_tx(
            symbol=code, 
            start_date='20250101', 
            end_date='20250309',
            adjust='qfq'
        )
        results[code] = {
            "name": name,
            "data": process_dataframe(df)
        }
        print(f"✓ 获取{len(df)}条")
        time.sleep(0.5)
    except Exception as e:
        print(f"✗ 错误: {e}")
        errors.append({"code": code, "name": name, "error": str(e)})
        continue

# 保存结果
output = {
    "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total": len(stocks),
    "success": len(results),
    "errors": errors,
    "stocks": results
}

with open('qdk_kline.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n=== 完成 ===")
print(f"成功: {len(results)}/{len(stocks)}")
if errors:
    print(f"失败股票: {[e['code'] for e in errors]}")
print(f"数据已保存到 qdk_kline.json")
