import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd

# ======================
#       字体设置
# ======================
font_path = "fonts/SimHei.ttf"   # 上传到 GitHub 的字体
fm.fontManager.addfont(font_path)
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ======================
#   页面基础设置
# ======================
st.set_page_config(page_title="销售数据分析系统", layout="wide")
st.title("🎯 三城市销售数据分析系统")

# ======================
#       输入区
# ======================
st.sidebar.header("📊 数据输入")
cost_per_lead = st.sidebar.number_input("单条线索成本(元)", value=320, min_value=0)

cities = ["从化", "中山", "江门"]
stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

default_values = {
    '从化': [21, 19, 17, 8, 4, 0],
    '中山': [30, 25, 20, 11, 0, 0],
    '江门': [6, 6, 5, 5, 1, 0]
}

cities_data = {}

# 城市输入表单
for city in cities:
    st.sidebar.subheader(f"{city} 转化数据")
    values = [
        st.sidebar.number_input(f"{city}-{stage}", value=default_values[city][i], key=f"{city}_{stage}")
        for i, stage in enumerate(stages)
    ]
    cities_data[city] = {"stages": stages, "values": values}

# ======================
#   未转化原因
# ======================
st.sidebar.header("❓ 未转化原因")

reason_types = {
    '从化': ['地域不符', '原因未知', '行业不符', '价格太高'],
    '中山': ['地域不符', '原因未知', '行业不符', '预算不足'],
    '江门': ['跟进中', '地域不符', '原因未知']
}

default_reason_values = {
    '从化': [6, 3, 3, 3],
    '中山': [3, 2, 2, 2],
    '江门': [1, 1, 2]
}

reasons_data = {}

for city in cities:
    st.sidebar.subheader(f"{city} 未转化原因")
    reasons_data[city] = {
        reason: st.sidebar.number_input(
            f"{city}-{reason}",
            value=default_reason_values[city][i],
            min_value=0,
            key=f"reason_{city}_{reason}"
        )
        for i, reason in enumerate(reason_types[city])
    }

# ======================
#      工具函数
# ======================

def calc_summary_table():
    table = []
    for city in cities:
        vals = cities_data[city]["values"]
        total_cost = vals[0] * cost_per_lead

        summary = {
            "城市": city,
            "线索总量": vals[0],
            "线索有效率": f"{(vals[2] / vals[0] * 100):.1f}%" if vals[0] else "0%",
            "线索成本": cost_per_lead,
            "线索有效成本": total_cost / vals[2] if vals[2] else None,
            "客户成本": total_cost / vals[3] if vals[3] else None,
            "到访成本": total_cost / vals[4] if vals[4] else None,
            "成交成本": total_cost / vals[5] if vals[5] else None,
        }

        # 转换 None → "\"
        for k, v in summary.items():
            if isinstance(v, float) and np.isinf(v):
                summary[k] = "\\"

        table.append(summary)

    return pd.DataFrame(table)


def draw_cost_chart():
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    cost_labels = {
        '线索量': '线索成本', '接通数': '接通成本', '有效数': '有效成本',
        '客户数': '客户成本', '到访数': '到访成本', '成交数': '成交成本'
    }

    for i, city in enumerate(cities):
        vals = cities_data[city]["values"]
        total_cost = vals[0] * cost_per_lead

        stage_costs = [total_cost / v if v else None for v in vals]
        labels = [f"{cost_labels[stage]}\n({vals[j]}人)" for j, stage in enumerate(stages) if vals[j] > 0]

        filtered_costs = [c for c in stage_costs if c]
        bars = axes[i].bar(range(len(filtered_costs)), filtered_costs, color=colors)

        axes[i].set_title(f"{city} - 成本分析")
        axes[i].set_ylabel("单条成本 (元)")
        axes[i].set_xticks(range(len(labels)))
        axes[i].set_xticklabels(labels, rotation=45, fontsize=8)

    plt.tight_layout()
    st.pyplot(fig)


def draw_funnel_chart():
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']

    for i, city in enumerate(cities):
        vals = cities_data[city]["values"]
        max_val = max(vals)

        left_offset = [(max_val - v) / 2 for v in vals]

        for j, v in enumerate(vals):
            axes[i].barh(stages[j], v, left=left_offset[j], color=colors[j])

        axes[i].set_title(f"{city}转化漏斗")
        axes[i].invert_yaxis()
        axes[i].set_xticks([])

    plt.tight_layout()
    st.pyplot(fig)


def draw_reason_chart():
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    colors = ['#FF9999', '#99CCFF', '#99FF99', '#FFD700', '#C9A0FF']

    for i, city in enumerate(cities):
        reasons = list(reasons_data[city].keys())
        counts = list(reasons_data[city].values())

        axes[i].barh(reasons, counts, color=colors[:len(reasons)])
        axes[i].set_title(city)
        axes[i].invert_yaxis()

    plt.tight_layout()
    st.pyplot(fig)

# ======================
#      数据展示区
# ======================
st.header("📈 数据汇总看板")
st.dataframe(calc_summary_table(), use_container_width=True)

st.header("💰 成本分析")
draw_cost_chart()

st.header("📊 转化漏斗分析")
draw_funnel_chart()

st.header("❓ 未转化客户原因分析")
draw_reason_chart()

