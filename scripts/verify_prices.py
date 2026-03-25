#!/usr/bin/env python3
"""获取股票今日收盘价用于复盘验证"""
import requests
import json
from datetime import datetime

stocks = [
    # QDK启动K Top5
    ('603165.SH', '荣晟环保', 14.35, 10.0),
    ('605099.SH', '共创草坪', 42.19, 10.0),
    ('300827.SH', '上能电气', 38.56, 20.01),
    ('688680.SH', '海优新材', 53.34, 13.56),
    ('301268.SZ', '铭利达', 23.08, 10.13),
    ('603381.SH', '永臻股份', 26.75, 10.02),
    ('301179.SZ', '泽宇智能', 21.9, 4.46),
    # ZTX涨停Top10
    ('000509.SZ', '华塑控股', 3.84, 9.93),
    ('603538.SH', '美诺华', 23.48, 10.0),
    ('605117.SH', '德业股份', 121.26, 9.91),
    ('002256.SZ', '兆新股份', 3.91, 10.05),
    ('002150.SZ', '正泰电器', 29.94, 10.0),
    ('600617.SH', '国新能源', 3.43, 9.92),
    ('002309.SZ', '中利集团', 3.46, 10.12),
    # ZTX非涨停Top10
    ('300854.SZ', '中兰环保', 24.4, 8.16),
    ('688307.SH', '中润光学', 55.84, 9.02),
    ('301365.SZ', '矩阵股份', 26.14, 7.0),
    ('688032.SH', '禾迈股份', 115.18, 9.99),
    ('000968.SZ', '蓝焰控股', 9.42, 4.99),
    ('688390.SH', '固德威', 94.4, 5.08),
    ('605162.SH', '新中港', 9.83, 5.14),
    ('300502.SZ', '新易盛', 397.75, 8.32),
    ('300693.SZ', '盛弘股份', 45.47, 5.54),
    ('301268.SZ', '铭利达', 23.08, 10.13),
]

codes = [s[0] for s in stocks]
code_str = ','.join(codes)

print(f"查询股票数量: {len(codes)}")
print(f"查询代码: {code_str}")

try:
    url = "https://q.verver.com.cn/api/batch/kline"
    headers = {"Content-Type": "application/json"}
    data = {"codes": code_str, "period": "daily", "count": 2}
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    result = resp.json()
    print(json.dumps(result, ensure_ascii=False, indent=2)[:3000])
except Exception as e:
    print(f"Error: {e}")
