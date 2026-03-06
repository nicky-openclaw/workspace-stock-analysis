# 选股工具使用说明

## 工具位置
- indicators/library.py - 指标库
- screener.py - 选股工具
- auto_stock_screener.py - 自动选股
- zhuanxing_v2.py - 砖型图检测

## 使用方式
```bash
python3 screener.py
python3 auto_stock_screener.py
```

## 指标列表
| 指标 | 函数 | 功能 |
|------|------|------|
| B2 | check_b2() | J值负+涨幅>3.95%+放量 |
| 暴力动能 | check_bldong() | 强动能选股 |
| 单针下30 | calc_danzhen() | 超跌反弹 |
| 超级B1 | check_chaoji_b1() | 趋势+缩量 |
