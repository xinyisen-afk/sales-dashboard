import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 网页标题
st.set_page_config(page_title="销售数据分析系统", layout="wide")
st.title("🎯 三城市销售数据分析系统")

# 侧边栏 - 数据输入
st.sidebar.header("📊 数据输入")
cost_per_lead = st.sidebar.number_input("单条线索成本(元)", value=320, min_value=0)

# 城市数据输入
st.sidebar.subheader("各城市转化数据")

cities_data = {}
cities = ['从化', '中山', '江门']
stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

default_values = {
    '从化': [21, 19, 17, 8, 4, 0],
    '中山': [30, 25, 20, 11, 0, 0], 
    '江门': [6, 6, 5, 5, 1, 0]
}

for city in cities:
    st.sidebar.write(f"**{city}转化数据**")
    values = []
    for i, stage in enumerate(stages):
        value = st.sidebar.number_input(
            f"{city}-{stage}", 
            value=default_values[city][i],
            key=f"{city}_{stage}"
        )
        values.append(value)
    cities_data[city] = values

# 未转化原因数据
st.sidebar.subheader("未转化原因数据")
reasons_data = {
    '从化': {'地域不符': 6, '原因未知': 3, '行业不符': 3, '价格太高': 3},
    '中山': {'地域不符': 3, '原因未知': 2, '行业不符': 2, '预算不足': 2},
    '江门': {'跟进中': 1, '地域不符': 1, '原因未知': 2}
}

def create_beautiful_funnel(city_data, city_name, stages):
    """创建美观的漏斗图"""
    values = city_data
    total_leads = values[0]
    
    # 计算转化率
    conversion_rates = []
    for i, value in enumerate(values):
        if total_leads > 0:
            rate = (value / total_leads * 100)
            conversion_rates.append(f"{rate:.1f}%")
        else:
            conversion_rates.append("0%")
    
    # 创建漏斗图
    fig = go.Figure()
    
    # 主要漏斗
    fig.add_trace(go.Funnel(
        y=[f"{stage}<br>{rate}" for stage, rate in zip(stages, conversion_rates)],
        x=values,
        textposition="inside",
        textinfo="value+text",
        textfont=dict(size=14, color="white", family="Arial"),
        marker=dict(
            color=values,
            colorscale="Teal",  # 使用Teal色系，更专业
            line=dict(width=3, color="white")
        ),
        connector=dict(
            line=dict(color="grey", width=2, dash="dot")
        ),
        opacity=0.85
    ))
    
    # 添加阶段转化率标注
    annotations = []
    for i in range(1, len(values)):
        if values[i-1] > 0:
            stage_rate = (values[i] / values[i-1] * 100)
            annotations.append(dict(
                x=0.02,
                y=i-0.1,
                xref="paper",
                yref="y",
                text=f"→ {stage_rate:.1f}%",
                showarrow=False,
                font=dict(size=11, color="darkred"),
                bgcolor="lightyellow",
                bordercolor="darkred",
                borderwidth=1
            ))
    
    fig.update_layout(
        title={
            'text': f"<b>{city_name}转化漏斗</b><br><sub>总转化率: {conversion_rates[-1]}</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': 'darkblue'}
        },
        plot_bgcolor='rgba(245,245,245,0.8)',
        paper_bgcolor='white',
        font=dict(size=12, family="Microsoft YaHei"),
        height=500,
        margin=dict(t=80, b=50, l=80, r=50),
        annotations=annotations,
        showlegend=False
    )
    
    return fig

def create_horizontal_funnel(city_data, city_name, stages):
    """创建水平漏斗图"""
    values = city_data
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        orientation="h",
        textposition="inside",
        textinfo="value+percent initial",
        textfont=dict(size=12, color="white"),
        marker=dict(
            color=px.colors.sequential.Viridis,
            line=dict(width=2, color="white")
        ),
        opacity=0.9
    ))
    
    fig.update_layout(
        title=f"<b>{city_name}水平视图</b>",
        plot_bgcolor='white',
        height=400,
        margin=dict(t=60, b=50, l=100, r=50)
    )
    
    return fig

