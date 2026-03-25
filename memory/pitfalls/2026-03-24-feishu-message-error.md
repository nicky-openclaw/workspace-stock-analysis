# Pitfall: 飞书 message 工具报错 Unknown channel

## 日期
2026-03-24

## 症状
`message` 工具发送时报错：
- `Unknown channel: feishu`
- `Channel is required (no configured channels detected)`
- 之前一直能正常发送

## 排查结果
1. `channel=feishu` → Unknown channel
2. 不带 channel 参数 → "no configured channels detected"
3. 指定 `accountId=stock-analysis` → 同样的错误

## 临时解决方案
在飞书对话里直接回复（通过标准输出），不依赖message工具。

## 待确认
可能原因：飞书应用token过期 / 应用权限被调整 / OpenClaw飞书插件状态异常

## 另记：飞书文档删除问题
- 飞书API删除文档需要 `drive:file:delete` 权限
- 应用有 `space:document:delete` 但那是知识库文档，不是网盘文档
- 今天创建的文档是网盘文档，用的是 `feishu_doc` 工具
- `feishu_delete_doc` 对网盘文档删除返回400错误
