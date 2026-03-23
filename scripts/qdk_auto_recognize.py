#!/usr/bin/env python3
"""
启动K条件股自动识别脚本
功能：自动读取patrol目录下的启动K截图，识别股票代码并去重
用法：python3 scripts/qdk_auto_recognize.py [日期]
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
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "qdk_output")
MEDIA_INBOUND_DIR = os.path.expanduser("~/.openclaw/media/inbound")
IMAGE_SCRIPT = os.path.expanduser("~/.openclaw/workspace/skills/minimax-understand-image/scripts/understand_image.py")


def get_date_string(date_arg=None):
    if date_arg:
        return date_arg
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")


TENCENT_API = "https://qt.gtimg.cn/q={}"


def copy_latest_images(date_str):
    """
    从 media/inbound 复制最新图片到 patrol 目录。
    
    注意：此函数仅在 patrol 目录没有任何符合 AGENTS.md 命名规范的图片
    （qdk_NN.png/jpg）时才会复制。
    AGENTS.md Step 0 会预先将截图保存为 qdk_NN.png，
    此时此函数不执行任何操作。
    """
    import shutil
    from datetime import datetime
    
    if not os.path.exists(MEDIA_INBOUND_DIR):
        return []
    
    date_hyphen = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    # 检查 patrol 目录是否已有 AGENTS.md 规范命名的图片
    # 如果有，说明 Step 0 已完成，无需复制
    existing = []
    for pattern in [
        os.path.join(PATROL_DIR, date_hyphen, "qdk_*.png"),
        os.path.join(PATROL_DIR, date_hyphen, "qdk_*.jpg"),
        os.path.join(WORKSPACE_DIR, "memory", "patrol", date_hyphen, "qdk_*.png"),
        os.path.join(WORKSPACE_DIR, "memory", "patrol", date_hyphen, "qdk_*.jpg"),
    ]:
        existing.extend(glob.glob(pattern))
    
    if existing:
        # Step 0 已保存截图，直接使用
        return []
    
    # 没有预存截图时，才从 media/inbound 复制（兜底逻辑）
    today = datetime.now().strftime("%Y-%m-%d")
    target_dir = os.path.join(PATROL_DIR, date_str)
    os.makedirs(target_dir, exist_ok=True)
    
    # 收集当天所有图片，按修改时间排序
    candidates = []
    for f in os.listdir(MEDIA_INBOUND_DIR):
        if f.endswith(('.jpg', '.png')):
            src_path = os.path.join(MEDIA_INBOUND_DIR, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(src_path))
            if mtime.strftime("%Y-%m-%d") == today:
                candidates.append((mtime, src_path))
    
    if not candidates:
        return []
    
    # 只复制最新的一张
    candidates.sort(key=lambda x: x[0])
    _, latest_src = candidates[-1]
    _, ext = os.path.splitext(latest_src)
    dst_name = f"{date_str}_qdk_01{ext}"
    dst_path = os.path.join(target_dir, dst_name)
    shutil.copy2(latest_src, dst_path)
    print(f"  [兜底] 从 media/inbound 复制最新图片到 patrol/")
    return [dst_path]


def find_images(date_str):
    # 首先尝试从 media/inbound 复制最新图片到 patrol 目录
    copy_latest_images(date_str)
    
    # 兼容两套命名规范：
    # 1. AGENTS.md 规范：memory/patrol/YYYY-MM-DD/qdk_NN.png/jpg
    # 2. 脚本旧规范：YYYYMMDD_qdk_NN.jpg 或 YYYYMMDD/startup_NN.jpg
    date_hyphen = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    patterns = [
        # AGENTS.md 规范：memory/patrol/YYYY-MM-DD/qdk_NN.png/jpg
        os.path.join(PATROL_DIR, date_hyphen, "qdk_*.png"),
        os.path.join(PATROL_DIR, date_hyphen, "qdk_*.jpg"),
        os.path.join(WORKSPACE_DIR, "memory", "patrol", date_hyphen, "qdk_*.png"),
        os.path.join(WORKSPACE_DIR, "memory", "patrol", date_hyphen, "qdk_*.jpg"),
        # 脚本旧规范
        os.path.join(PATROL_DIR, f"{date_str}_startup_*.jpg"),
        os.path.join(PATROL_DIR, f"{date_str}_qdk_*.jpg"),
        os.path.join(PATROL_DIR, date_str, "startup_*.jpg"),
        os.path.join(PATROL_DIR, date_str, "qdk_*.jpg"),
    ]
    images = []
    for pattern in patterns:
        images.extend(glob.glob(pattern))
    # 去重
    images = list(dict.fromkeys(images))
    images.sort()
    return images


def extract_name_from_text(text, code):
    """从识别结果文本中提取股票名称"""
    import re
    
    # 格式1: "600000 浦发银行" 或 "600000:浦发银行"
    pattern1 = rf'{code}\s*[:：]\s*([^\d\n,，,，。]+)'
    match = re.search(pattern1, text)
    if match:
        name = match.group(1).strip()
        if len(name) >= 2:
            return name
    
    # 格式2: "1. 600000 浦发银行" 或 "1、600000浦发银行"
    pattern2 = rf'\d+[.、]\s*{code}\s*([^\d\n,，,"]。]+)'
    match = re.search(pattern2, text)
    if match:
        name = match.group(1).strip()
        if len(name) >= 2:
            return name
    
    # 格式3: 处理 markdown 加粗格式 **代码** 名称
    pattern3 = rf'\*{2}{code}\*{2}\s*([^\*\n]+)'
    match = re.search(pattern3, text)
    if match:
        name = match.group(1).strip()
        ignore_words = ['股票', '代码', '如下', '包括', '分别', '共', '只', '个', '等', '和', '与']
        if len(name) >= 2 and name not in ignore_words:
            return name
    
    # 格式4: 查找代码后面的字符作为名称（排除常见无意义词和*）
    pattern4 = rf'{code}\s*([^*\d\s,，,"]。;；:：\[\]（）()]+)'
    match = re.search(pattern4, text)
    if match:
        name = match.group(1).strip()
        ignore_words = ['股票', '代码', '如下', '包括', '分别', '共', '只', '个', '等', '和', '与']
        if len(name) >= 2 and name not in ignore_words:
            return name
    
    return ""


def recognize_image(image_path):
    """识别图片中的股票代码和名称"""
    cmd = ["python3", IMAGE_SCRIPT, image_path, "请识别图片中的所有股票，列出股票代码和股票名称"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return []
        
        import re
        stocks = []
        text = result.stdout
        
        # 找到所有6位数字代码
        all_codes = set(re.findall(r'\b(\d{6})\b', text))
        
        for code in all_codes:
            name = extract_name_from_text(text, code)
            stocks.append({"code": code, "name": name})
        
        return stocks
    except:
        return []


def fill_missing_names(stocks):
    """补全缺失的股票名称"""
    import urllib.request
    
    # 找出需要查询的股票（空名或错误名）
    need_query = [s for s in stocks if not s.get('name') or s.get('name') in ('', '**')]
    if not need_query:
        return stocks
    
    # 按市场前缀分组，每次最多20只
    for i in range(0, len(need_query), 20):
        batch = need_query[i:i+20]
        codes_with_prefix = []
        for s in batch:
            code = s['code']
            codes_with_prefix.append('sh' + code) if code.startswith('6') else codes_with_prefix.append('sz' + code)
        
        url = TENCENT_API.format(",".join(codes_with_prefix))
        try:
            resp = urllib.request.urlopen(url, timeout=10)
            data = resp.read().decode('gbk', errors='ignore')
            for line in data.split(';'):
                if '~' not in line:
                    continue
                parts = line.split('~')
                # parts[0] = 'v_sh600000="51'（含 ="51 后缀）
                # parts[1] = 股票名称
                # parts[2] = 股票代码
                name = parts[1] if len(parts) > 1 else ""
                full_code = parts[2] if len(parts) > 2 else parts[0].replace('v_sh', '').replace('v_sz', '').split('=')[0]
                for s in stocks:
                    if s['code'] == full_code and (not s.get('name') or s.get('name') in ('', '**')):
                        s['name'] = name
        except Exception as e:
            print(f"  警告: 批量获取名称失败: {e}")
    
    # 统计获取到的名称数量
    named_count = sum(1 for s in stocks if s.get('name') and s.get('name') not in ('', '**'))
    print(f"  已补全 {named_count}/{len(stocks)} 只股票的名称")
    
    # 二次补全：对仍有空名或**名的股票重试
    remaining = [s for s in stocks if not s.get('name') or s.get('name') in ('', '**')]
    if remaining:
        print(f"  [二次补全] 还有 {len(remaining)} 只股票名字缺失，重试...")
        for i in range(0, len(remaining), 20):
            batch = remaining[i:i+20]
            codes_with_prefix = []
            for s in batch:
                code = s['code']
                codes_with_prefix.append('sh' + code) if code.startswith('6') else codes_with_prefix.append('sz' + code)
            url = TENCENT_API.format(",".join(codes_with_prefix))
            try:
                resp = urllib.request.urlopen(url, timeout=10)
                data = resp.read().decode('gbk', errors='ignore')
                for line in data.split(';'):
                    if '~' not in line:
                        continue
                    parts = line.split('~')
                    name = parts[1].strip() if len(parts) > 1 and parts[1].strip() else ''
                    if not name or name == '**':
                        continue
                    full_code = parts[2] if len(parts) > 2 else parts[0].replace('v_sh', '').replace('v_sz', '').split('=')[0]
                    for s in stocks:
                        if s['code'] == full_code and (not s.get('name') or s.get('name') in ('', '**')):
                            s['name'] = name
            except Exception as e:
                print(f"    二次补全失败: {e}")
    
    return stocks


def main():
    date_str = get_date_string(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"日期: {date_str}")
    
    images = find_images(date_str)
    if not images:
        print("未找到启动K截图")
        return
    
    print(f"找到 {len(images)} 张截图")
    
    all_stocks = []
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
    output_file = os.path.join(OUTPUT_DIR, "qdk_stocks.json")
    
    stocks_data = {
        "date": date_str,
        "total_images": len(images),
        "total_recognized": len(all_stocks),
        "unique_count": len(unique_stocks),
        "stocks": unique_stocks
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存到: {output_file}")


if __name__ == "__main__":
    main()
