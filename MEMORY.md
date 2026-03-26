# MEMORY.md - 股票分析 Agent 知识索引

## 身份
- **工作区**: ~/.openclaw/workspace-stock-analysis/
- **核心文件**: AGENTS.md（执行规范）

---

## 📁 文件索引（什么情况查什么）

| 场景 | 查什么文件 |
|------|-------------|
| 任何任务开始 | AGENTS.md（Rule 1） |
| 选股任务 | frameworks/qdk_framework_v4.md（v4.6）<br/>frameworks/ztx_framework_v3.md（v3.4）<br/>frameworks/b1_framework_v3.md（v3.4） |
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

---

## 框架文件索引

| 框架 | 文件 | 版本 |
|------|------|------|
| 启动K | frameworks/qdk_framework_v4.md | **v4.6（2026-03-25）** |
| 砖型图 | frameworks/ztx_framework_v3.md | **v3.4（2026-03-25）** |
| B1选股 | frameworks/b1_framework_v3.md | **v3.4（2026-03-25）** |

---

## ⚡ 速查规则

- **浏览器自动化**：必须用 `agent-browser` CLI（exec调用），**禁止用 `browser` 工具**
- **板块数据优先级**：mx_finance_data → eastmoney_financial_data → agent-browser → QVeris
- **行业归属**：mx_finance_data 或 eastmoney_financial_data
- **复盘涨幅**：必须用K线API计算
- **图片分析**：必须用 `minimax-understand-image` skill

---

## 🛠️ Skill索引

| Skill | 用途 | 调用方式 |
|-------|------|---------|
| **mx_finance_data** | 行业归属 + 板块涨跌幅（首选，2次/股→1次） | `python3 ~/.openclaw/skills/mx-finance-data/scripts/get_data.py "查询内容"` |
| **mx_finance_search** | 金融资讯/热点实时搜索（盘中首选） | `python3 ~/.openclaw/skills/mx-finance-search/scripts/get_data.py "关键词" --no-save` |
| **eastmoney_financial_data** | 板块主力净额（f62字段，JSON稳定） | skill |
| **minimax-understand-image** | 图片识别（股票截图） | skill |

> ⚠️ mx skills 位置: `~/.openclaw/skills/`（软链接生效后）
> ⚠️ 选股用 mx_finance_data（行业+涨跌），复盘用 mx_finance_search（资讯）

---

## 📌 关键路径

- qdk_scores.json: `qdk_output/qdk_scores.json`
- ztx_scores.json: `ztx_output/ztx_scores.json`
- 板块缓存: `[framework]_output/sector_cache.json`
- 腾讯API: `https://qt.gtimg.cn/q=`
- 股票群: `oc_5079867a1fd5155704772dc651c7d230`

---

## ⚠️ 记忆规范

- 教训/坑 → memory_store + memory/pitfalls/
- 任务前 → memory_recall 检索
- 错误后 → 先写 memory/pitfalls/ 再继续
- 会话结束 → 归档到 memory/YYYY-MM-DD.md + corrections.md

---

## 2026-03-25 重要更新

### mx skills 已配置（4个全部加载）
- `mx_finance_data`：行业归属 + 板块涨跌幅
- `mx_finance_search`：金融资讯搜索
- `mx_macro_data`：宏观数据
- `mx_stocks_screener`：股票筛选

### 板块数据获取 v4.3
- mx_finance_data：行业归属 + 板块涨跌幅（自然语言一次搞定）
- eastmoney_financial_data：板块主力净额（f62字段）
- API调用：3次/股 → 2次/股

### feishu_create_doc 不稳定
- 工具在部分session可用，部分不可用
- 状态：插件已注册但session级加载不稳定

### 复盘范围
- 方案B：只复盘上涨股票（由用户2026-03-25确认）
- 每只上涨股票需填写：板块效应、驱动类型、催化剂

### 框架版本（2026-03-25更新）
- sector_analysis_v4.py → v4.3
- qdk_framework_v4.md → v4.6
- ztx_framework_v3.md → v3.4
- b1_framework_v3.md → v3.4
