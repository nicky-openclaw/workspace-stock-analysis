# 2026-02-24 图片识别问题

## 问题描述
- image工具报错：MiniMax VLM API error (2049): invalid api key
- 但API Key实际有效（文本模型可用）
- 原因：image工具调用VL模型，但配置中缺少VL模型

## 解决方式
使用 **minimax-understand-image skill** 脚本：
```bash
python3 ~/.openclaw/workspace/skills/minimax-understand-image/scripts/understand_image.py <图片路径> "<提问>"
```

## 教训
- image工具不稳定，不要使用
- 必须用skill脚本方式调用图片识别
- 以后所有agent的图片识别都要用这个方式

## 更新的配置
- agent.yaml 图片识别规则已更新
- 禁止行为加入：❌ 不能使用image工具
