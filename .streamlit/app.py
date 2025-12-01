import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 定义所有城市
cities = ['从化', '中山', '江门', '南沙二园', '佛山']
stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

# 初始化session state (仅包含必要的初始化，省略完整代码块)
if 'cities_data' not in st.session_state:
    st.session_state.cities_data = {}
if 'reasons_data' not in st.session_state:
    st.session_state.reasons_data = {}
if 'reason_labels' not in st.session_state:
    st.session_state.reason_labels = {
        'invalid': ['空号错号', '无人接听', '拒绝沟通', '信息错误'],
        'not_converted': ['需求不符', '预算不足', '竞品选择', '时机不对'],
        'not_client': ['价格问题', '服务担忧', '方案不符', '跟进中'],
        'not_visit': ['时间冲突', '距离太远', '兴趣减弱', '其他安排'],
        'not_deal': ['价格太贵', '被竞品抢走', '资金问题', '决策延迟']
    }

# 默认值 - 城市转化数据
default_values_conversion = {
    '从化': [21, 19, 17, 8, 4, 2],
    '中山': [30, 25, 20, 11, 5, 1],
    '江门': [6, 6, 5, 5, 1, 0],
    '南沙二园': [31, 26, 20, 11, 0, 0], 
    '佛山': [4, 4, 4, 3, 0, 0]
}
    
# 默认值 - 原因数量 (省略完整结构，仅保留键)
default_values_reasons = {
    'invalid': {}, 'not_converted': {}, 'not_client': {}, 'not_visit': {}, 'not_deal': {}
}

# 侧边栏和数据输入函数 (保持不变，此处省略)
# ...

# 漏斗图函数定义 (保持不变，此处省略)
# ...

# 定义 create_beautiful_funnel 和 create_horizontal_funnel 函数 (保持不变)
def create_beautiful_funnel(city_data, city_name, stages):
    # ... (函数体保持不变)
    values = city_data
    
    color_schemes = {
        '从化': ['#FF6B6B', '#FF8E8E', '#FFB1B1', '#FFD4D4', '#FFE8E8', '#FFF5F5'],
        '中山': ['#4ECDC4', '#88D8D0', '#A8E6DD', '#C8F3EC', '#E1F8F5', '#F0FCFA'],
        '江门': ['#45B7D1', '#7BC9E0', '#9AD6E8', '#B9E3F0', '#D4EDF7', '#EAF6FB'],
        '南沙二园': ['#96CEB4', '#B4E0C8', '#D2F0DC', '#E8F8F0', '#F2FBF4', '#F7FDF9'],
        '佛山': ['#FFD700', '#FFE64D', '#FFF099', '#FFF7CC', '#FFFBF0', '#FFFDF8']
    }
    
    colors = color_schemes.get(city_name, px.colors.sequential.Blues)
    
    text_colors = []
    for color in colors[:len(values)]:
        if color in ['#FF6B6B', '#FF8E8E', '#4ECDC4', '#45B7D1', '#96CEB4']:
            text_colors.append("white")
        else:
            text_colors.append("black")
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        textfont=dict(size=12, color=text_colors, weight="bold"),
        marker=dict(
            color=colors[:len(values)],
            line=dict(width=2, color="darkgray")
        ),
        connector=dict(
            line=dict(color="rgba(128,128,128,0.5)", width=2, dash="dot")
        ),
        opacity=0.85
    ))
    
    fig.update_layout(
        title={
            'text': f"<b>{city_name}转化漏斗</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': '#2C3E50'}
        },
        plot_bgcolor='rgba(248,248,248,0.8)',
        paper_bgcolor='white',
        font=dict(size=11),
        height=450,
        margin=dict(t=60, b=40, l=60, r=40),
        showlegend=False
    )
    
    return fig

def create_horizontal_funnel(city_data, city_name, stages):
    # ... (函数体保持不变)
    values = city_data
    
    horizontal_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD700', '#DDA0DD']
    
    valid_values = [v if v > 0 else 0.1 for v in values] 
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=valid_values,
        orientation="h",
        textposition="inside",
        textinfo="value+percent initial",
        textfont=dict(size=11, color="white", weight="bold"),
        marker=dict(
            color=horizontal_colors[:len(values)],
            line=dict(width=2, color="white")
        ),
        opacity=0.9
    ))
    
    fig.update_layout(
        title={
            'text': f"<b>{city_name}水平视图</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14, 'color': '#2C3E50'}
        },
        plot_bgcolor='rgba(248,248,248,0.8)',
        paper_bgcolor='white',
        height=400,
        margin=dict(t=50, b=40, l=80, r=40)
    )
    
    return fig


# ... (create_simple_reason_chart, create_pie_chart_for_reason 保持不变)

