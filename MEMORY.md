# MEMORY.md - 股票分析 Agent 知识索引

## 身份
- **工作区**: ~/.openclaw/workspace-stock-analysis/
- **核心文件**: AGENTS.md（执行规范）

---

## 📁 文件索引（什么情况查什么）

| 场景 | 查什么文件 |
|------|-------------|
| 任何任务开始 | AGENTS.md（Rule 1） |
| 选股任务 | frameworks/qdk_framework_v4.md（v4.5）<br/>frameworks/ztx_framework_v3.md（v3.3）<br/>frameworks/b1_framework_v3.md（v3.3） |
| 复盘任务 | memory/patrol/market/YYYY-MM-DD.md（盘面分析）<br/>memory/patrol/YYYY-MM-DD/（选股记录） |
| 遇到问题 | memory_recall + memory/pitfalls/ |
| 查视频知识 | knowledge/总索引.md |

### patrol/ 目录结构（统一格式）

```
memory/patrol/
├── market/                    ← 盘面分析（独立目录）
│   ├── 2026-03-17.md
│   ├── 2026-03-18.md
│   └── 2026-03-19.md
└── YYYY-MM-DD/               ← 选股记录（每个交易日一个子目录）
    ├── [框架]_report.md       ← 选股报告
    ├── [框架]_scores.json    ← 评分结果
    ├── [框架]_stocks.json    ← 选股列表
    └── screenshots/           ← 截图（选股后清理）
```

**说明**：
- `memory/patrol/market/` = cron每日盘面分析输出
- `memory/patrol/YYYY-MM-DD/` = 手动选股/复盘的记录文件
- screenshots/ 内的截图在选股完成后删除，永久报告只保留md和json

---

## 框架文件索引

| 框架 | 文件 | 版本 |
|------|------|------|
| 启动K | frameworks/qdk_framework_v4.md | **v4.5（2026-03-19）** |
| 砖型图 | frameworks/ztx_framework_v3.md | **v3.3（2026-03-19）** |
| B1选股 | frameworks/b1_framework_v3.md | **v3.3（2026-03-19）** |

> ⚠️ 执行选股前必须读取对应框架文件，以框架文件版本号为准。AGENTS.md为执行规范总则，框架文件为详细手册，两者须保持一致。

---

## ⚡ 速查规则（2026-03-17更新）

- **浏览器自动化**：必须用 `agent-browser` CLI（exec调用），**禁止用 `browser` 工具**
- **板块数据优先级**：eastmoney_financial_data → agent-browser → QVeris（保底）
- **行业归属**：eastmoney_financial_data 或 agent-browser，**禁止直接用QVeris**
- **复盘涨幅**：必须用K线API计算
- **图片分析**：`image` 工具

---

## 🛠️ Skill索引

| Skill | 用途 | API Key |
|-------|------|---------|
| eastmoney_financial_data | 板块涨跌+主力净额（优先） | mkt_ed_FmsusuPQr6aZCpqc2Pgof6l7gGbnvS_riNSxtGeI |
| eastmoney_financial_search | 金融资讯搜索 | 同上 |
| qveris-official | 保底数据 | sk-PxV8UWOz7UcoaU6yt0rsAfrzmTpSAyW70Qge8jsj-8g |

---

## ⚠️ 记忆规范

- 教训/坑 → memory_store（fact + decision）
- 任务前 → memory_recall 检索
- 错误后 → 先写 memory/pitfalls/ 再继续

---

## 📌 关键实体

- 腾讯API: `https://qt.gtimg.cn/q=`
- 股票群: `oc_5079867a1fd5155704772dc651c7d230`
