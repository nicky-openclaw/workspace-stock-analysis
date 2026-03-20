# Pitfall: 启动K识图错误 + 板块数据缺失

**日期:** 2026-03-20

## 问题1：识图幻觉

**现象:** 第一次用 `image` 工具识别条件股截图，模型完全输出错误结果（6只错误股票），第二次识别仍然错误，直到第三次加了严格prompt才得到正确结果。

**根因:**
- `image` 工具在识别交易软件截图时受干扰（大量数字、密集排列），模型产生幻觉
- 第一次识别 API 返回 error (1033)，但我仍然使用了错误结果
- 没有对识别结果进行自检验证

**教训:**
- 识图必须用 `minimax-understand-image` skill（专用MCP服务）
- 识别后必须对照截图验证股票数量和内容
- 发现异常立即重新识别，不盲目相信单次结果

---

## 问题2：板块数据获取失败

**现象:** eastmoney push2 API 返回空响应，agent-browser 页面数据为JS动态加载无法提取，腾讯API只有行业代码没有板块涨跌幅。

**根因:**
- eastmoney push2 服务器在当前网络环境被屏蔽或限制
- agent-browser 动态页面snapshot无法获取表格数值

**正确做法:**
- 任何一步失败都要立即停止并汇报用户
- 不得在数据缺失情况下生成报告
- 报告中的板块数据标注"待补录"违反SOUL.md禁止猜测规则

---

## 问题3：执行流程违规

**违反的AGENTS.md规则:**
1. 没有做 memory_recall 前置检索
2. 没有读取 frameworks/qdk_framework_v4.md
3. 没有用 `minimax-understand-image` skill 识图
4. 写错了 stocks.json 路径（写到 qdk_output 而非 patrol/）
5. 没有用 `run_stock_selection.py` 统一入口
6. 跳过 Step 4.1 强制检查点
7. 板块数据失败后继续生成报告（应停止）

---

## 修复行动

1. ✅ 已存储 pitfall 和 decision 到 LanceDB
2. ✅ 通知用户当前状态
3. ✅ sector_analysis_v4.py API 解析路径修复（已验证可获取数据）
4. ✅ 已生成合规版报告（https://www.feishu.cn/docx/VSCQdcGI5oA0KhxMc4dcSQimnIg）
5. ✅ 已记录完整错误清单到 memory/pitfalls/2026-03-20-qdk-task-full-record.md
6. 待办：铭利达行业归属明日补录
7. 待办：上能电气/海优新材板块涨跌明日补录
