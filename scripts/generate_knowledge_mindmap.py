#!/usr/bin/env python3
"""
股票交易体系 - 知识库思维导图生成器
生成知识体系可视化图片
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')

# 中文字体
FONT_PATH = '/System/Library/Fonts/STHeiti Medium.ttc'
fp = FontProperties(fname=FONT_PATH)

def get_font(size=10, weight='normal'):
    return fp

fig, ax = plt.subplots(1, 1, figsize=(28, 20))
ax.set_xlim(0, 28)
ax.set_ylim(0, 20)
ax.axis('off')
ax.set_facecolor('#1a1a2e')
fig.patch.set_facecolor('#1a1a2e')

# ========== 颜色方案 ==========
COLORS = {
    'root': '#e94560',
    'l1': '#0f3460',
    'l1_border': '#16213e',
    'l2': '#1a1a4e',
    'l2_border': '#533483',
    'theory': '#533483',
    'case': '#0f9b8e',
    'comprehensive': '#e07b39',
    'ultra': '#2d6a4f',
    'mind': '#9b2335',
    'arrow': '#888888',
    'text': 'white',
    'subtext': '#cccccc',
}

# ========== 绘制圆角矩形 ==========
def draw_box(ax, x, y, w, h, text, color, text_color='white', fontsize=9, radius=0.3):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle=f"round,pad=0.05,rounding_size={radius}",
                         facecolor=color, edgecolor='white', linewidth=1.2,
                         zorder=3)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center',
            fontsize=fontsize, color=text_color,
            fontproperties=fp, fontweight='bold', zorder=4,
            wrap=True)

def draw_centered_box(ax, x, y, w, h, text, color, text_color='white', fontsize=10):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.1,rounding_size=0.4",
                         facecolor=color, edgecolor='white', linewidth=2,
                         zorder=3)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center',
            fontsize=fontsize, color=text_color,
            fontproperties=fp, fontweight='bold', zorder=4)

# ========== 绘制箭头 ==========
def draw_arrow(ax, x1, y1, x2, y2, color='#888888'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                               lw=1.5, connectionstyle='arc3,rad=0'),
                zorder=2)

# ========== 布局参数 ==========
# 中心点
CX, CY = 14, 10

# 五个主层级的位置（上方半圆放射）
# Layer 1 (骨架判断) - 顶部
L1_Y = 17.5
# Layer 2 (择时) - 右上
L2_Y, L2_X = 15, 22
# Layer 3 (标的筛选) - 右
L3_Y, L3_X = 10, 24
# Layer 4 (买卖点) - 左下
L4_Y, L4_X = 5, 22
# Layer 5 (进阶策略) - 底部
L5_Y = 2.5
# 超短线 - 右下
U1_Y, U1_X = 5, 2
# 心态类 - 左上
M1_Y, M1_X = 15, 6

# ========== 根节点 ==========
draw_centered_box(ax, CX, CY, 3.5, 1.2, '股票交易\n知识体系', '#e94560', 'white', 13)

# ========== Layer 1: 骨架判断 ==========
draw_centered_box(ax, CX, L1_Y, 4, 1.1, '第一层\n骨架判断', '#0f3460', 'white', 11)
draw_arrow(ax, CX, CY + 0.6, CX, L1_Y - 0.55)

# Layer 1 子节点（理论类）
l1_items = [
    ('1.1 双线战法\n10.4', CX - 3.5, L1_Y - 1.8),
    ('1.2 量价关系\n12.10', CX - 1.2, L1_Y - 1.8),
    ('1.3 关键K\n10.15', CX + 1.2, L1_Y - 1.8),
    ('1.3 暴力K\n12.24', CX + 3.5, L1_Y - 1.8),
]
for text, bx, by in l1_items:
    draw_box(ax, bx, by, 2.2, 0.9, text, COLORS['theory'], fontsize=8)
    draw_arrow(ax, CX, L1_Y - 0.55, bx, by + 0.45)

# 仓位管理放在中层
draw_box(ax, CX + 3.8, 12.5, 2.0, 0.9, '1.4 仓位管理\n11-12', COLORS['theory'], fontsize=8)
draw_arrow(ax, CX + 1.75, CY + 0.6, CX + 3.8, 12.95)

# ========== Layer 2: 择时 ==========
draw_centered_box(ax, L2_X, L2_Y, 4, 1.1, '第二层\n择时', '#0f3460', 'white', 11)
draw_arrow(ax, CX + 1.75, CY + 0.6, L2_X - 2, L2_Y + 0.3)
ax.annotate('', xy=(L2_X - 2, L2_Y + 0.55), xytext=(CX + 1, CY + 0.6),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=1.5,
                           connectionstyle='arc3,rad=-0.2'), zorder=2)

l2_items = [
    ('2.1 五步工作流\n11.26', L2_X - 1.5, L2_Y - 1.8),
    ('2.1 活跃市值\n3.15案例', L2_X + 0.5, L2_Y - 1.8),
    ('2.2 对称战法\n10.22', L2_X + 2.5, L2_Y - 1.8),
]
for text, bx, by in l2_items:
    c = COLORS['case'] if '3.15' in text else COLORS['theory']
    draw_box(ax, bx, by, 2.2, 0.9, text, c, fontsize=8)
    draw_arrow(ax, L2_X, L2_Y - 0.55, bx, by + 0.45)

# ========== Layer 3: 标的筛选 ==========
draw_centered_box(ax, L3_X, L3_Y, 4, 1.1, '第三层\n标的筛选', '#0f3460', 'white', 11)
draw_arrow(ax, L2_X - 0.5, L2_Y - 1.35, L3_X - 2, L3_Y + 0.3)
ax.annotate('', xy=(L3_X - 2, L3_Y + 0.55), xytext=(L2_X, L2_Y - 1.3),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=1.5,
                           connectionstyle='arc3,rad=0.2'), zorder=2)

l3_items = [
    ('3.1 波段选股\n0219', L3_X - 1.5, L3_Y - 1.8),
    ('3.4 击穿对手盘\n12.31', L3_X + 0.5, L3_Y - 1.8),
    ('3.7 异动选牛\n8.13', L3_X + 2.5, L3_Y - 1.8),
]
for text, bx, by in l3_items:
    c = COLORS['case'] if '8.13' in text else COLORS['theory']
    draw_box(ax, bx, by, 2.2, 0.9, text, c, fontsize=8)
    draw_arrow(ax, L3_X, L3_Y - 0.55, bx, by + 0.45)

# ========== Layer 4: 买卖点 ==========
draw_centered_box(ax, L4_X, L4_Y, 4, 1.1, '第四层\n买卖点', '#0f3460', 'white', 11)
draw_arrow(ax, L3_X - 0.5, L3_Y - 1.35, L4_X + 0.5, L4_Y + 1.0)
ax.annotate('', xy=(L4_X + 0.5, L4_Y + 0.55), xytext=(L3_X, L3_Y - 1.3),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=1.5,
                           connectionstyle='arc3,rad=-0.2'), zorder=2)

l4_items = [
    ('4.1 B1/B2/B3战法\n10.6 理论', L4_X - 3.5, L4_Y - 1.8),
    ('4.1 B2买点案例\n1.7 案例', L4_X - 1.3, L4_Y - 1.8),
    ('4.1 B1信号丰富案例\n3.15', L4_X + 1.0, L4_Y - 1.8),
    ('4.4 牛市逃顶\n8.24', L4_X + 3.3, L4_Y - 1.8),
]
for text, bx, by in l4_items:
    c = COLORS['case'] if '案例' in text or '3.15' in text else COLORS['theory']
    draw_box(ax, bx, by, 2.2, 0.9, text, c, fontsize=8)
    draw_arrow(ax, L4_X, L4_Y - 0.55, bx, by + 0.45)

# ========== Layer 5: 进阶策略 ==========
draw_centered_box(ax, CX, L5_Y, 6, 1.1, '第五层 · 进阶策略', '#0f3460', 'white', 11)
draw_arrow(ax, L4_X - 1.5, L4_Y - 1.35, CX - 1, L5_Y + 1.5)
ax.annotate('', xy=(CX - 1, L5_Y + 0.55), xytext=(L4_X, L4_Y - 1.3),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=1.5,
                           connectionstyle='arc3,rad=0.3'), zorder=2)

l5_items = [
    ('5.1 量比选最强\n8.19', CX - 6, L5_Y - 1.8),
    ('5.2 单针下20\n6.1', CX - 3.5, L5_Y - 1.8),
    ('5.5 防卖飞\n7.30', CX - 1, L5_Y - 1.8),
    ('5.6 挖坑填坑\n6.11', CX + 1.5, L5_Y - 1.8),
    ('5.6 麒麟会运作\n7.23 综合', CX + 4, L5_Y - 1.8),
    ('5.8 十张完美图\n9.3', CX + 6.2, L5_Y - 1.8),
]
for text, bx, by in l5_items:
    if '综合' in text:
        c = COLORS['comprehensive']
    else:
        c = COLORS['theory']
    draw_box(ax, bx, by, 2.1, 0.9, text, c, fontsize=8)
    draw_arrow(ax, CX, L5_Y - 0.55, bx, by + 0.45)

# ========== 超短线体系 ==========
draw_centered_box(ax, U1_X, U1_Y, 4, 1.1, '超短线体系\n砖型图', '#2d6a4f', 'white', 11)
draw_arrow(ax, CX - 1.75, CY - 0.6, U1_X + 1, U1_Y + 1.0)
ax.annotate('', xy=(U1_X + 0.5, U1_Y + 0.55), xytext=(CX - 1, CY - 0.6),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=1.5,
                           connectionstyle='arc3,rad=0.2'), zorder=2)

u1_items = [
    ('超短基础理念\n0220', U1_X - 2, U1_Y - 1.8),
    ('砖型图补充\n2.23', U1_X + 0.5, U1_Y - 1.8),
    ('砖型图核心用法\n3.18', U1_X + 3, U1_Y - 1.8),
]
for text, bx, by in u1_items:
    draw_box(ax, bx, by, 2.2, 0.9, text, COLORS['ultra'], fontsize=8)
    draw_arrow(ax, U1_X, U1_Y - 0.55, bx, by + 0.45)

# ========== 心态类 ==========
draw_centered_box(ax, M1_X, M1_Y, 4, 1.1, '心态思维类', '#9b2335', 'white', 11)
draw_arrow(ax, CX - 1.75, CY + 0.6, M1_X + 2, M1_Y - 0.3)
ax.annotate('', xy=(M1_X + 1.5, M1_Y - 0.55), xytext=(CX - 1, CY + 0.6),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=1.5,
                           connectionstyle='arc3,rad=-0.3'), zorder=2)

m1_items = [
    ('九篇心法\n3.11', M1_X - 1.5, M1_Y - 1.8),
    ('散户思维\n9.24', M1_X + 0.5, M1_Y - 1.8),
    ('闲聊案例\n3.4', M1_X + 2.5, M1_Y - 1.8),
]
for text, bx, by in m1_items:
    draw_box(ax, bx, by, 2.1, 0.9, text, COLORS['mind'], fontsize=8)
    draw_arrow(ax, M1_X, M1_Y - 0.55, bx, by + 0.45)

# ========== 学习路径标注 ==========
# B1学习路径
path_x = [10.5, 10.5, 13.5]
path_y = [7.5, 4.5, 4.5]
ax.annotate('', xy=(13.5, 4.5), xytext=(10.5, 7.5),
            arrowprops=dict(arrowstyle='->', color='#ff6b6b', lw=2,
                           linestyle='dashed', connectionstyle='arc3,rad=-0.3'), zorder=2)
ax.text(10.8, 6.2, 'B1学习路径', fontsize=8, color='#ff6b6b',
        fontproperties=fp, style='italic')

# ========== 图例 ==========
legend_items = [
    ('理论类', COLORS['theory']),
    ('案例类', COLORS['case']),
    ('综合类', COLORS['comprehensive']),
    ('超短线', COLORS['ultra']),
    ('心态类', COLORS['mind']),
]
for i, (label, color) in enumerate(legend_items):
    x = 1 + i * 2.2
    y = 0.8
    box = FancyBboxPatch((x - 0.7, y - 0.3), 1.4, 0.6,
                         boxstyle="round,pad=0.05,rounding_size=0.2",
                         facecolor=color, edgecolor='white', linewidth=1, zorder=3)
    ax.add_patch(box)
    ax.text(x, y, label, ha='center', va='center', fontsize=8,
            color='white', fontproperties=fp, fontweight='bold', zorder=4)

ax.text(1, 19.5, '股票交易知识体系 v2.0  |  知识库总索引  |  2026-03-19',
         fontsize=9, color='#888888', fontproperties=fp)

# 顶部标题
ax.text(14, 19.8, '麒麟会战法 · 知识体系思维导图',
        fontsize=16, color='white', fontproperties=fp, fontweight='bold', ha='center')

plt.tight_layout(pad=0.5)
output_path = '/Users/nicky/.openclaw/workspace-stock-analysis/knowledge/知识体系思维导图.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight',
            facecolor='#1a1a2e', edgecolor='none')
plt.close()
print(f'Saved to: {output_path}')
