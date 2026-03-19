#!/usr/bin/env python3
"""
股票交易体系 - 知识库思维导图 v2
干净的从上到下层次结构，左到右流程
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')

FONT_PATH = '/System/Library/Fonts/STHeiti Medium.ttc'
fp = FontProperties(fname=FONT_PATH)

fig, ax = plt.subplots(1, 1, figsize=(30, 22))
ax.set_xlim(0, 30)
ax.set_ylim(0, 22)
ax.axis('off')
ax.set_facecolor('#0d1117')
fig.patch.set_facecolor('#0d1117')

COLORS = {
    'root': '#f85149',
    'layer': '#1c2128',
    'theory': '#388bfd',
    'case': '#3fb950',
    'comprehensive': '#d29922',
    'ultra': '#a371f7',
    'mind': '#f778ba',
    'line': '#30363d',
    'arrow': '#6e7681',
    'text': 'white',
    'sub': '#8b949e',
}

# ====== 绘制函数 ======
def box(ax, cx, cy, w, h, text, color, fs=9, text_color='white'):
    r = 0.25
    p = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                       boxstyle=f"round,pad=0.05,rounding_size={r}",
                       facecolor=color, edgecolor='#ffffff44', linewidth=1.2, zorder=3)
    ax.add_patch(p)
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs,
            color=text_color, fontproperties=fp, fontweight='bold',
            zorder=4, linespacing=1.3)

def arrow(ax, x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=COLORS['arrow'],
                               lw=1.8, connectionstyle='arc3,rad=0'), zorder=2)

def h_arrow(ax, x1, y, x2):
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=COLORS['arrow'],
                               lw=1.5, connectionstyle='arc3,rad=0'), zorder=2)

# ====== 布局参数 ======
# Y轴位置（从上到下）
Y_ROOT = 20.5
Y_L1 = 18.2
Y_L2 = 15.5
Y_L3 = 12.5
Y_L4 = 9.5
Y_L5 = 6.5
Y_ULTRA = 3.5
Y_MIND = 0.8

# X轴位置
X_L0 = 1.0    # 根节点
X_L1 = 5.0    # 第一层
X_L2 = 10.5   # 第二层
X_L3 = 15.5   # 第三层
X_L4 = 20.5   # 第四层
X_L5 = 25.5   # 第五层

# ====== 根节点 ======
box(ax, X_L0, Y_ROOT, 2.8, 1.2, '股票交易\n知识体系', COLORS['root'], fs=12)

# ====== Layer 1: 骨架判断 ======
box(ax, X_L1, Y_L1, 3.0, 1.2, '第一层\n骨架判断', COLORS['layer'], fs=11)
ax.text(X_L1, Y_L1 + 0.75, 'Layer 1', fontsize=7, color=COLORS['sub'],
        fontproperties=fp, ha='center')
arrow(ax, X_L0 + 1.4, Y_ROOT - 0.6, X_L1 - 1.5, Y_L1)
h_arrow(ax, X_L1 - 1.5, Y_L1, X_L1 + 1.5)

# Layer 1 子节点
l1_data = [
    ('10.4\n双线战法', X_L1 - 1.6, Y_L1 - 1.6),
    ('12.10\n量价关系', X_L1 + 0.0, Y_L1 - 1.6),
    ('10.15\n关键K', X_L1 + 1.6, Y_L1 - 1.6),
    ('12.24\n暴力K', X_L1 + 3.2, Y_L1 - 1.6),
    ('11-12\n仓位管理', X_L1 + 4.8, Y_L1 - 1.6),
]
for text, bx, by in l1_data:
    box(ax, bx, by, 2.0, 0.9, text, COLORS['theory'], fs=8)
    arrow(ax, X_L1 + 1.5, Y_L1 - 0.6, bx, by + 0.45)

# ====== Layer 2: 择时 ======
box(ax, X_L2, Y_L2, 3.0, 1.2, '第二层\n择时', COLORS['layer'], fs=11)
ax.text(X_L2, Y_L2 + 0.75, 'Layer 2', fontsize=7, color=COLORS['sub'],
        fontproperties=fp, ha='center')
arrow(ax, X_L1 + 4.8, Y_L1 - 1.15, X_L2 - 1.5, Y_L2 + 0.5)
h_arrow(ax, X_L2 - 1.5, Y_L2, X_L2 + 1.5)

l2_data = [
    ('11.26\n五步工作流', X_L2 - 2.5, Y_L2 - 1.6),
    ('2.1 活跃市值指标\n（前置于五步）', X_L2 - 0.3, Y_L2 - 1.6),
    ('3.15\nB1×65案例', X_L2 + 2.0, Y_L2 - 1.6),
    ('10.22\n对称战法', X_L2 + 4.3, Y_L2 - 1.6),
]
for text, bx, by in l2_data:
    c = COLORS['case'] if '3.15' in text else COLORS['theory']
    box(ax, bx, by, 2.3, 0.9, text, c, fs=8)
    arrow(ax, X_L2 + 1.5, Y_L2 - 0.6, bx, by + 0.45)

# ====== Layer 3: 标的筛选 ======
box(ax, X_L3, Y_L3, 3.0, 1.2, '第三层\n标的筛选', COLORS['layer'], fs=11)
ax.text(X_L3, Y_L3 + 0.75, 'Layer 3', fontsize=7, color=COLORS['sub'],
        fontproperties=fp, ha='center')
arrow(ax, X_L2 + 4.3, Y_L2 - 1.15, X_L3 - 1.5, Y_L3 + 0.5)
h_arrow(ax, X_L3 - 1.5, Y_L3, X_L3 + 1.5)

l3_data = [
    ('0219\n波段选股', X_L3 - 3.0, Y_L3 - 1.6),
    ('12.31\n击穿对手盘', X_L3 - 0.8, Y_L3 - 1.6),
    ('8.13\n异动选牛股', X_L3 + 1.4, Y_L3 - 1.6),
    ('3.8\n异动与筹码\n(案例)', X_L3 + 3.6, Y_L3 - 1.6),
]
for text, bx, by in l3_data:
    c = COLORS['case'] if '案例' in text else COLORS['theory']
    box(ax, bx, by, 2.3, 0.9, text, c, fs=8)
    arrow(ax, X_L3 + 1.5, Y_L3 - 0.6, bx, by + 0.45)

# ====== Layer 4: 买卖点 ======
box(ax, X_L4, Y_L4, 3.0, 1.2, '第四层\n买卖点', COLORS['layer'], fs=11)
ax.text(X_L4, Y_L4 + 0.75, 'Layer 4', fontsize=7, color=COLORS['sub'],
        fontproperties=fp, ha='center')
arrow(ax, X_L3 + 3.6, Y_L3 - 1.15, X_L4 - 1.5, Y_L4 + 0.5)
h_arrow(ax, X_L4 - 1.5, Y_L4, X_L4 + 1.5)

l4_data = [
    ('10.6\nB2+B3战法', X_L4 - 4.0, Y_L4 - 1.6),
    ('1.7\nB2买点案例', X_L4 - 2.0, Y_L4 - 1.6),
    ('3.15\nB1信号库\n(100帧72股)', X_L4 + 0.0, Y_L4 - 1.6),
    ('8.24\n牛市逃顶', X_L4 + 2.0, Y_L4 - 1.6),
    ('9.17\n主力出货', X_L4 + 4.0, Y_L4 - 1.6),
]
for text, bx, by in l4_data:
    c = COLORS['case'] if '案例' in text or '3.15' in text else COLORS['theory']
    box(ax, bx, by, 2.3, 0.9, text, c, fs=8)
    arrow(ax, X_L4 + 1.5, Y_L4 - 0.6, bx, by + 0.45)

# ====== Layer 5: 进阶 ======
box(ax, X_L5, Y_L5, 3.0, 1.2, '第五层\n进阶策略', COLORS['layer'], fs=11)
ax.text(X_L5, Y_L5 + 0.75, 'Layer 5', fontsize=7, color=COLORS['sub'],
        fontproperties=fp, ha='center')
arrow(ax, X_L4 + 4.0, Y_L4 - 1.15, X_L5 - 1.5, Y_L5 + 0.5)
h_arrow(ax, X_L5 - 1.5, Y_L5, X_L5 + 1.5)

l5_data = [
    ('8.19\n量比选最强', X_L5 - 5.0, Y_L5 - 1.6),
    ('6.1\n单针下20', X_L5 - 3.0, Y_L5 - 1.6),
    ('7.30\n防卖飞', X_L5 - 1.0, Y_L5 - 1.6),
    ('6.11\n挖坑填坑', X_L5 + 1.0, Y_L5 - 1.6),
    ('7.23\n麒麟会运作\n(综合)', X_L5 + 3.0, Y_L5 - 1.6),
    ('9.3\n十张完美图', X_L5 + 5.0, Y_L5 - 1.6),
    ('9.24\n散户思维\n(心态)', X_L5 + 7.0, Y_L5 - 1.6),
]
for text, bx, by in l5_data:
    if '综合' in text:
        c = COLORS['comprehensive']
    elif '心态' in text:
        c = COLORS['mind']
    else:
        c = COLORS['theory']
    box(ax, bx, by, 2.2, 0.9, text, c, fs=8)
    arrow(ax, X_L5 + 1.5, Y_L5 - 0.6, bx, by + 0.45)

# ====== 超短线 ======
box(ax, X_L0 + 0.8, Y_ULTRA, 3.5, 1.2, '超短线·砖型图体系\n0220首讲→2.23补充→3.18核心', '#a371f7', fs=10)
arrow(ax, X_L0 + 1.4, Y_ROOT - 0.6, X_L0 + 0.8, Y_ULTRA + 1.3)
h_arrow(ax, X_L0 + 0.8, Y_ULTRA + 0.6, X_L0 + 0.8 + 1.0)

ultra_data = [
    ('0220\n砖型图首讲', X_L0 + 0.0, Y_ULTRA - 1.7),
    ('2.23\n砖型图补充', X_L0 + 2.0, Y_ULTRA - 1.7),
    ('3.18\n砖型核心用法', X_L0 + 4.0, Y_ULTRA - 1.7),
]
for text, bx, by in ultra_data:
    box(ax, bx, by, 2.2, 0.9, text, COLORS['ultra'], fs=8)
    arrow(ax, X_L0 + 0.8, Y_ULTRA - 0.6, bx, by + 0.45)

# ====== 心态类 ======
box(ax, X_L5 - 2.5, Y_MIND, 3.0, 1.2, '心态思维类', '#f778ba', fs=11)
h_arrow(ax, X_L5 + 0.5, Y_MIND + 0.6, X_L5 - 2.5 + 1.5)

mind_data = [
    ('3.11\n九篇心法', X_L5 - 6.0, Y_MIND),
    ('3.4\n闲聊案例', X_L5 - 3.8, Y_MIND),
    ('9.24\n散户思维', X_L5 - 1.6, Y_MIND),
]
for text, bx, by in mind_data:
    box(ax, bx, by, 2.2, 0.9, text, COLORS['mind'], fs=8)
    arrow(ax, X_L5 - 2.5 + 1.5, Y_MIND, bx, by + 0.45)

# ====== 学习路径（虚线）======
ax.annotate('', xy=(X_L2 - 0.3, Y_L2 - 1.15), xytext=(X_L2 - 0.3, Y_L2 - 0.6),
            arrowprops=dict(arrowstyle='->', color='#f78166', lw=2.0,
                           linestyle='dashed', connectionstyle='arc3,rad=0'), zorder=2)
ax.annotate('', xy=(X_L4 + 0.0, Y_L4 - 1.15), xytext=(X_L2 - 0.3, Y_L2 - 1.15),
            arrowprops=dict(arrowstyle='->', color='#f78166', lw=2.0,
                           linestyle='dashed', connectionstyle='arc3,rad=0'), zorder=2)
ax.text(X_L3 + 0.3, 10.8, '← B1学习路径 →\n(先学理论再看案例)', fontsize=7.5,
        color='#f78166', fontproperties=fp, ha='center', style='italic')

# ====== 图例 ======
legend = [
    ('理论类', COLORS['theory']),
    ('案例类', COLORS['case']),
    ('综合类', COLORS['comprehensive']),
    ('超短线', COLORS['ultra']),
    ('心态', COLORS['mind']),
]
lx, ly = 1.5, 1.8
for label, color in legend:
    p = FancyBboxPatch((lx - 0.8, ly - 0.3), 1.6, 0.6,
                        boxstyle="round,pad=0.05,rounding_size=0.15",
                        facecolor=color, edgecolor='white', linewidth=1, zorder=3)
    ax.add_patch(p)
    ax.text(lx, ly, label, ha='center', va='center', fontsize=8,
            color='white', fontproperties=fp, fontweight='bold', zorder=4)
    lx += 2.0

# 标题
ax.text(15, 21.5, '麒麟会战法 · 知识体系思维导图 v2',
        fontsize=16, color='white', fontproperties=fp,
        fontweight='bold', ha='center')
ax.text(15, 21.0, '基于总知识库5层框架  |  共30个系列  |  理论20 / 案例3 / 综合5  |  2026-03-19',
        fontsize=8, color='#6e7681', fontproperties=fp, ha='center')

plt.tight_layout(pad=0.3)
output_path = '/Users/nicky/.openclaw/workspace-stock-analysis/knowledge/知识体系思维导图_v2.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight',
            facecolor='#0d1117', edgecolor='none')
plt.close()
print(f'Saved: {output_path}')
