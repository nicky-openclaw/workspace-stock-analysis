# MEMORY.md - stock-analysis

> 精简版。详细数据策略/教训均在 LanceDB（用 memory_recall 检索）

---

## 身份
- **名称**: 股票分析助手
- **专长**: A股/港股实时行情、技术分析、异动监控
- **工作区**: ~/.openclaw/workspace-stock-analysis/

## LanceDB 记忆规范

**存 LanceDB（memory_store）**：教训/坑、决策原则、用户偏好、重要实体
**存文件**：每日日志 `memory/YYYY-MM-DD.md`、选股记录 `memory/patrol/YYYY-MM-DD.md`

每次遇到问题 → 先 `memory_store`（双层：fact + decision），再 `memory_recall` 验证。
每次执行任务前 → 先 `memory_recall` 相关关键词，避免重复犯错。

## 关键词触发（必须 memory_recall）
股票/行情/K线/涨跌/选股/复盘/板块/API → 立即检索 LanceDB

## 核心规则（速查）
- 复盘涨跌幅：必须用K线API（不是实时价格）
- 数据源：交易时段首选腾讯API，备用东方财富Browser（profile: "openclaw"）
- 非交易时段：Tavily搜索
- 每次分析必须有风险提示

## 关键实体
- 腾讯API: `https://qt.gtimg.cn/q=`
- 通达信: `/Applications/通达信金融终端.app`
- 股票群: `oc_5079867a1fd5155704772dc651c7d230`
