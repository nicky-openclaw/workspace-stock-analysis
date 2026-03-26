# 2026-03-26 教训：Session结束后没有保存每日记忆

## 事件
昨晚（2026-03-25）与用户的完整会话内容保存在 SESSION-STATE.md 中，但 session 结束后没有按 Rule M + Rule W-End 归档到：
1. `memory/YYYY-MM-DD.md`（每日记忆）
2. `self-improving/corrections.md`（教训日志）

## 影响
今日（2026-03-26）session重置后，用户昨晚配置的mx skills、分工调整、复盘SOP确认、cron任务配置等信息全部丢失，导致：
- 无法使用正确的skill（用烂的腾讯API解析）
- 复盘SOP版本混乱（用了旧版而非昨晚确认的版本）
- 复盘范围理解错误（复盘了全部股票而非仅上涨股票）

## 根因
AGENTS.md 中定义的 WAL → SESSION-STATE.md → corrections.md + memory/ 流程未被执行。SESSION-STATE.md 看起来是"堆积文件"，每次会话后追加而非归档。

## 正确做法（Rule M + W-End）
每次会话结束（用户说"没了/就这样/结束"或长时间无响应时）：
1. 读 SESSION-STATE.md
2. 提取 WAL 触发条目 → 追加到 corrections.md（CRR格式）
3. 创建/更新 memory/YYYY-MM-DD.md
4. 清空 SESSION-STATE.md 或移动到 archive/

## 待修复
- [ ] 检查 SESSION-STATE.md 的正确处理流程
- [ ] 确保每次会话结束自动触发 WAL 归档
- [ ] 建立 SESSION-STATE.md 堆积内容的清理机制

---

## [CRR-20260326-001]
**触发词**: 非交易日
**错误认知**: 3/26是非交易日，无法获取3/26数据
**正确认知**: 3/26是正常交易日，腾讯API返回了数据
**教训**: 不要凭日期判断猜测，必须先实际验证数据
**来源**: SESSION-STATE

## [CRR-20260326-002]
**触发词**: mx skill
**错误认知**: mx skill不可用/不会用，用了烂的腾讯API解析
**正确认知**: mx_finance_data可用，优先用它获取行业+涨跌数据
**教训**: 选股复盘必须先用mx skill，备用agent-browser
**来源**: SESSION-STATE

## [CRR-20260326-003]
**触发词**: 全部股票
**错误认知**: 复盘要分析全部选出的股票（55只QDK + 10只ZTX）
**正确认知**: 复盘范围=方案B，只复盘上涨股票（TOP5）
**教训**: 复盘只聚焦上涨股票，沉淀到案例库
**来源**: SESSION-STATE

## [CRR-20260326-004]
**触发词**: 飞书文档
**错误认知**: 没有feishu_doc工具，无法创建云文档
**正确认知**: 飞书官方插件自带feishu_doc，不需要单独配置
**教训**: AGENTS.md里有feishu_doc.create/write，但工具未加载到当前session，需重启Gateway
**来源**: SESSION-STATE

## [CRR-20260326-005]
**触发词**: TOP20
**错误认知**: 复盘要复盘TOP20只股票
**正确认知**: 复盘范围=QDK TOP5 + ZTX TOP5（共10只）
**教训**: 复盘范围严格按skill文件定义执行，不自行扩大
**来源**: SESSION-STATE
