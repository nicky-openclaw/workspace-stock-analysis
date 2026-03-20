# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Feishu 群组

- **股票分析群** - `oc_5079867a1fd5155704772dc651c7d230`

## 工具使用限制

### image 工具（禁用）

**禁止使用 `image` 工具进行股票条件股截图识别。**

原因：image 工具在股票截图识别上幻觉严重，2026-03-20 两次任务均导致完全错误的识别结果（QDK 第一次6只全错，ZTX 第一次86只识别为11只）。

**正确做法：** 必须使用 `minimax-understand-image` skill。如果 skill 不可用，排查配置问题而非换用 image 工具。
