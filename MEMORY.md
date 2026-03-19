# MEMORY.md - 股票分析 Agent 知识索引

## 身份
- **工作区**: ~/.openclaw/workspace-stock-analysis/
- **核心文件**: AGENTS.md（执行规范）

---

## 📁 文件索引（什么情况查什么）

| 场景 | 查什么文件 |
|------|-------------|
| 任何任务开始 | AGENTS.md（Rule 1） |
| 选股任务 | frameworks/qdk_framework_v4.md<br/>frameworks/ztx_framework_v3.md<br/>frameworks/b1_framework_v3.md |
| 复盘任务 | memory/patrol/YYYY-MM-DD.md |
| 遇到问题 | memory_recall + memory/pitfalls/ |
| 查视频知识 | knowledge/总索引.md |

---

## 框架文件索引

| 框架 | 文件 | 版本 |
|------|------|------|
| 启动K | frameworks/qdk_framework_v4.md | **v4.5（2026-03-19）** |
| 砖型图 | frameworks/ztx_framework_v3.md | v3 |
| B1选股 | frameworks/b1_framework_v3.md | v3 |

> ⚠️ 执行选股前必须读取对应框架文件，以框架文件版本号为准。AGENTS.md为执行规范总则，框架文件为详细手册，两者须保持一致。

---

## ⚡ 速查规则（2026-03-17更新）

- **浏览器自动化**：必须用 `agent-browser` CLI（exec调用），**禁止用 `browser` 工具**
- **板块数据优先级**：eastmoney_financial_data → agent-browser → QVeris（保底）
- **行业归属**：eastmoney_financial_data 或 agent-browser，**禁止直接用QVeris**
- **复盘涨幅**：必须用K线API计算
- **图片分析**：`image` 工具

---

## 🚀 选股SOP（快速索引）

| 步骤 | 操作 | 工具/脚本 |
|------|------|---------|
| 1 | 识图 | `image` 工具 |
| 2 | 写入stocks.json | 手动写入（含今日日期） |
| 3 | 执行选股 | `python3 scripts/run_stock_selection.py [qdk\|ztx\|b1]` |
| 4 | 板块分析 | `python3 scripts/sector_analysis_v4.py --framework [qdk\|ztx\|b1]` |
| 5 | 生成飞书文档 | `feishu_create_doc` + `message` 发送链接 |

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
