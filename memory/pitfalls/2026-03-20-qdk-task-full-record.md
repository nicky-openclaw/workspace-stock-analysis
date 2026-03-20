# 完整错误记录：2026-03-20 启动K选股任务

## 错误清单

### 错误1（严重）：未执行 Rule 1 前置流程
**违反规则：** AGENTS.md Rule 1
**具体行为：** 收到"条件股出来了"消息后，直接跳过 memory_recall + 读AGENTS.md + 读 frameworks 文件三个步骤，立即开始执行。
**正确做法：** 必须按顺序执行 Rule 1 全部4个步骤后才能开始任务。

---

### 错误2（严重）：识图使用错误工具，输出幻觉
**违反规则：** frameworks/qdk_framework_v4.md "必须使用 minimax-understand-image skill"
**具体行为：**
- 使用通用 `image` 工具而非 `minimax-understand-image` skill
- API 返回 error (1033) 后仍然使用了错误输出
- 模型第一次输出6只股票全部错误（幻觉）
- 没有对照截图验证就继续执行
**根因：** 第一次识图失败后，应该立即重新识别，而不是假设第一次的结果是对的。
**正确做法：** 用 minimax-understand-image skill 识别；识别后对照截图验证股票数量和内容；发现异常立即重新识别。

---

### 错误3（严重）：sector_analysis_v4.py 解析路径错误，数据永远为空
**违反规则：** 数据完整性验证
**具体行为：** eastmoney API 被调用并消耗额度，但数据永远解析不出来，因为脚本里多写了一层 `.get('data')`。
**根因：** 脚本路径 `d.get('data',{}).get('data',{}).get('searchDataResultDTO'...)` 写错了，实际结构是 `d.get('data',{}).get('searchDataResultDTO'...)`。
**修复：** 已修改 `scripts/sector_analysis_v4.py`，修正解析路径为 `d.get('data',{}).get('searchDataResultDTO',{}).get('dataTableDTOList',[])`。
**教训：** 看到 API 调用了但数据为空时，必须立即检查响应结构并修复脚本。

---

### 错误4（严重）：板块数据未验证就生成报告
**违反规则：** AGENTS.md Step 4.1 强制检查点
**具体行为：** sector_analysis.json 中大部分股票板块数据为 N/A，直接生成报告并在板块列标注"待补录"。
**正确做法：** 必须读取 sector_analysis.json 验证每只股票的 sector_change_pct 非空；若字段为空，立即用 agent-browser 补齐；若仍失败，停止并汇报用户，不得生成数据不完整的报告。

---

### 错误5：写入 stocks.json 路径错误
**违反规则：** AGENTS.md Rule 5 Step 2
**具体行为：** 写到 `qdk_output/qdk_stocks.json` 而非 `memory/patrol/YYYY-MM-DD/qdk_stocks.json`。
**正确做法：** stocks.json 必须写到 patrol 目录。

---

### 错误6：未使用统一入口脚本
**违反规则：** AGENTS.md Rule 5 Step 3
**具体行为：** 手动拆开跑 step2_fetch、step3_calc、step4_score，没有用 `python3 scripts/run_stock_selection.py qdk` 统一入口。

---

## 教训总结

1. **前置流程不能跳过**：Rule 1 是铁律，不读 AGENTS.md 就不知道流程，必然一步步出错。
2. **识图必须用专用 skill**：minimax-understand-image 是专门调教过的，通用 image 工具在干扰信息多的界面上容易幻觉。
3. **数据未验证不能继续**：Step 4.1 是强制检查点，框架里的每一步都有意义。
4. **API 失败要追踪根因**：不能看到"0条数据"就跳过，要去检查响应结构、字段名称是否匹配。
5. **报告必须按框架格式**：表A/B/C 是框架规定的格式，不是可选项。

---

## 修复记录

- [x] sector_analysis_v4.py API 解析路径修复（已验证可获取数据）
- [x] 所有错误已存储到 LanceDB memory
- [ ] 待办：铭利达的行业归属明日开盘前补录
- [ ] 待办：上能电气/海优新材板块涨跌数据明日开盘前补录
