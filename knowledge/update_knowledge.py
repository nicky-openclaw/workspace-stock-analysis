#!/usr/bin/env python3
"""
知识库整合脚本 - 分批次处理
"""

import os
import json
import time
from datetime import datetime

# 配置
SOURCE_DIR = "/Users/nicky/Desktop/Z哥笔记"
OUTPUT_FILE = "/Users/nicky/.openclaw/workspace-stock-analysis/knowledge/knowledge_base.md"
LOG_FILE = "/Users/nicky/.openclaw/workspace-stock-analysis/knowledge/progress.json"

# 定义批次（按重要性排序）
BATCHES = [
    {"name": "2026/1.7 B2买点案例", "priority": 1, "done": True},
    {"name": "2025/10.6 B2+B3战法", "priority": 2, "done": False},
    {"name": "2025/10.4 双线战法", "priority": 3, "done": False},
    {"name": "2025/12.24 暴力k", "priority": 4, "done": False},
    {"name": "2025/6.1（单针下20）", "priority": 5, "done": False},
    {"name": "2026/2.4 当前环境下最好的交易策略", "priority": 6, "done": False},
    {"name": "2025/12.31 击穿对手盘", "priority": 7, "done": False},
    # ... 继续其他批次
]

def get_progress():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    return {"batches": BATCHES, "last_update": None}

def save_progress(progress):
    progress["last_update"] = datetime.now().isoformat()
    with open(LOG_FILE, 'w') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def get_next_batch():
    progress = get_progress()
    for i, b in enumerate(progress["batches"]):
        if not b.get("done", False):
            return b
    return None

print("=== 知识库整合进度 ===")
progress = get_progress()
for b in progress["batches"]:
    status = "✅" if b.get("done") else "⏳"
    print(f"{status} {b['name']}")

print(f"\n下一批次: {get_next_batch()}")
