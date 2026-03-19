#!/usr/bin/env python3
"""
砖型图条件股自动识别脚本
功能：自动读取patrol目录下的砖型图截图，识别股票代码并去重
用法：python3 scripts/ztx_auto_recognize.py [日期]
"""

import os
import sys
import json
import glob
import subprocess

# 配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
PATROL_DIR = os.path.join(WORKSPACE_DIR, "patrol")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "ztx_output")
MEDIA_INBOUND_DIR = os.path.expanduser("~/.openclaw/media/inbound")
IMAGE_SCRIPT = os.path.expanduser("~/.openclaw/workspace/skills/minimax-understand-image/scripts/understand_image.py")
TENCENT_API = "https://qt.gtimg.cn/q={}"


def fill_missing_names(stocks):
    """补全缺失的股票名称"""
    import urllib.request
    
    # 找出需要查询的股票
    need_query = [s for s in stocks if not s.get('name')]
    if not need_query:
        return stocks
    
    # 添加市场前缀并批量查询（每次最多20只）
    for i in range(0, len(need_query), 20):
        batch = need_query[i:i+20]
        # 添加前缀: 6开头=sh, 0/3开头=sz
        codes_with_prefix = []
        for s in batch:
            code = s['code']
            if code.startswith('6'):
                codes_with_prefix.append('sh' + code)
            else:
                codes_with_prefix.append('sz' + code)
        
        url = TENCENT_API.format(",".join(codes_with_prefix))
        try:
            resp = urllib.request.urlopen(url, timeout=10)
            data = resp.read().decode('gbk', errors='ignore')
            for line in data.split(';'):
                if not line.strip():
                    continue
                # 解析返回数据，格式: "v_sh600000=\"51~股票名称~600000~..."
                # 需要先去掉 v_ 前缀和后面的 ="51 部分
                if '~' not in line:
                    continue
                # 提取代码和名称
                code_part = line.split('~')[0]
                # 去掉 v_sh 或 v_sz 前缀
                if '=' in code_part:
                    code_part = code_part.split('=')[0]
                full_code = code_part.replace('v_sh', '').replace('v_sz', '')
                name = line.split('~')[1] if '~' in line else ""
                
                # 更新stocks中对应的名称
                for s in stocks:
                    if s['code'] == full_code and not s.get('name'):
                        s['name'] = name
        except Exception as e:
            print(f"  警告: 批量获取名称失败: {e}")
    
    # 统计获取到的名称数量
    named_count = sum(1 for s in stocks if s.get('name'))
    print(f"  已补全 {named_count}/{len(stocks)} 只股票的名称")
    
    return stocks


def get_date_string(date_arg=None):
    if date_arg:
        return date_arg
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")


def find_images(date_str):
    # 首先尝试从 media/inbound 复制最新图片到 patrol 目录
    copy_latest_images(date_str)
    
    # 只使用 brick_ 前缀，统一命名规范
    patterns = [
        os.path.join(PATROL_DIR, f"{date_str}_brick_*.jpg"),
        os.path.join(PATROL_DIR, date_str, "brick_*.jpg"),
    ]
    images = []
    for pattern in patterns:
        images.extend(glob.glob(pattern))
    images.sort()
    return images


def copy_latest_images(date_str):
    """从 media/inbound 目录复制最新图片到 patrol 目录"""
    import shutil
    from datetime import datetime
    
    if not os.path.exists(MEDIA_INBOUND_DIR):
        return
    
    # 查找当天上传的图片（修改时间为当天）
    today = datetime.now().strftime("%Y-%m-%d")
    target_dir = os.path.join(PATROL_DIR, date_str)
    os.makedirs(target_dir, exist_ok=True)
    
    copied = []
    # 查找 jpg 图片
    for f in os.listdir(MEDIA_INBOUND_DIR):
        if f.endswith('.jpg'):
            src_path = os.path.join(MEDIA_INBOUND_DIR, f)
            # 检查修改时间
            mtime = datetime.fromtimestamp(os.path.getmtime(src_path))
            if mtime.strftime("%Y-%m-%d") == today:
                # 复制并重命名
                idx = len(copied) + 1
                dst_name = f"{date_str}_brick_{idx:02d}.jpg"
                dst_path = os.path.join(target_dir, dst_name)
                shutil.copy2(src_path, dst_path)
                copied.append(dst_path)
    
    if copied:
        print(f"  从 media/inbound 复制了 {len(copied)} 张图片到 patrol/")


