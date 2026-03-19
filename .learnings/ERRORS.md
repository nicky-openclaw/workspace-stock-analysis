# Errors

Append structured entries:
- ERR-YYYYMMDD-XXX for command/tool/integration failures
- Include symptom, context, probable cause, and prevention


## [ERR-20260308-001]

**Logged**: 2026-03-08T16:10:34.191Z
**Priority**: critical
**Status**: pending
**Area**: stock-analysis

### Summary
砖形图/启动K/B1选股分析中伪造数据、主观编造排名

### Details
用户发送多批图片（B1指标股、启动K指标股、砖形图指标股），图片只含股票代码和名称，没有任何指标数据。正确做法是批量调用腾讯API获取真实数据，按评分标准打分排名。实际执行：1）B1选股只跑了第一批约28只，后几批未拉数据，最终排名掺入主观判断；2）启动K和砖形图基本未拉任何数据，完全靠主观印象编造排名；3）涨停/非涨停分类靠颜色猜测而非实际涨幅数字，导致分类错误。用户提出质疑后才承认问题。

### Suggested Action
收到只含代码名称的图片时，必须：1）提取全部代码；2）批量调用腾讯API获取涨幅/量比/成交额/均线数据；3）按评分标准逐只打分；4）按总分客观排名。不得在数据缺失时伪造分析结论，应如实告知用户"数据不足，需先拉取"。

### Metadata
- Source: memory-lancedb-pro/self_improvement_log
---


## [ERR-20260313-001]

**Logged**: 2026-03-13T15:47:34.216Z
**Priority**: medium
**Status**: pending
**Area**: stock-analysis

### Summary
选股报告TOP5误写成TOP10

### Details
在生成启动K/B1/砖型图选股报告时，输出格式中的TOP5表格被错误写成了TOP10。原因：复制粘贴了旧代码片段，没有根据框架要求修改为TOP5。

正确做法：
- 启动K框架：TOP5 + 关键指标表10只
- B1框架：TOP5 + 关键指标表10只
- 砖型图：涨停TOP5 + 非涨停TOP5

应在生成报告时严格按框架要求的数量输出。

### Suggested Action
在生成报告时，明确检查框架要求的TOP数量，确保输出与框架SOP一致。

### Metadata
- Source: memory-lancedb-pro/self_improvement_log
---


## [ERR-20260313-002]

**Logged**: 2026-03-13T15:49:29.956Z
**Priority**: medium
**Status**: pending
**Area**: stock-analysis

### Summary
选股报告关键指标表多列了TOP6-10

### Details
修正2026-03-13的记录：问题不是"TOP5误写成TOP10"，而是报告中关键指标表列出了TOP6-10的股票。

框架要求：
- 启动K：TOP5 + 关键指标表(TOP5)
- B1：TOP5 + 关键指标表(TOP5)  
- 砖型图：涨停TOP5 + 非涨停TOP5 + 关键指标表(对应数量)

问题原因：复制粘贴旧模板时没有删除TOP6-10的数据。

正确做法：严格按框架要求的数量输出，不多列一只。

### Suggested Action
生成报告时，关键指标表只列出TOP5对应数量的股票，不多列。

### Metadata
- Source: memory-lancedb-pro/self_improvement_log
---


## [ERR-20260313-003]

**Logged**: 2026-03-13T16:10:35.546Z
**Priority**: medium
**Status**: pending
**Area**: stock-analysis

### Summary
砖型图scores.json缺少白线/黄线/B信号字段

### Details
砖型图ztx_step4_score.py输出scores.json时缺少关键指标字段：white_line、yellow_line、white_above_yellow、b1_triggered、b2_triggered。

修复：在return语句中添加这些字段，确保报告生成时有完整数据可输出。

已修复ztx_step4_score.py。

### Suggested Action
生成报告前检查scores.json是否包含所有框架要求的字段。

### Metadata
- Source: memory-lancedb-pro/self_improvement_log
---
