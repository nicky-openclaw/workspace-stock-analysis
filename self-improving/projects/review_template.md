# 选股复盘（含大盘分析） - {{DATE}}

---

## 一、大盘分析

### 1.1 指数表现

| 指数 | 收盘 | 涨跌幅 | 成交量 | 成交额 |
|------|------|--------|--------|--------|
| 上证 | {{sh_price}} | {{sh_change}}% | {{sh_vol}}万手 | {{sh_amount}}亿 |
| 深证 | {{sz_price}} | {{sz_change}}% | {{sz_vol}}万手 | {{sz_amount}}亿 |
| 沪深300 | {{hs300_price}} | {{hs300_change}}% | - | {{hs300_amount}}亿 |

**两市合计成交额**：{{total_amount}}亿（vs昨日 {{yesterday_total}}亿，{{volume_compare}}）

### 1.2 市场情绪

- 涨停数量：{{zt_count}}只
- 情绪判断：{{sentiment}}（活跃/中性/冷淡）

### 1.3 板块资金流

| 强势板块 | 主力净流入 | 代表股 |
|---------|-----------|--------|
| {{sector1}} | {{flow1}}亿 | {{stock1}} |
| {{sector2}} | {{flow2}}亿 | {{stock2}} |

| 弱势板块 | 主力净流出 | 风险 |
|---------|-----------|------|
| {{weak_sector1}} | {{weak_flow1}}亿 | {{risk1}} |

### 1.4 大盘特征总结

{{market_characteristics}}

---

## 二、选股结果验证

### 2.1 启动K（执行日期：{{qdk_date}}）

| 排名 | 代码 | 名称 | 评分 | 昨日涨幅 | 今日收盘 | 今日涨幅 | 验证 |
|:----:|:----:|:----:|:----:|:--------:|:--------:|:--------:|:----:|
{{qdk_table}}

**准确率：{{qdk_accuracy}}，平均涨幅：{{qdk_avg_change}}**

### 2.2 砖型图（执行日期：{{ztx_date}}）

| 排名 | 代码 | 名称 | 评分 | 昨日涨幅 | 今日收盘 | 今日涨幅 | 验证 |
|:----:|:----:|:----:|:----:|:--------:|:--------:|:--------:|:----:|
{{ztx_table}}

**准确率：{{ztx_accuracy}}，平均涨幅：{{ztx_avg_change}}**

### 2.3 合计统计

| 框架 | 准确率 | 平均涨幅 |
|------|--------|---------|
| 启动K | {{qdk_accuracy}} | {{qdk_avg_change}} |
| 砖型图 | {{ztx_accuracy}} | {{ztx_avg_change}} |
| **合计** | **{{total_accuracy}}** | **{{total_avg_change}}** |

---

## 三、归因分析

### 3.1 选股结果 vs 大盘环境

**今日市场环境**：{{market_env}}

**框架整体表现**：{{framework_performance}}

### 3.2 成功案例（与大盘/板块共振）

**{{success_stock1}}（{{success_code1}}，{{success_change1}}%）**
- 归因：{{success_reason1}}
- 板块助攻：{{sector_support1}}
- 逻辑：{{success_logic1}}

**{{success_stock2}}（{{success_code2}}，{{success_change2}}%）**
- 归因：{{success_reason2}}
- 板块助攻：{{sector_support2}}
- 逻辑：{{success_logic2}}

### 3.3 失败案例（与大盘/板块背离）

**{{fail_stock}}（{{fail_code}}，{{fail_change}}%）**
- 归因：{{fail_reason}}
- 教训：{{fail_lesson}}

---

## 四、自主学习总结

### 4.1 今日市场特征

{{today_market_features}}

### 4.2 框架表现 vs 市场环境匹配度

{{match_analysis}}

### 4.3 新增认知

**观察到**：
{{observation}}

**判断**：
{{judgment}}

**是否形成模式**（重复3次以上→升级到HOT）：
{{pattern_status}}

### 4.4 认知更新

| 认知 | 来源 | 状态 |
|------|------|------|
{{cognitive_updates}}

---

## 五、次日操作建议

{{next_day_suggestion}}

---

*选股日期：{{stock_date}}*
*验证日期：{{verify_date}}*
*数据来源：{{data_source}}*