def recognize_image(image_path):
    cmd = ["python3", IMAGE_SCRIPT, image_path, "请识别图片中的所有股票，列出股票代码和股票名称"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return []
        
        # 解析结果，提取 "代码 名称" 或 "代码:名称" 格式
        import re
        stocks = []
        
        # 清理结果文本
        text = result.stdout
        
        # 尝试匹配各种格式：
        # 1. 6位数字 + 空格/冒号/中文后的名称
        # 2. 名称 + 6位数字
        
        # 方法1: 找到所有6位数字代码
        all_codes = set(re.findall(r'\b(\d{6})\b', text))
        
        for code in all_codes:
            # 尝试在同一行或附近找名称
            name = extract_name_from_text(text, code)
            stocks.append({"code": code, "name": name})
        
        return stocks
    except:
        return []


def extract_name_from_text(text, code):
    """从识别结果文本中提取股票名称"""
    import re
    
    # 尝试各种格式
    
    # 格式1: "600000 浦发银行" 或 "600000:浦发银行"
    pattern1 = rf'{code}\s*[:：]\s*([^\d\n,，,，。]+)'
    match = re.search(pattern1, text)
    if match:
        name = match.group(1).strip()
        if len(name) >= 2:
            return name
    
    # 格式2: "1. 600000 浦发银行" 或 "1、600000浦发银行"
    pattern2 = rf'\d+[.、]\s*{code}\s*([^\d\n,，,，。]+)'
    match = re.search(pattern2, text)
    if match:
        name = match.group(1).strip()
        if len(name) >= 2:
            return name
    
    # 格式3: 查找代码后面的2-6个字符作为名称（排除常见无意义词）
    pattern3 = rf'{code}\s*([^\d\s,，,。，;；:：\[\]（）()]+)'
    match = re.search(pattern3, text)
    if match:
        name = match.group(1).strip()
        # 过滤掉常见无意义词
        ignore_words = ['股票', '代码', '如下', '包括', '分别', '共', '只', '个', '等', '和', '与']
        if len(name) >= 2 and name not in ignore_words:
            return name
    
    return ""


def main():
    date_str = get_date_string(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"日期: {date_str}")
    
    images = find_images(date_str)
    if not images:
        print("未找到砖型图截图")
        return
    
    print(f"找到 {len(images)} 张截图")
    
    all_stocks = []  # Changed from all_codes
    for i, img in enumerate(images, 1):
        print(f"识别第{i}张...")
        stocks = recognize_image(img)
        print(f"  识别到 {len(stocks)} 个股票")
        all_stocks.extend(stocks)
    
    # 去重，保留第一个名称
    seen = set()
    unique_stocks = []
    for s in all_stocks:
        if s['code'] not in seen:
            seen.add(s['code'])
            unique_stocks.append(s)
    
    # 补全缺失的股票名称
    unique_stocks = fill_missing_names(unique_stocks)
    
    print(f"总计: {len(all_stocks)} 个, 去重后: {len(unique_stocks)} 个")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, "ztx_stocks.json")
    
    stocks_list = unique_stocks
    stocks_data = {
        "date": date_str,
        "total_images": len(images),
        "total_recognized": len(all_stocks),
        "unique_count": len(unique_stocks),
        "stocks": stocks_list
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存到: {output_file}")


if __name__ == "__main__":
    main()
