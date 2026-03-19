# 砖形图脚本问题记录 (2026-03-17)

## 问题1: 日期校验函数错误

**问题描述**：
- `get_latest_trading_day()` 函数在非交易时段（凌晨）返回了"今天"而不是"昨天"
- 导致K线日期校验错误，显示警告信息混乱

**根因**：
- 原代码只判断周末，不判断当前是否在交易时段
- 凌晨运行脚本时错误地认为当天是交易日

**修复**：
- 添加交易时段判断（9:30-11:30, 13:00-15:00）
- 非交易时段返回昨天日期

**修复文件**：
- `scripts/ztx_step2_fetch.py` - get_latest_trading_day() 函数

---

## 问题2: 识图脚本未找到图片

**问题描述**：
- 用户发送的图片在 `media/inbound/` 目录
- 但 `ztx_auto_recognize.py` 只查找 `patrol/` 目录
- 导致脚本找不到新图片，使用了旧的 stocks.json

**根因**：
- 脚本只查找 patrol 目录，没有从 media/inbound 复制图片

**修复**：
- 在 ztx_auto_recognize.py 中添加从 media/inbound 复制图片的逻辑
- 或修改脚本查找路径

**修复文件**：
- `scripts/ztx_auto_recognize.py` - find_images() 函数

---

## 教训

1. **启动K和砖形图都存在同样问题**：脚本需要从正确的目录读取图片
2. **日期校验必须考虑非交易时段**：不能在凌晨返回"今天"
3. **自动识别前应先清理旧数据**：避免残留数据干扰

## 待办

- [ ] 修复 ztx_auto_recognize.py 的图片查找逻辑
- [ ] 确保 patrol 目录有最新图片（从 media/inbound 复制）
