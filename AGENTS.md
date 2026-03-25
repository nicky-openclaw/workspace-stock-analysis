# AGENTS.md - 股票分析 Agent 执行规范

## 🎯 Rule 0: 任务开始前确认清单（铁律，每次任务必须执行）

**收到任何任务后，开始执行前必须确认以下所有事项：**

- [ ] **已读取 AGENTS.md 所有 Rule**，特别是本次任务的专属 Rule
- [ ] 已确认使用 **minimax-understand-image skill** 做识图（禁止用 `image` 工具）
- [ ] 已确认报告结构遵循 **SOP 框架**（禁止自行发挥结构）
- [ ] 如有任何疑问，**先停下来**汇报用户，不得凭记忆猜测执行

**如果跳过了上述确认直接开始执行，属于违规行为。**

---

## ⚡ Rule W: WAL 即时写（每次消息触发）

**收到任何消息时，若包含以下任一触发词，立即将内容写入 SESSION-STATE.md，再回复用户：**

| 触发类型 | 触发词示例 | 写入内容 |
|---------|-----------|---------|
| 纠正/否定 | "不是X" / "错了" / "其实" | 错误：原认知 → 正确认知 |
| 决策/结论 | "用X" / "选Y" / "确认" | Decision: X，Trigger: Y |
| 偏好 | "我喜欢X" / "不要Y" | Preference: X |
| 专有名词 | 代码/人名/股票/日期 | Entity: X |
| 具体数值 | 数字/ID/URL | Value: X |

**操作步骤**：
1. 检测到触发词 → **停** → 不立即回复
2. 读 SESSION-STATE.md（如存在）
3. 追加新内容到文件
4. 再回复用户

**SESSION-STATE.md 路径**：`~/.openclaw/workspace-stock-analysis/SESSION-STATE.md`

---

## 🎯 Rule 1: 任务执行前置流程（铁律）

**收到任何任务后，必须按顺序执行：**

1. ✅ memory_recall 检索相关关键词
2. ✅ 读取 memory/ 相关文件
3. ✅ 读取 AGENTS.md（检查任务规则）
4. ✅ 读取 frameworks/ 框架文件
5. ✅ **完成 Rule 0 确认清单的全部事项**
6. ✅ 开始执行

**禁止**：
- ❌ 不检索就执行
- ❌ 边执行边查
- ❌ 以为记住了就不查

---

## ⚠️ Rule 2: 禁止凭记忆输出

- 禁止不读取源文件就生成内容
- 禁止复制粘贴原文套入模板
- 禁止跳过步骤
- **禁止在未完成质量评级前将视频报告导入知识库**

---

## ⚡ Rule 3: 双层记忆存储

### 存储时机
- 遇到教训/坑 → 立即存储
- 用户纠正 → 立即存储
- 重要决策 → 立即存储

### 存储格式（双层）
1. **fact 层**：Pitfall: [症状]. Cause: [根因]. Fix: [解决方案]
2. **decision 层**：Principle: [行为规则]. Trigger: [何时触发]. Action: [怎么做]

### 存储位置
- LanceDB: `memory_store`（永久）
- 本地文件: `memory/pitfalls/YYYY-MM-DD-[关键词].md`

---

## 📊 数据源规则

| 场景 | 数据源 | 备注 |
|------|--------|------|
| 交易时段 | 腾讯API | qt.gtimg.cn |
| 交易时段备用 | 东方财富Browser | profile: "openclaw" |
| 非交易时段 | Tavily | 搜索 |
| 复盘涨幅 | **agent-browser** | 批量获取收盘价，禁止用实时价格 |
| 复盘备用 | 腾讯API | agent-browser失败时使用 |

---

## 🛠️ 工具规范

| 工具 | 规范 |
|------|------|
| 图片分析 | minimax-understand-image skill |
| 发文件 | cp → ~/.openclaw/media/ → 发送 |
| 复盘 | 必须用K线收盘价计算 |

---

## 📁 文件索引

