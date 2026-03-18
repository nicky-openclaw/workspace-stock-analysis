# 选股框架索引

> 更新日期：2026-03-12

---

## 框架文件

| 框架 | 版本 | 文件 |
|------|------|------|
| 启动K | v4.1 | qdk_framework_v4.md |
| B1 | v3.1 | b1_framework_v3.md |
| 砖型图 | v3.1 | ztx_framework_v3.md |

---

## 触发规则

| 用户关键词 | 框架文件 |
|------------|----------|
| 启动K | qdk_framework_v4.md |
| B1 / B1选股 | b1_framework_v3.md |
| 砖型图 / 砖形图 | ztx_framework_v3.md |

---

## 完整执行流程（5步）

### 第1步：收截图 → 保存
收到用户选股截图后，**立即**保存到：
- 目录：`memory/patrol/YYYY-MM-DD/`
- 文件命名：`{框架}_{序号}.png`（如 `b1_001.png`, `ztx_001.png`）

### 第2步：识图分析 → 提取股票
调用识图规范（spawn子代理，串行处理单张图片）
- 输出：`memory/patrol/YYYY-MM-DD/{框架}_stocks.json`

### 第3步：数据计算 → 指标评分
执行各框架计算脚本：
- B1：`scripts/b1_step2_fetch.py` → `b1_output/b1_scores.json`
- 砖型图：`scripts/ztx_step4_score.py` → `ztx_output/ztx_scores.json`
- 启动K：`scripts/qdk_step4_score.py` → `qdk_output/qdk_scores.json`

### 第4步：生成选股报告
保存到：`memory/patrol/YYYY-MM-DD.md`
- 内容：TOP5结果、关键指标表、明日交易建议

### 第5步：发送飞书群
选股完成后**立即**发送到飞书群，不等待定时任务

### 第6步（自动）：清理截图
选股报告生成并确认后，删除 `memory/patrol/YYYY-MM-DD/` 下的png文件

---

## 通用规范

1. **图片识别**：必须使用 minimax-understand-image skill
2. **截图清理**：任务完成后删除 patrol 目录图片
3. **风险提示**：每次分析必须有风险提示
