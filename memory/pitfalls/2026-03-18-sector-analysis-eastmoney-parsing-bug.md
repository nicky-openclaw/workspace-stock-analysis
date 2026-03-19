# Pitfall: 板块分析脚本 sector_analysis_v4.py eastmoney API 解析失败

**日期**: 2026-03-18
**现象**: 选股报告中板块效应分析全部显示"待获取"，sector_analysis.json 中数据为空
**影响**: 选股报告缺失关键板块效应维度

## 根因

`sector_analysis_v4.py` 中 `get_sector_data_eastmoney()` 函数有解析 bug：

1. 脚本先用 eastmoney API 查询"XXX所属行业板块..."，期望从返回的 table 字典中提取 industry 字段
2. 但 API 实际返回的行业名称在 `entityTagDTO.fullName` 字段，而非 table 字典里
3. 因此 `industry` 提取永远失败 → `sector_cache` 永远为空
4. 脚本认为"已有行业数据"，跳过 eastmoney 板块查询，进入 agent-browser 补齐逻辑
5. agent-browser 浏览器加载空白页面失败 → 最终板块数据全空

**关键发现**: API 本身是正常工作的（curl 直接测试返回完整数据），问题在于解析代码。

## 修复方案

方案A（正确解析）: 修复 `get_sector_data_eastmoney()`，从 `entityTagDTO.fullName` 提取行业名

方案B（稳定可靠）: 从股票名称硬编码行业映射（东方财富行业分类标准）

## 预防措施

1. **选股报告生成后**，必须验证 `sector_analysis.json` 中 `sector_change_pct` 不为空
2. 如果为空，立即手动补全（参考 `scripts/sector_analysis_v4_fix.py` 的正确解析逻辑）
3. 手动补全时用 curl 直接测试 API，用 `entityTagDTO.fullName` 获取行业名

## 正确解析逻辑（2026-03-18 验证通过）

```python
# 查询行业归属（行业在 entityTagDTO.fullName）
d = json.loads(resp.read())
tables = d.get('data',{}).get('data',{}).get('searchDataResultDTO',{}).get('dataTableDTOList',[])
if tables:
    entity = tables[0].get('entityTagDTO', {})
    industry = entity.get('fullName', '')  # 正确！不是 table 字典里

# 查询板块数据（数据在 table.f3 和 table.f62）
tables = d.get('data',{}).get('data',{}).get('searchDataResultDTO',{}).get('dataTableDTOList',[])
t = tables[0]
table = t.get('table', {})
change = table.get('f3', [None])[0]   # 涨跌幅
mainflow = table.get('f62', [None])[0] # 主力净额
```

## 行业映射参考（东方财富标准）

| 股票 | 行业名称 |
|:----:|:----:|
| 600513 联环药业 | 医药生物 |
| 300571 平治信息 | 通信设备 |
| 605058 澳弘电子 | 元件 |
| 301128 强瑞技术 | 专用设备 |
| 603088 宁波精达 | 通用设备 |
| 300317 珈伟新能 | 光伏设备 |
| 605162 新中港 | 电力 |
| 300900 广联航空 | 航空装备 |
| 301399 英特科技 | 仪器仪表 |
| 688307 中润光学 | 光学光电子 |
