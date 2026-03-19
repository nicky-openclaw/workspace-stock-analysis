#!/usr/bin/env python3
"""启动K - 板块分析 v4.0"""
import subprocess, sys
subprocess.run([sys.executable, "/Users/nicky/.openclaw/workspace-stock-analysis/scripts/sector_analysis_v4.py", "--framework", "qdk"] + sys.argv[1:])
