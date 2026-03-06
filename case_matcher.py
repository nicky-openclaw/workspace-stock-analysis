#!/usr/bin/env python3
"""
知识库案例匹配工具
当选出股票后，匹配知识库中的相似案例
"""

# 知识库案例（从VideoAnalysisOutput提取）
B2_CASES = {
    "航天发展": {
        "code": "000547",
        "特征": "高值71的突破",
        "形态": "缩量横盘后放量启动",
        "关键": "只要能在此位置横化"
    },
    "十四连阳": {
        "code": "000001",
        "特征": "十四连阳",
        "意义": "证明2026年慢牛格局"
    },
    "内需消费": {
        "code": "",
        "特征": "政策导向",
        "意义": "2026年大的基调"
    }
}

# 从知识库提取的B2买点规则
B2_RULES = [
    "B2买点的核心是寻找突破后能继续上涨的股票",
    "高值只是辅助参考，关键是形态和量能",
    "突破位置不重要（55/80/100都可以），重要的是突破后能保持在80以上",
    "选股要选择形态完美的，缩量后微微放量的形态",
    "没有S1锁量，横盘后放量启动可追",
    "黄线位置的反包只需要看两者的关系",
    "打到黄线反弹是正常走势，不要慌",
    "做的是弱水三千只取一瓢，只抓确定性高的机会"
]

# 从知识库提取的超短线规则
ZHUANXING_RULES = [
    "超短线寻找转折点的爆发力",
    "绿转红是买点",
    "卖点：绿转绿、第二天不涨",
    "专注单一策略",
    "无脑执行策略",
    "速战速决（4-6根K线）",
    "没有S1锁量，横盘后放量启动可追"
]

# 砖形图相关规则
ZHUANXING_DETAIL = [
    "砖形图绿转红 = 买点",
    "砖形图红转绿 = 卖点",
    "只做转折点，不做普通波动",
    "寻找向上爆发力最强的位置"
]

def match_case(stock_code, signals):
    """匹配知识库案例"""
    matched = []
    
    # B2相关
    if "B2突破" in signals or "绿转红" in signals:
        matched.append({
            "类型": "B2买点",
            "规则": B2_RULES[:3],
            "提示": "突破后能继续上涨是关键，形态和量能优先"
        })
    
    # 超短线
    if "绿转红" in signals:
        matched.append({
            "类型": "砖形图超短",
            "规则": ZHUANXING_RULES[:4],
            "提示": "速战速决，4-6根K线必须走"
        })
    
    # RSI超卖
    if "RSI超卖" in str(signals):
        matched.append({
            "类型": "超跌反弹",
            "规则": ["RSI<30超卖", "等待反弹"],
            "提示": "抢反弹要快进快出"
        })
    
    # 多头趋势
    if "多头趋势" in signals:
        matched.append({
            "类型": "趋势跟随",
            "规则": ["顺势而为", "不做逆势"],
            "提示": "多头趋势中持股待涨"
        })
    
    return matched

def get_case_summary(code, signals):
    """获取案例总结"""
    matches = match_case(code, signals)
    
    if not matches:
        return "无匹配案例，请综合判断"
    
    summary = "\n📚 知识库匹配： for m\n"
    for m in matches:
        summary += f"\n【{m['类型']}】\n"
        for r in m["规则"]:
            summary += f"  • {r}\n"
        summary += f"  💡 {m['提示']}\n"
    
    return summary

# 测试
if __name__ == "__main__":
    # 测试用例
    test_signals = ["绿转红", "B2突破", "多头趋势"]
    print(get_case_summary("601890", test_signals))
    
    print("\n" + "="*50)
    
    test_signals2 = ["RSI超卖(25)", "单针"]
    print(get_case_summary("000001", test_signals2))
