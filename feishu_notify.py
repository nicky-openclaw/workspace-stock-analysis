#!/usr/bin/env python3
"""
飞书消息推送
"""

import json
import requests

def send_feishu_message(message, webhook_url=None):
    """发送飞书消息"""
    # 这里需要配置飞书webhook
    # 示例：需要你提供飞书的webhook地址
    
    if not webhook_url:
        print("⚠️ 未配置飞书webhook，请设置后使用")
        return False
    
    data = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }
    
    try:
        resp = requests.post(webhook_url, data=json.dumps(data), timeout=10)
        return resp.status_code == 200
    except:
        return False

def format_stock_alert(results, scan_time):
    """格式化选股提醒"""
    message = f"📡 盘中监控 - {scan_time}\n\n"
    
    if not results:
        message += "暂无符合条件的股票\n"
        return message
    
    message += f"发现 {len(results)} 只强势股：\n\n"
    
    for r in results[:5]:
        message += f"⭐ {r['name']}({r['code']})\n"
        message += f"   涨幅: {r.get('change', 0):+.2f}%\n"
        message += f"   信号: {' '.join(r['signals'][:2])}\n\n"
    
    return message

if __name__ == "__main__":
    # 测试
    test_results = [
        {
            "code": "601890",
            "name": "亚星锚链",
            "change": 5.5,
            "signals": ["🚀涨幅>5%", "💰成交额>5亿"]
        }
    ]
    
    msg = format_stock_alert(test_results, "10:00")
    print(msg)
