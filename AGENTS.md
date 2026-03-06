# WAL Protocol 配置说明

## 核心规则

**每次对话中检测到以下内容时：**

| 类型 | 触发词 | 行动 |
|------|--------|------|
| 纠正 | "不是X" / "是Y" / "实际上" | 立即写入 SESSION-STATE.md + memory_store |
| 决策 | "用X" / "选Y" / "确定" | 立即写入 SESSION-STATE.md + memory_store |
| 偏好 | "我喜欢X" / "不要Y" | 立即写入 SESSION-STATE.md + memory_store |
| 专有名词 | 人名/公司名/产品名 | 立即写入 SESSION-STATE.md |

## LanceDB-Pro 记忆插件使用规范（2026-03-04 更新）

### 记录方式
- **纠正/教训** → `memory_store` (category: fact, importance: 0.7+)
- **偏好** → `memory_store` (category: preference)
- **重要决策** → `memory_store` (category: decision)

### 读取方式
- 遇到问题 → 先 `memory_recall` 搜索，再回答
- 不依赖"我记得..."，相信搜索结果

### 分类标准
| Category | 用途 | 示例 |
|----------|------|------|
| fact | 客观事实、教训、问题记录 | "腾讯API返回涨幅字段错误" |
| preference | 用户偏好、习惯 | "复盘要用K线收盘价" |
| decision | 重要决策、执行方案 | "首选腾讯API，备用东方财富" |
| entity | 股票代码、人名等 | 个股分析记录 |

### importance 分级
- 0.9: 关键教训，重复会出大事
- 0.7: 重要规则，需要记住
- 0.5: 一般信息，辅助参考

## 执行流程

```
收到人类消息 → 扫描触发词 → 有触发 → 写 SESSION-STATE.md + memory_store → 再回复
                                      ↓
                               无触发 → 先 memory_recall 搜索 → 再回复
```

## SESSION-STATE.md 格式

```markdown
# Session State - {date}

## 关键更新
- [时间] 主题: 具体内容

## 待办
- [ ] 任务1

## 偏好
- 主题: 偏好内容
```

## 重要

- **先写后说** - 不要让"想回复"的冲动阻止你写细节
- **细节是明显的** - 当时很明显，但 context 会丢失
- **写是RAM，说是缓存** - SESSION-STATE.md 是唯一的保险

## 自我复盘（每周日10:00）

**核心原则**：自主执行、自主学习、自主进步

### 每周复盘维度
- **任务完成率**: 完成了多少？未完成原因？
- **自主性**: 有多少是主动做的？多少需要人类推动？
- **学习**: 本周学到了什么？
- **改进**: 下周要改进什么？

### 复盘流程
1. 读取本周 memory/ 文件
2. 分析完成情况
3. 写入 AGENTS.md 改进日志
4. 发送周报给用户


---

## 共享知识库（Rule 26）

**路径**：`~/.openclaw/workspace/shared-knowledge/`

**使用原则**：
- 遇到飞书/浏览器/cron/记忆/日期/配置相关问题 → 先查 shared-knowledge/
- 发现通用规律（任何 Agent 都可能遇到的）→ 写入 shared-knowledge/
- 文件列表见 `shared-knowledge/README.md`

**关键词速查**：
- 飞书发消息问题 → `shared-knowledge/feishu-api.md`
- 浏览器 profile 问题 → `shared-knowledge/browser-tips.md`
- Cron 报错/超时 → `shared-knowledge/cron-pitfalls.md`
- 记忆/LanceDB → `shared-knowledge/memory-system.md`
- 日期硬编码问题 → `shared-knowledge/date-handling.md`
- 配置/插件变更 → `shared-knowledge/config-rules.md`

---

## 坑记录强制机制（Rule 25）

**触发条件**（任意一条）：工具失败、任务报错、重复错误、用户纠正

**执行流程**：
```
遇到错误 → 先写坑记录 → 再回复用户/继续执行
```

**坑记录路径**：
- 本 Agent 专属坑 → `memory/pitfalls/YYYY-MM-DD-[关键词].md`
- 跨 Agent 通用坑 → 同时更新 `~/.openclaw/workspace/shared-knowledge/` 对应文件

**格式**：症状 / 根因 / 解决方案 / 预防措施
