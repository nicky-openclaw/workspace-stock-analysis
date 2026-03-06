#!/usr/bin/env python3
"""
获取个股概念板块 - 使用agent-browser
用法: python3 get_concept.py 600498,300303,603958
"""

import subprocess
import sys
import re
import time

def get_concept(stock_code):
    """获取单只股票的概念板块"""
    # 判断市场
    if stock_code.startswith('6'):
        market = 'sh'
    elif stock_code.startswith('0') or stock_code.startswith('3'):
        market = 'sz'
    else:
        market = 'bj'
    
    url = f"https://quote.eastmoney.com/{market}{stock_code}.html"
    
    # 使用subprocess运行agent-browser命令
    cmds = [
        ['agent-browser', 'open', url],
        ['agent-browser', 'wait', '2000'],
        ['agent-browser', 'snapshot']
    ]
    
    try:
        # 打开页面
        result = subprocess.run(cmds[0], capture_output=True, text=True, timeout=15)
        if '✓' not in result.stdout:
            return {'concept': '未知', 'industry': '未知', 'error': '打开失败'}
        
        time.sleep(2)
        
        # 获取快照
        result = subprocess.run(cmds[2], capture_output=True, text=True, timeout=15)
        output = result.stdout
        
        # 提取概念板块
        concept_match = re.search(r'概念[：:]\s*([^\n]+)', output)
        industry_match = re.search(r'行业[：:]\s*([^\n]+)', output)
        
        # 从链接文本中提取
        concept_links = re.findall(r'概念.*?\[ref=', output)
        
        concept = concept_match.group(1).strip() if concept_match else ''
        industry = industry_match.group(1).strip() if industry_match else ''
        
        return {
            'concept': concept[:50] if concept else '未找到',
            'industry': industry[:50] if industry else '未找到'
        }
        
    except Exception as e:
        return {'concept': '未知', 'industry': '未知', 'error': str(e)[:30]}

def main():
    if len(sys.argv) < 2:
        print("用法: python3 get_concept.py 600498,300303,603958")
        sys.exit(1)
    
    codes = sys.argv[1].split(',')
    results = {}
    
    print(f"开始获取 {len(codes)} 只股票的概念板块...")
    
    for i, code in enumerate(codes):
        code = code.strip()
        if not code:
            continue
        
        print(f"[{i+1}/{len(codes)}] 获取 {code}...", end=" ")
        result = get_concept(code)
        results[code] = result
        print(f"概念:{result.get('concept', '未知')}")
    
    # 输出结果
    print("\n=== 结果汇总 ===")
    print("| 代码 | 概念板块 | 行业 |")
    print("|------|----------|------|")
    for code, info in results.items():
        print(f"| {code} | {info.get('concept', '未知')} | {info.get('industry', '未知')} |")
    
    # 保存到文件
    with open('/tmp/concept_result.txt', 'w') as f:
        for code, info in results.items():
            f.write(f"{code}: {info.get('concept')} | {info.get('industry')}\n")
    
    print("\n结果已保存到 /tmp/concept_result.txt")

if __name__ == '__main__':
    main()
