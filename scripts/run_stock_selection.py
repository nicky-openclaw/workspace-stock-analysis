#!/usr/bin/env python3
"""
统一选股入口脚本
用法: python3 run_stock_selection.py [qdk|ztx|b1]
"""
import subprocess, sys, os, json
from datetime import datetime

FRAMEWORKS = {
    'qdk': {
        'name': '启动K',
        'stocks_file': 'qdk_output/qdk_stocks.json',
        'kline_file': 'qdk_output/qdk_kline.json',
        'scores_file': 'qdk_output/qdk_scores.json',
        'patrol_dir': 'memory/patrol',
        'steps': [
            ('auto_recognize', 'scripts/qdk_auto_recognize.py'),
            ('step2_fetch', 'scripts/qdk_step2_fetch.py'),
            ('step3_calc', 'scripts/qdk_step3_calc.py'),
            ('step4_score', 'scripts/qdk_step4_score.py'),
        ]
    },
    'ztx': {
        'name': '砖型图',
        'stocks_file': 'ztx_output/ztx_stocks.json',
        'kline_file': 'ztx_output/ztx_kline.json',
        'scores_file': 'ztx_output/ztx_scores.json',
        'patrol_dir': 'memory/patrol',
        'steps': [
            ('auto_recognize', 'scripts/ztx_auto_recognize.py'),
            ('step2_fetch', 'scripts/ztx_step2_fetch.py'),
            ('step3_calc', 'scripts/ztx_step3_calc.py'),
            ('step4_score', 'scripts/ztx_step4_score.py'),
        ]
    },
    'b1': {
        'name': 'B1',
        'stocks_file': 'b1_output/b1_stocks.json',
        'kline_file': 'b1_output/b1_kline.json',
        'scores_file': 'b1_output/b1_scores.json',
        'patrol_dir': 'memory/patrol',
        'steps': [
            ('auto_recognize', 'scripts/b1_auto_recognize.py'),
            ('step2_fetch', 'scripts/b1_step2_fetch.py'),
            ('step3_calc', 'scripts/b1_step3_calc.py'),
            ('step4_score', 'scripts/b1_step4_score.py'),
        ]
    }
}

WORKDIR = os.path.expanduser('~/.openclaw/workspace-stock-analysis')

def run_step(name, script_path):
    print(f"\n🔄 执行 {name}...")
    result = subprocess.run(
        ['python3', script_path],
        cwd=WORKDIR,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ {name} 失败: {result.stderr}")
        return False
    print(f"✅ {name} 完成")
    return True

def load_scores(scores_file):
    path = os.path.join(WORKDIR, scores_file)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    # 兼容多种格式
    if 'stocks' in data:
        return data['stocks']
    elif 'all_scored' in data:
        return data['all_scored']
    elif 'top5' in data:
        return data['top5']
    elif 'top_limit_up' in data:
        # 砖型图格式
        return data['top_limit_up'] + data.get('non_limit_up', [])
    elif 'non_limit_up_count' in data:
        # 砖型图另一种格式
        return data.get('non_limit_up', [])
    return None

def generate_markdown(framework, scores_data):
    today = datetime.now().strftime('%Y-%m-%d')
    fw = FRAMEWORKS[framework]
    framework_name = fw['name']
    
    if not scores_data or len(scores_data) == 0:
        return None
    
    stocks = scores_data
    top5 = stocks[:5] if len(stocks) >= 5 else stocks
    
    md = f"""# 🚀 {framework_name}选股报告 - {today}

## 📊 今日选股结果

| 排名 | 代码 | 名称 | 涨幅% | 量比 | 位置 | 启动类型 | 评分 |
|:----:|:----:|:----:|:------:|:----:|:----:|:--------:|:----:|
"""
    for i, s in enumerate(top5, 1):
        vol = s.get('vol_ratio', 'N/A')
        if vol != 'N/A':
            vol = f"{vol}x"
        md += f"| {i} | {s.get('code', '')} | {s.get('name', '')} | {s.get('change_pct', 'N/A')} | {vol} | {s.get('position_label', 'N/A')} | {s.get('launch_type', 'N/A')} | {s.get('score', 'N/A')} |\n"
    
    # 淘汰股票
    eliminated = stocks[5:] if len(stocks) > 5 else []
    if eliminated:
        md += "\n## ⚠️ 今日未入选股票\n\n| 代码 | 名称 | 淘汰原因 |\n|:----:|:----:|:--------:|\n"
        for s in eliminated:
            md += f"| {s.get('code', '')} | {s.get('name', '')} | {s.get('eliminate_reason', '量化信号不明确')} |\n"
    
    md += f"\n---\n\n*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    return md

def save_to_patrol(framework, scores_data):
    """保存选股结果到 patrol 目录"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    patrol_dir = os.path.join(WORKDIR, 'memory', 'patrol', today)
    
    # 创建目录
    os.makedirs(patrol_dir, exist_ok=True)
    
    # 保存选股结果 JSON
    fw = FRAMEWORKS[framework]
    stocks_file = os.path.join(patrol_dir, f'{framework}_stocks.json')
    with open(stocks_file, 'w', encoding='utf-8') as f:
        json.dump({'stocks': scores_data, 'date': today}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 选股结果已保存: {stocks_file}")
    return patrol_dir

def main():
    if len(sys.argv) < 2:
        print("用法: python3 run_stock_selection.py [qdk|ztx|b1]")
        sys.exit(1)
    
    framework = sys.argv[1].lower()
    if framework not in FRAMEWORKS:
        print(f"未知框架: {framework}")
        print(f"可用框架: {', '.join(FRAMEWORKS.keys())}")
        sys.exit(1)
    
    fw = FRAMEWORKS[framework]
    print(f"\n{'='*60}")
    print(f"📊 {fw['name']}选股流程开始")
    print(f"{'='*60}")
    
    # 执行各步骤
    for step_name, script in fw['steps']:
        if not run_step(step_name, script):
            print(f"❌ 流程中断于 {step_name}")
            sys.exit(1)
    
    # 生成报告
    print(f"\n📝 生成markdown报告...")
    scores_data = load_scores(fw['scores_file'])
    md_content = generate_markdown(framework, scores_data)
    
    if md_content:
        # 保存markdown文件
        md_file = os.path.join(WORKDIR, f"{framework}_report.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"✅ 报告已保存: {md_file}")
        
        # 保存到 patrol 目录（供复盘使用）
        patrol_dir = save_to_patrol(framework, scores_data)
        patrol_md = os.path.join(patrol_dir, f'{framework}_report.md')
        with open(patrol_md, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"✅ 报告已保存到patrol: {patrol_md}")
        
        # 输出飞书文档创建指令
        print(f"\n{'='*60}")
        print("📤 飞书文档创建指令（请执行）:")
        print(f"{'='*60}")
        print(f"""
🎯 下一步操作（Agent执行）:

1. 读取报告文件:
   → read → path: {md_file}

2. 创建飞书文档:
   → feishu_create_doc → markdown: [上面的内容] → title: "{fw['name']}选股报告 {datetime.now().strftime('%Y-%m-%d')}"

3. 发送文档链接:
   → message → action:send → channel:feishu → target: user:ou_a4ac9339b404c3650179d05328bcee04 → message: "📊 {fw['name']}选股报告已生成！\n\n[文档链接]"
""")
    else:
        print("❌ 无法生成报告（无评分数据）")

if __name__ == '__main__':
    main()