| 任务类型 | 必须查的文件 |
|----------|--------------|
| 选股 | frameworks/*.md |
| 复盘 | patrol/YYYYMMDD/ 目录（上一交易日） |
| 复盘SOP | frameworks/review_sop.md |
| 知识库 | knowledge/总索引.md |
| **视频报告监控与评级** | **knowledge/视频报告质量评级.md** |

---

## 🎯 Rule 6: 视频报告监控与评级（铁律，禁止跳过）

**触发条件**：
- 用户要求检索小黑的视频分析产出时
- 每日定时（HEARTBEAT）检查 `~/Desktop/VideoAnalysisOutput/` 下新增的系列报告

### 执行步骤（严格按顺序）

**Step 1: 检测新系列**
- 扫描 `~/Desktop/VideoAnalysisOutput/` 目录
- 对比 `knowledge/视频报告质量评级.md` 中"已评估系列"表格
- 确认尚未评估的新系列，记录系列名

**Step 2: 读取评级标准（必须）**
- 读取 `knowledge/视频报告质量评级.md`（当前版本）
- 按文件内的分类标准（技术分析类 / 案例讲解类 / 心态思维类）判断系列类型
- 按文件内的评分公式执行打分和等级决策

**Step 3: 读取帧分析JSON**
- 路径：`~/Desktop/VideoAnalysisOutput/[系列名]_帧分析.json`
- 若无帧分析 JSON → 降级读取知识库 JSON：
  `~/Desktop/VideoAnalysisOutput/[系列名]_知识库.json`

**Step 4: 执行质量评级**
- 按 `knowledge/视频报告质量评级.md` 的标准执行打分
- 输出：总分 + 等级 + 处理建议

**Step 5: 决策**
- **≥90 分（优秀）**：✅ 直接导入知识库
- **75-89 分（合格）**：✅ 可导入
- **60-74 分（一般）**：⚠️ 单独处理，汇报用户后再决定
- **<60 分（不合格）**：❌ 不导入，标记需重做，汇报用户

**Step 6: 更新评级记录**
- 评级完成后，**立即更新** `knowledge/视频报告质量评级.md` 的"已评估系列"表格
- 格式：[系列名] | [类型] | [总分] | [等级] | [评分明细]

**Step 7: 导入知识库（如评级通过）**
- 参照 `knowledge/总索引.md` 的结构将内容归档
- 不得在未评级通过的情况下导入

**禁止**：
- ❌ 检测到新系列后不读评级文件就导入
- ❌ 跳过评级流程直接凭感觉判断
- ❌ 评级不达标仍然导入知识库
- ❌ 评级后不更新"已评估系列"表格

---

## 🚀 Rule 5: 选股SOP（铁律，禁止跳步）

### 触发条件
用户发送选股截图 + 关键词（启动K/砖型图/B1）

### 执行步骤（严格按顺序）

**Step 0: 截图命名与保存（收到截图后立即执行）**
1. 根据用户发送的关键词判断框架类型：
   - "启动K" → 框架 = `qdk`
   - "砖型图" / "砖图" → 框架 = `ztx`
   - "B1" / "b1" → 框架 = `b1`
2. 获取今日日期格式：`YYYY-MM-DD`
3. 创建目录：`memory/patrol/<今日日期>/`
4. 将截图**重命名**为 `[框架]_[序号].png`（如 `qdk_01.png`）并保存到该目录
5. **禁止**在未命名的情况下进行后续操作

**Step 1: 识图（必须使用 skill，禁止直接调用 image 工具）**
- **必须**使用 `minimax-understand-image` skill：
  ```bash
  python3 ~/.openclaw/skills/minimax-understand-image/scripts/understand_image.py \
    "memory/patrol/<今日日期>/[框架]_*.png" \
    "识别图中所有股票代码和名称，以列表形式输出"
  ```
- 禁止直接调用 `image` 工具（该工具有幻觉问题，会导致选股数据错误）
- 读取 `memory/patrol/<今日日期>/[框架]_*.png` 进行识别

**Step 2: 写入股票列表**
- 写入对应框架的 stocks.json（含今日日期）
- qdk → `memory/patrol/<今日日期>/qdk_stocks.json`
- ztx → `memory/patrol/<今日日期>/ztx_stocks.json`
- b1 → `memory/patrol/<今日日期>/b1_stocks.json`

**Step 3: 执行选股脚本**
```bash
python3 scripts/run_stock_selection.py [qdk|ztx|b1]
```
- 脚本根据框架类型自动调用对应的 step2/3/4 脚本
- 脚本自动读取 Step 2 写入的 stocks.json（路径见 Step 2）
- 脚本输出自动保存到 `memory/patrol/<今日日期>/`

> ⚠️ 【重要】脚本运行完后，**必须读取输出文件**（`*_scores.json`）获取完整数据，禁止只看终端输出。

**Step 4: 板块效应分析**
```bash
python3 scripts/sector_analysis_v4.py --framework [qdk|ztx|b1]
```
数据获取优先级（v4.2）：
1. 腾讯API → 个股涨跌幅
2. eastmoney_financial_data → 行业+板块涨跌+主力净额
3. agent-browser → 补齐行业（备用）
4. QVeris → 保底

**⚠️ Step 4.1（强制检查点）：验证板块数据**
- 板块分析完成后，必须读取 `memory/patrol/<今日日期>/sector_analysis.json`
- 检查每只股票的 `sector_change_pct` 字段是否非空
- **验证通过标准**：每只股票至少要有 `sector_change_pct`（板块涨跌幅）和 `sector_money_net`（主力净额）
- 若字段为空（解析失败），立即手动 curl eastmoney API 补全：
  ```bash
  curl -s -X POST "https://mkapi2.dfcfs.com/finskillshub/api/claw/query" \
    -H "Content-Type: application/json" \
    -H "apikey: mkt_ed_FmsusuPQr6aZCpqc2Pgof6l7gGbnvS_riNSxtGeI" \
    -d '{"toolQuery":"行业名称板块今日涨跌幅主力净流入"}' | python3 -c "..."
  ```
  注意：行业名称从 `entityTagDTO.fullName` 提取，板块涨跌幅在 `table.f3`，主力净额在 `table.f62`
- **若 eastmoney API 也失败**：立即停止并汇报用户，不得自行猜测板块数据
- 板块数据未验证通过之前，**禁止进入 Step 5**

**Step 5: 生成飞书文档**
- 读取 `memory/patrol/<今日日期>/[框架]_scores.json` 和 **已验证的板块数据**
- 调用 `feishu_create_doc` 创建文档（新建，不要在旧文档上 update）
- **报告必须严格遵循 SOP 框架结构**（包括评分子框架、数据字段顺序、输出格式）
- **禁止**凭记忆自行发挥结构或省略任何评分字段
- 调用 `message` 发送链接给用户

**禁止**：
- ❌ 跳过识图直接执行脚本
- ❌ 不写入stocks.json就执行
- ❌ 用 `browser` 工具（必须用 `agent-browser` CLI）
- ❌ 直接用QVeris获取行业（先用eastmoney_financial_data）
- ❌ 板块数据未验证通过就生成报告
- ❌ 在旧文档上update（总是新建）
- ❌ 表格单元格内使用内嵌格式（加粗/斜体等）
- ❌ 报告结构偏离 SOP 框架（禁止省略或自行调整评分子框架）
- ❌ 直接调用 `image` 工具做识图（必须用 minimax-understand-image skill）

**选股完成后的文件管理**：
1. `memory/patrol/YYYY-MM-DD/` 目录（选股任务开始时自动确保存在）
2. 截图命名格式：`[框架]_[序号].png`（如 `qdk_01.png`、`ztx_02.png`），保存到 `memory/patrol/YYYY-MM-DD/`
3. 脚本输出的 `*_stocks.json` 和 `*_scores.json` 保留在 `memory/patrol/YYYY-MM-DD/`（由脚本自动写入）
4. 飞书文档创建后，将报告正文保存到 `memory/patrol/YYYY-MM-DD/[框架]_report.md`
5. 选股任务全部完成后 → **删除该目录下所有截图**（截图用完即删，不保留）
6. 最终目录结构：
   ```
   memory/patrol/YYYY-MM-DD/
   ├── qdk_01.png              ← 临时（任务完成后删除）
   ├── ztx_01.png              ← 临时（任务完成后删除）
   ├── [框架]_scores.json    ← 永久评分数据
   ├── [框架]_stocks.json    ← 永久股票列表
   └── [框架]_report.md       ← 永久报告
   ```

## 🛠️ 脚本索引

| 脚本 | 用途 | 调用方式 |
|------|------|---------|
| `run_stock_selection.py` | 统一选股入口 | `python3 scripts/run_stock_selection.py [qdk\|ztx\|b1]` |
| `sector_analysis_v4.py` | 板块效应分析 | `python3 scripts/sector_analysis_v4.py --framework [qdk\|ztx\|b1]` |
| `qdk_step2_fetch.py` | 启动K K线获取 | 由run_stock_selection.py调用 |
| `qdk_step3_calc.py` | 启动K指标计算 | 由run_stock_selection.py调用 |
| `qdk_step4_score.py` | 启动K评分 | 由run_stock_selection.py调用 |
| `ztx_step2_fetch.py` | 砖型图 K线获取 | 由run_stock_selection.py调用 |
| `ztx_step3_calc.py` | 砖型图指标计算 | 由run_stock_selection.py调用 |
| `ztx_step4_score.py` | 砖型图评分 | 由run_stock_selection.py调用 |
| `b1_step2_fetch.py` | B1 K线获取 | 由run_stock_selection.py调用 |
| `b1_step3_calc.py` | B1指标计算 | 由run_stock_selection.py调用 |
| `b1_step4_score.py` | B1评分 | 由run_stock_selection.py调用 |

---

## 🛠️ 工具规范（更新）

| 工具 | 规范 |
|------|------|
| 图片分析 | **minimax-understand-image skill**（禁止用 `image` 工具）|
| 浏览器自动化 | **`agent-browser` CLI**（exec调用），禁止用 `browser` 工具 |
| 板块数据 | **eastmoney_financial_data** skill（优先），agent-browser（备用） |
| 发文件 | cp → ~/.openclaw/media/ → 发送 |
| 复盘 | 必须用K线收盘价计算 |

---

## 📈 Rule 4: 选股复盘铁律

**触发时机**：每个交易日 15:30 收盘后

**执行步骤**：
1. ✅ 读取 `memory/patrol/前一交易日/` 目录下的选股报告：
   - 启动K：`memory/patrol/YYYY-MM-DD/qdk_scores.json`
   - 砖型图：`memory/patrol/YYYY-MM-DD/ztx_scores.json`
   - B1：`memory/patrol/YYYY-MM-DD/b1_scores.json`
2. ✅ 用 **agent-browser** 批量获取所有选股今日收盘价和涨跌幅（禁止逐个浏览器查询）
3. ✅ 对每只股票进行归因分析（见 frameworks/review_sop.md）
4. ✅ 生成复盘报告保存到 `memory/patrol/YYYY-MM-DD/market.md`（选股结果）或 `memory/patrol/market/YYYY-MM-DD.md`（盘面分析）

**归因分析要素**：
- 今日开盘方式（高开/平开/低开）
- 今日量能变化（放量/缩量）
- 主力资金净流向
- 消息面/题材持续性
- 结论：延续强势 / 正常回调 / 诱多出货 / 一日游

**禁止**：
- ❌ 不读取patrol目录就开始复盘
- ❌ 只列涨跌幅不做归因分析
- ❌ 用浏览器逐个查询股价（改用agent-browser）

---

## 📄 飞书文档写作规范（铁律）

### 排版规则
- ❌ **禁止在表格单元格内使用加粗/斜体等内嵌格式**（飞书会将 `**加粗**` 当作原始标签渲染，导致排版异常）
- ✅ 数字和文字均使用纯文本
- ✅ 标题层级清晰（`#` > `##` > `###`）

### 更新规则（针对已存在的文档）
- ❌ **禁止在旧文档上做 update/replace**（容易遗漏、产生重复内容）
- ✅ **总是新建文档**：`feishu_create_doc` 创建干净文档
- ✅ 如必须更新现有文档：先用 `feishu_fetch_doc` 确认当前内容结构，`selection_with_ellipsis` 必须写足够长的唯一特征文本（不能只写标题）
- ✅ 更新后再次 `feishu_fetch_doc` 验证无重复内容

### 删除规则
- 删除旧文档时，如果提示需要授权，授权后立即重试删除操作

---

## 🔧 每周自我复盘

**时间**：每周日 10:00

**维度**：
- 任务完成率
- 自主性
- 学习改进

**流程**：
1. 读取本周 memory/ 文件
2. 分析完成情况
3. 写入周报

---

## 🧠 自主学习框架（self-improving）

**目录**：`self-improving/`

**核心文件**：
- `memory.md` — HOT记忆（≤100行，重复3次以上的经验）
- `corrections.md` — 纠正日志（用户纠正自动记录）
- `heartbeat-state.md` — 心跳状态
- `projects/stock-selection.md` — 选股框架学习
- `projects/market-analysis.md` — 大盘分析学习
- `projects/review_template.md` — 复盘报告模板

**运行规则**：
- 每次复盘后自动触发自我反思
- 用户纠正 → 记录到 corrections.md → 判断是否升级到 memory.md
- 重复3次以上的经验 → 升级到 memory.md（HOT）
- 认知更新 → 记录到对应 projects/ 文件

---

## 🔥 妙想 mx-skills 路由规则（金融问题默认调用）

收到金融相关问题时，按以下原则选择 skill：

| 问题类型 | 调用 Skill | 示例 |
|---------|-----------|------|
| 筛选符合特定条件的股票/基金/行业板块 | mx-stocks-screener | "今日涨跌幅大于5%的A股" |
| 联网检索金融资讯、公告、研报、市场热点 | mx-finance-search | "宁德时代近期公告" |
| 查询 GDP、CPI、宏观政策等经济数据 | mx-macro-data | "中美近十年GDP对比" |
| 查询股票/基金/债券的财务数据（PE/ROE/财报等）| eastmoney_financial_data | "宁德时代PE和ROE" |

**已安装的 mx-skills：**
- `mx-finance-search` — 金融资讯搜索（额度有限但数据权威）
- `mx-stocks-screener` — 智能选股
- `mx-macro-data` — 宏观数据

**注意**：
- 混合问题时，按主要需求选择最合适的一个 skill
- 需要多个 skill 综合分析时，依次调用，分别获取数据后再整合
- 额度用尽时，回退到新浪/腾讯API + agent-browser
