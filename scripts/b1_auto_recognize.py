#!/usr/bin/env python3
"""
B1条件股自动识别脚本
功能：自动读取patrol目录下的B1截图，识别股票代码并去重
用法：python3 scripts/b1_auto_recognize.py [日期]
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
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "b1_output")
MEDIA_INBOUND_DIR = os.path.expanduser("~/.openclaw/media/inbound")
IMAGE_SCRIPT = os.path.expanduser("~/.openclaw/workspace/skills/minimax-understand-image/scripts/understand_image.py")


def get_date_string(date_arg=None):
    if date_arg:
        return date_arg
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")


def copy_latest_images(date_str):
    """从 media/inbound 目录复制最新图片到 patrol 目录"""
    import shutil
    from datetime import datetime
    
    if not os.path.exists(MEDIA_INBOUND_DIR):
        return []
    
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
                # 复制并重命名为 b1_ 前缀
                idx = len(copied) + 1
                dst_name = f"{date_str}_b1_{idx:02d}.jpg"
                dst_path = os.path.join(target_dir, dst_name)
                shutil.copy2(src_path, dst_path)
                copied.append(dst_path)
    
    if copied:
        print(f"  从 media/inbound 复制了 {len(copied)} 张图片到 patrol/")
    
    return copied


def find_b1_images(date_str):
    # 首先尝试从 media/inbound 复制最新图片到 patrol 目录
    copy_latest_images(date_str)
    
    patterns = [
        os.path.join(PATROL_DIR, f"{date_str}_b1_*.jpg"),
        os.path.join(PATROL_DIR, date_str, "b1_*.jpg"),
    ]
    images = []
    for pattern in patterns:
        images.extend(glob.glob(pattern))
    images.sort()
    return images


def recognize_image(image_path):
    cmd = ["python3", IMAGE_SCRIPT, image_path, "请识别图片中的所有股票，列出股票代码和股票名称"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return []
        import re
        stocks = []
        for line in result.stdout.split('\n'):
            matches = re.findall(r'\b(\d{6})\b', line)
            stocks.extend(matches)
        return list(set(stocks))
    except:
        return []


def main():
    date_str = get_date_string(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"日期: {date_str}")
    
    images = find_b1_images(date_str)
    if not images:
        print("未找到B1截图")
        return
    
    print(f"找到 {len(images)} 张截图")
    
    all_codes = []
    for i, img in enumerate(images, 1):
        print(f"识别第{i}张...")
        codes = recognize_image(img)
        print(f"  识别到 {len(codes)} 个代码")
        all_codes.extend(codes)
    
    unique_codes = sorted(set(all_codes))
    print(f"总计: {len(all_codes)} 个, 去重后: {len(unique_codes)} 个")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, "b1_stocks.json")
    
    stocks_list = [{"code": code, "name": ""} for code in unique_codes]
    stocks_data = {
        "date": date_str,
        "total_images": len(images),
        "total_recognized": len(all_codes),
        "unique_count": len(unique_codes),
        "stocks": stocks_list
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存到: {output_file}")


if __name__ == "__main__":
    main()
