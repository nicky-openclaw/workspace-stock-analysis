#!/usr/bin/env python3
"""砖型图 - 板块分析 v4.0"""
import subprocess, sys
subprocess.run([sys.executable, "/Users/nicky/.openclaw/workspace-stock-analysis/scripts/sector_analysis_v4.py", "--framework", "ztx"] + sys.argv[1:])