# ==================== 主图表生成函数 (重点修改转化漏斗部分) ====================
def generate_charts():
    cities_data = st.session_state.cities_data
    reasons_data = st.session_state.reasons_data

    # ... (数据汇总、成本分析部分保持不变) ...
    
    # ==================== 转化漏斗 ====================
    st.header("🎨 转化漏斗分析")
    st.markdown("该功能使用 **标签页（Tabs）** 展示不同维度的漏斗图。")
    
    tab1, tab2 = st.tabs(["🎯 垂直漏斗图", "📊 水平视图"])
    
    # === 垂直漏斗图 (Tab 1) ===
    with tab1:
        st.subheader("垂直漏斗图")
        
        # 使用 2 行 3 列布局，第 2 行仅使用 2 列
        # 0, 1, 2 在第一行 (row_idx=1)
        # 3, 4 在第二行 (row_idx=2)
        
        for i, city in enumerate(cities):
            row_idx = 1 if i < 3 else 2
            col_idx = (i % 3) + 1
            
            # 使用 make_subplots 来将所有图表在一个容器内统一布局
            # 这是一个更简洁的 Streamlit 布局方式，但在此处我们仍然使用 Streamlit 的列布局以简化代码
            
            if i < 3: # 第一行，3个城市
                if i == 0: col_row1_1, col_row1_2, col_row1_3 = st.columns(3)
                cols = [col_row1_1, col_row1_2, col_row1_3]
                with cols[i]:
                    fig_funnel = create_beautiful_funnel(cities_data[city], city, stages)
                    st.plotly_chart(fig_funnel, use_container_width=True)
            else: # 第二行，2个城市
                if i == 3: 
                    col_row2_1, col_row2_2, _ = st.columns([1, 1, 1]) # 创建 3 列，但只用前 2 列
                    cols = [col_row2_1, col_row2_2]
                
                with cols[i-3]:
                    fig_funnel = create_beautiful_funnel(cities_data[city], city, stages)
                    st.plotly_chart(fig_funnel, use_container_width=True)

    # === 水平视图 (Tab 2) ===
    with tab2:
        st.subheader("水平漏斗图")
        
        for i, city in enumerate(cities):
            if i < 3: # 第一行，3个城市
                if i == 0: col_row1_h1, col_row1_h2, col_row1_h3 = st.columns(3)
                cols = [col_row1_h1, col_row1_h2, col_row1_h3]
                with cols[i]:
                    fig_h = create_horizontal_funnel(cities_data[city], city, stages)
                    st.plotly_chart(fig_h, use_container_width=True)
            else: # 第二行，2个城市
                if i == 3: 
                    col_row2_h1, col_row2_h2, _ = st.columns([1, 1, 1]) # 创建 3 列，但只用前 2 列
                    cols = [col_row2_h1, col_row2_h2]
                
                with cols[i-3]:
                    fig_h = create_horizontal_funnel(cities_data[city], city, stages)
                    st.plotly_chart(fig_h, use_container_width=True)
    
    # ... (未转化客户深度分析部分保持不变) ...

# 侧边栏和数据输入代码 (省略)
def create_reason_inputs(stage_key, stage_title, reason_count=4):
    # ... (函数体保持不变)
    pass # 实际代码中需要保留该函数及调用

# 为确保代码完整性，请使用上一个回答中完整的代码结构，并替换 generate_charts 函数中的“转化漏斗”部分。

# 假设您已将前面的代码复制到 Streamlit 文件中，以下是主要的修改点：

```python
# ... (前面代码保持不变，包括 create_beautiful_funnel, create_horizontal_funnel)

# ==================== 主图表生成函数 (仅展示修改后的转化漏斗部分) ====================
def generate_charts():
    cities_data = st.session_state.cities_data
    reasons_data = st.session_state.reasons_data

    # ... (数据汇总、成本分析部分保持不变) ...

    # ==================== 转化漏斗 ====================
    st.header("🎨 转化漏斗分析")
    st.markdown("该功能使用 **标签页（Tabs）** 展示不同维度的漏斗图。") # 添加功能命名
    
    tab1, tab2 = st.tabs(["🎯 垂直漏斗图", "📊 水平视图"])
    
    # === 垂直漏斗图 (Tab 1) ===
    with tab1:
        st.subheader("垂直漏斗图")
        
        # 1. 绘制第一行 (3个城市)
        col_row1_1, col_row1_2, col_row1_3 = st.columns(3)
        cols_row1 = [col_row1_1, col_row1_2, col_row1_3]
        for i in range(3):
            city = cities[i]
            with cols_row1[i]:
                fig_funnel = create_beautiful_funnel(cities_data[city], city, stages)
                st.plotly_chart(fig_funnel, use_container_width=True)
                
        # 2. 绘制第二行 (2个城市)
        col_row2_1, col_row2_2, _ = st.columns([1, 1, 1]) # 创建 3 列，只用前 2 列
        cols_row2 = [col_row2_1, col_row2_2]
        for i in range(2):
            city = cities[i + 3] # 南沙二园 (index 3), 佛山 (index 4)
            with cols_row2[i]:
                fig_funnel = create_beautiful_funnel(cities_data[city], city, stages)
                st.plotly_chart(fig_funnel, use_container_width=True)


    # === 水平视图 (Tab 2) ===
    with tab2:
        st.subheader("水平漏斗图")
        
        # 1. 绘制第一行 (3个城市)
        col_row1_h1, col_row1_h2, col_row1_h3 = st.columns(3)
        cols_row1_h = [col_row1_h1, col_row1_h2, col_row1_h3]
        for i in range(3):
            city = cities[i]
            with cols_row1_h[i]:
                fig_h = create_horizontal_funnel(cities_data[city], city, stages)
                st.plotly_chart(fig_h, use_container_width=True)
                
        # 2. 绘制第二行 (2个城市)
        col_row2_h1, col_row2_h2, _ = st.columns([1, 1, 1])
        cols_row2_h = [col_row2_h1, col_row2_h2]
        for i in range(2):
            city = cities[i + 3]
            with cols_row2_h[i]:
                fig_h = create_horizontal_funnel(cities_data[city], city, stages)
                st.plotly_chart(fig_h, use_container_width=True)
    
    # ... (未转化客户深度分析部分保持不变) ...

# ... (代码末尾保持不变)
