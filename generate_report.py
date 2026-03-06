#!/usr/bin/env python3
"""
定时选股报告生成器
每天14:50自动运行，生成选股报告
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_stock_screener import *

def generate_report():
    """生成选股报告"""
    import io
    from contextlib import redirect_stdout
    
    # 捕获输出
    f = io.StringIO()
    with redirect_stdout(f):
        main()
    
    return f.getvalue()

if __name__ == "__main__":
    report = generate_report()
    print(report)
    
    # 保存到文件
    with open("/tmp/stock_report.txt", "w", encoding="utf-8") as fp:
        fp.write(report)
    
    print("\n报告已保存到 /tmp/stock_report.txt")
