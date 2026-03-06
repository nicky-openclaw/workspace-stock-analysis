# 2026-02-28 错误教训汇总

## 错误1：浏览器工具用错
- **错误**：使用 OpenClaw 内置 browser 工具
- **正确**：必须用 ~/.agents/skills/agent-browser/ skill
- **教训**：用户多次强调要用agent-browser，每次都要纠正

## 错误2：东方财富API作为首选
- **错误**：把东方财富API作为首选数据源
- **正确**：腾讯API为首选，东方财富API不稳定尽量避免
- **教训**：东方财富API经常不稳定，必须用腾讯API

---

## 核心原则（必须记住！）

1. **浏览器** → agent-browser skill（不是OpenClaw内置browser）
2. **数据** → 腾讯API为首选（东方财富API不稳定）