def generate_charts():
    # ==================== 汇总看板表格 ====================
    st.header("📈 数据汇总看板")
    
    summary_data = []
    for city in cities:
        values = cities_data[city]
        total_leads = values[0]
        valid_leads = values[2]
        clients = values[3]
        visits = values[4]
        deals = values[5]
        
        total_cost = total_leads * cost_per_lead
        valid_rate = (valid_leads / total_leads * 100) if total_leads > 0 else 0
        valid_lead_cost = total_cost / valid_leads if valid_leads > 0 else 0
        client_cost = total_cost / clients if clients > 0 else 0
        visit_cost = total_cost / visits if visits > 0 else 0
        deal_cost = total_cost / deals if deals > 0 else 0
        
        summary_data.append({
            '城市': city,
            '线索总量': total_leads,
            '线索有效率': f"{valid_rate:.1f}%",
            '线索成本': f"¥{cost_per_lead}",
            '有效线索成本': f"¥{valid_lead_cost:.0f}" if valid_lead_cost > 0 else "无限大",
            '客户成本': f"¥{client_cost:.0f}" if client_cost > 0 else "无限大",
            '到访成本': f"¥{visit_cost:.0f}" if visit_cost > 0 else "无限大",
            '成交成本': f"¥{deal_cost:.0f}" if deal_cost > 0 else "无限大"
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)

    # ==================== 成本分析 - Plotly柱状图 ====================
    st.header("💰 各阶段成本分析")
    
    fig_cost = make_subplots(rows=1, cols=3, subplot_titles=[f'{city}成本分析' for city in cities])
    
    cost_labels = ['线索', '接通', '有效', '客户', '到访', '成交']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    
    for i, city in enumerate(cities):
        values = cities_data[city]
        total_cost = values[0] * cost_per_lead
        
        stage_costs = []
        for j in range(len(values)):
            if values[j] > 0:
                cost = total_cost / values[j]
                stage_costs.append(cost)
            else:
                stage_costs.append(0)
        
        fig_cost.add_trace(
            go.Bar(
                name=city,
                x=cost_labels,
                y=stage_costs,
                marker_color=colors,
                text=[f'¥{cost:.0f}' for cost in stage_costs],
                textposition='auto',
                showlegend=False
            ),
            row=1, col=i+1
        )
        
        fig_cost.update_xaxes(title_text="阶段", row=1, col=i+1)
        fig_cost.update_yaxes(title_text="成本(元)", row=1, col=i+1)
    
    fig_cost.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig_cost, use_container_width=True)

    # ==================== 转化漏斗 - 优化后的美观漏斗图 ====================
    st.header("📊 转化漏斗分析")
    
    # 创建标签页显示不同类型的漏斗图
    tab1, tab2 = st.tabs(["垂直漏斗图", "水平视图"])
    
    with tab1:
        # 垂直漏斗图 - 三列布局
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig_funnel1 = create_beautiful_funnel(cities_data['从化'], '从化', stages)
            st.plotly_chart(fig_funnel1, use_container_width=True)
            
        with col2:
            fig_funnel2 = create_beautiful_funnel(cities_data['中山'], '中山', stages)
            st.plotly_chart(fig_funnel2, use_container_width=True)
            
        with col3:
            fig_funnel3 = create_beautiful_funnel(cities_data['江门'], '江门', stages)
            st.plotly_chart(fig_funnel3, use_container_width=True)
    
    with tab2:
        # 水平漏斗图 - 三列布局
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig_h1 = create_horizontal_funnel(cities_data['从化'], '从化', stages)
            st.plotly_chart(fig_h1, use_container_width=True)
            
        with col2:
            fig_h2 = create_horizontal_funnel(cities_data['中山'], '中山', stages)
            st.plotly_chart(fig_h2, use_container_width=True)
            
        with col3:
            fig_h3 = create_horizontal_funnel(cities_data['江门'], '江门', stages)
            st.plotly_chart(fig_h3, use_container_width=True)

    # ==================== 未转化原因分析 - Plotly水平柱状图 ====================
    st.header("❓ 未转化客户原因分析")
    
    fig_reason = make_subplots(rows=1, cols=3, subplot_titles=[f'{city}未转化原因' for city in cities])
    
    reason_colors = ['#FF9999', '#99CCFF', '#99FF99', '#FFD700']
    
    for i, city in enumerate(cities):
        reason_data = reasons_data[city]
        reasons = list(reason_data.keys())
        counts = list(reason_data.values())
        
        fig_reason.add_trace(
            go.Bar(
                name=city,
                y=reasons,
                x=counts,
                orientation='h',
                marker_color=reason_colors[:len(reasons)],
                text=counts,
                textposition='auto',
                showlegend=False
            ),
            row=1, col=i+1
        )
        
        fig_reason.update_xaxes(title_text="数量", row=1, col=i+1)
    
    fig_reason.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_reason, use_container_width=True)

    # ==================== 线索量对比 - Plotly饼图 ====================
    st.header("🔢 线索量分布")
    
    leads_data = [cities_data[city][0] for city in cities]
    
    fig_pie = px.pie(
        values=leads_data,
        names=cities,
        title='各城市线索量占比',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label+value')
    st.plotly_chart(fig_pie, use_container_width=True)

# 显示图表
generate_charts()

# 刷新按钮
if st.sidebar.button("🔄 刷新图表"):
    generate_charts()

st.sidebar.markdown("---")
st.sidebar.success("✅ 使用Plotly图表，中文完美支持！")
