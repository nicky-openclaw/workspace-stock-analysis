# 教训记录 - 2026-03-19

---

## Pitfall 1: 脚本数据在文件里，不在终端输出里

**症状**：qdk_step4_score.py输出的scores.json有完整指标（J值/RSI3/白线/黄线），但我只看了终端打印就自己手算了一遍，全部算错。

**根因**：脚本终端输出是给人看的展示，数据实际在输出文件里。我没有去读文件。

**解决方案**：脚本运行完 → 直接读取对应的JSON输出文件获取完整数据，不再看终端。

**触发时机**：每次执行完任何脚本之后

**Action**：读取 `*_scores.json` / `*_kline.json` 文件获取数据，不要看终端输出

---

## Pitfall 2: skill失败后没再调用skill就切换browser

**症状**：sector_analysis_v4.py返回0条数据，直接用浏览器截图，没有再次手动调用eastmoney_financial_data skill。

**根因**：SOP要求的流程是 skill失败→再次调用skill→还失败→才用browser。我跳过了中间步骤。

**解决方案**：
1. 脚本API失败 → 先手动再调一次eastmoney_financial_data skill
2. skill返回有效数据 → 使用
3. skill还失败 → 才用agent-browser兜底

**触发时机**：板块数据为空/失败时

---

## Pitfall 3: 三个框架文件版本不一致

**症状**：qdk/ztx/b1三个框架文件的脚本名、数据优先级、检查点完全不同步。

**根因**：workflow优化后只更新了部分文件，没有全部同步。

**解决方案**：每次执行选股前执行版本检查：
1. 读AGENTS.md（执行规范总则）
2. 读MEMORY.md（速查索引）
3. 读对应框架文件（详细手册）
4. 确认三者版本一致再开始

**触发时机**：每次收到选股任务时

---

## Pitfall 4: image工具可能不可用

**症状**：image工具调用minimax-understand-image skill，报错Unknown model。

**根因**：模型配置问题，工具不可用。

**解决方案**：备选方案：
- 腾讯API批量查询（通过code反查name）
- 直接使用已知股票code列表执行脚本
- 截图复制到patrol目录备用

**触发时机**：image工具调用失败时

---

*记录时间：2026-03-19 18:10*
