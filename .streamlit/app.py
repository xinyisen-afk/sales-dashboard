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

# 未转化原因数据 - 扩展为四个维度
st.sidebar.header("🔍 未转化原因分析数据")

# 1. 无效线索原因
st.sidebar.subheader("无效线索原因")
invalid_reasons_data = {
    '从化': {'空号错号': 3, '无人接听': 2, '拒绝沟通': 1, '信息错误': 1},
    '中山': {'空号错号': 4, '无人接听': 3, '拒绝沟通': 2, '信息错误': 1},
    '江门': {'空号错号': 1, '无人接听': 1, '拒绝沟通': 0, '信息错误': 0}
}

# 2. 未转化线索原因 (接通但无效)
st.sidebar.subheader("未转化线索原因")
not_converted_reasons_data = {
    '从化': {'需求不符': 4, '预算不足': 3, '竞品选择': 2, '时机不对': 1},
    '中山': {'需求不符': 5, '预算不足': 2, '竞品选择': 3, '时机不对': 1},
    '江门': {'需求不符': 2, '预算不足': 1, '竞品选择': 1, '时机不对': 1}
}

# 3. 未转化客户原因 (有效但未成客户)
st.sidebar.subheader("未转化客户原因")
not_client_reasons_data = {
    '从化': {'价格问题': 4, '服务担忧': 2, '方案不符': 2, '跟进中': 1},
    '中山': {'价格问题': 3, '服务担忧': 3, '方案不符': 2, '跟进中': 1},
    '江门': {'价格问题': 2, '服务担忧': 1, '方案不符': 1, '跟进中': 1}
}

# 4. 未到访原因 (客户但未到访)
st.sidebar.subheader("未到访原因")
not_visit_reasons_data = {
    '从化': {'时间冲突': 2, '距离太远': 1, '兴趣减弱': 1, '其他安排': 0},
    '中山': {'时间冲突': 5, '距离太远': 3, '兴趣减弱': 2, '其他安排': 1},
    '江门': {'时间冲突': 2, '距离太远': 1, '兴趣减弱': 1, '其他安排': 1}
}

def create_reason_chart(reason_data, title, chart_type="bar"):
    """创建原因分析图表"""
    fig = make_subplots(rows=1, cols=3, subplot_titles=[f'{city}{title}' for city in cities])
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    
    for i, city in enumerate(cities):
        city_data = reason_data[city]
        reasons = list(city_data.keys())
        counts = list(city_data.values())
        
        if chart_type == "bar":
            fig.add_trace(
                go.Bar(
                    name=city,
                    y=reasons,
                    x=counts,
                    orientation='h',
                    marker_color=colors[:len(reasons)],
                    text=counts,
                    textposition='auto',
                    showlegend=False
                ),
                row=1, col=i+1
            )
            fig.update_xaxes(title_text="数量", row=1, col=i+1)
        else:
            # 饼图
            fig.add_trace(
                go.Pie(
                    labels=reasons,
                    values=counts,
                    name=city,
                    marker_colors=colors[:len(reasons)],
                    textinfo='percent+label',
                    showlegend=False
                ),
                row=1, col=i+1
            )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        title_text=f"<b>{title}分析</b>",
        title_x=0.5
    )
    return fig

def create_comparison_chart(reason_data, title):
    """创建城市对比图表"""
    all_reasons = set()
    for city_data in reason_data.values():
        all_reasons.update(city_data.keys())
    all_reasons = list(all_reasons)
    
    # 准备数据
    comparison_data = []
    for city in cities:
        city_data = reason_data[city]
        for reason in all_reasons:
            count = city_data.get(reason, 0)
            comparison_data.append({
                '城市': city,
                '原因': reason,
                '数量': count
            })
    
    df = pd.DataFrame(comparison_data)
    
    fig = px.bar(
        df, 
        x='原因', 
        y='数量', 
        color='城市',
        barmode='group',
        title=title,
        color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
    )
    
    fig.update_layout(
        height=500,
        xaxis_tickangle=-45
    )
    
    return fig

def create_sankey_diagram(reason_data, title):
    """创建桑基图显示原因分布"""
    labels = []
    source = []
    target = []
    value = []
    
    # 添加城市节点
    for i, city in enumerate(cities):
        labels.append(city)
    
    # 添加原因节点
    reason_offset = len(cities)
    all_reasons = set()
    for city_data in reason_data.values():
        all_reasons.update(city_data.keys())
    
    reason_list = list(all_reasons)
    for i, reason in enumerate(reason_list):
        labels.append(reason)
    
    # 创建连接
    for i, city in enumerate(cities):
        city_data = reason_data[city]
        for j, reason in enumerate(reason_list):
            if reason in city_data:
                source.append(i)  # 城市索引
                target.append(reason_offset + j)  # 原因索引
                value.append(city_data[reason])
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=["#FF6B6B", "#4ECDC4", "#45B7D1"] + ["#96CEB4"] * len(reason_list)
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        )
    )])
    
    fig.update_layout(
        title_text=f"<b>{title} - 桑基图</b>",
        font_size=12,
        height=500
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
    st.header("🎨 转化漏斗分析")
    
    # 创建标签页显示不同类型的漏斗图
    tab1, tab2, tab3 = st.tabs(["🎯 垂直漏斗图", "📊 水平视图", "🌈 渐变色视图"])
    
    with tab1:
        st.subheader("垂直漏斗图 - 各城市独立色彩")
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
        st.subheader("水平漏斗图 - 彩虹色彩")
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
    
    with tab3:
        st.subheader("渐变色漏斗图 - 现代风格")
        col1, col2, col3 = st.columns(3)
        with col1:
            fig_g1 = create_gradient_funnel(cities_data['从化'], '从化', stages)
            st.plotly_chart(fig_g1, use_container_width=True)
        with col2:
            fig_g2 = create_gradient_funnel(cities_data['中山'], '中山', stages)
            st.plotly_chart(fig_g2, use_container_width=True)
        with col3:
            fig_g3 = create_gradient_funnel(cities_data['江门'], '江门', stages)
            st.plotly_chart(fig_g3, use_container_width=True)

    # ==================== 未转化客户分析 - 四个维度的标签页 ====================
    st.header("🔍 未转化客户深度分析")
    
    # 创建四个分析维度的标签页
    reason_tab1, reason_tab2, reason_tab3, reason_tab4 = st.tabs([
        "❌ 无效线索原因", 
        "📞 未转化线索原因", 
        "👥 未转化客户原因", 
        "🚫 未到访原因"
    ])
    
    with reason_tab1:
        st.subheader("无效线索原因分析")
        
        # 在无效线索标签页内再创建子标签页
        subtab1, subtab2, subtab3 = st.tabs(["📊 柱状图分析", "🥧 饼图分析", "🔗 桑基图"])
        
        with subtab1:
            fig_invalid_bar = create_reason_chart(invalid_reasons_data, "无效线索原因", "bar")
            st.plotly_chart(fig_invalid_bar, use_container_width=True)
            
        with subtab2:
            fig_invalid_pie = create_reason_chart(invalid_reasons_data, "无效线索原因", "pie")
            st.plotly_chart(fig_invalid_pie, use_container_width=True)
            
        with subtab3:
            fig_invalid_sankey = create_sankey_diagram(invalid_reasons_data, "无效线索原因分布")
            st.plotly_chart(fig_invalid_sankey, use_container_width=True)
        
        # 城市对比图
        fig_invalid_compare = create_comparison_chart(invalid_reasons_data, "各城市无效线索原因对比")
        st.plotly_chart(fig_invalid_compare, use_container_width=True)
    
    with reason_tab2:
        st.subheader("未转化线索原因分析（接通但无效）")
        
        subtab1, subtab2, subtab3 = st.tabs(["📊 柱状图分析", "🥧 饼图分析", "🔗 桑基图"])
        
        with subtab1:
            fig_not_conv_bar = create_reason_chart(not_converted_reasons_data, "未转化线索原因", "bar")
            st.plotly_chart(fig_not_conv_bar, use_container_width=True)
            
        with subtab2:
            fig_not_conv_pie = create_reason_chart(not_converted_reasons_data, "未转化线索原因", "pie")
            st.plotly_chart(fig_not_conv_pie, use_container_width=True)
            
        with subtab3:
            fig_not_conv_sankey = create_sankey_diagram(not_converted_reasons_data, "未转化线索原因分布")
            st.plotly_chart(fig_not_conv_sankey, use_container_width=True)
        
        fig_not_conv_compare = create_comparison_chart(not_converted_reasons_data, "各城市未转化线索原因对比")
        st.plotly_chart(fig_not_conv_compare, use_container_width=True)
    
    with reason_tab3:
        st.subheader("未转化客户原因分析（有效但未成客户）")
        
        subtab1, subtab2, subtab3 = st.tabs(["📊 柱状图分析", "🥧 饼图分析", "🔗 桑基图"])
        
        with subtab1:
            fig_not_client_bar = create_reason_chart(not_client_reasons_data, "未转化客户原因", "bar")
            st.plotly_chart(fig_not_client_bar, use_container_width=True)
            
        with subtab2:
            fig_not_client_pie = create_reason_chart(not_client_reasons_data, "未转化客户原因", "pie")
            st.plotly_chart(fig_not_client_pie, use_container_width=True)
            
        with subtab3:
            fig_not_client_sankey = create_sankey_diagram(not_client_reasons_data, "未转化客户原因分布")
            st.plotly_chart(fig_not_client_sankey, use_container_width=True)
        
        fig_not_client_compare = create_comparison_chart(not_client_reasons_data, "各城市未转化客户原因对比")
        st.plotly_chart(fig_not_client_compare, use_container_width=True)
    
    with reason_tab4:
        st.subheader("未到访原因分析（客户但未到访）")
        
        subtab1, subtab2, subtab3 = st.tabs(["📊 柱状图分析", "🥧 饼图分析", "🔗 桑基图"])
        
        with subtab1:
            fig_not_visit_bar = create_reason_chart(not_visit_reasons_data, "未到访原因", "bar")
            st.plotly_chart(fig_not_visit_bar, use_container_width=True)
            
        with subtab2:
            fig_not_visit_pie = create_reason_chart(not_visit_reasons_data, "未到访原因", "pie")
            st.plotly_chart(fig_not_visit_pie, use_container_width=True)
            
        with subtab3:
            fig_not_visit_sankey = create_sankey_diagram(not_visit_reasons_data, "未到访原因分布")
            st.plotly_chart(fig_not_visit_sankey, use_container_width=True)
        
        fig_not_visit_compare = create_comparison_chart(not_visit_reasons_data, "各城市未到访原因对比")
        st.plotly_chart(fig_not_visit_compare, use_container_width=True)

    # ==================== 线索量对比 - Plotly饼图 ====================
    st.header("🔢 线索量分布")
    
    leads_data = [cities_data[city][0] for city in cities]
    
    fig_pie = px.pie(
        values=leads_data,
        names=cities,
        title='各城市线索量占比',
        color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label+value')
    st.plotly_chart(fig_pie, use_container_width=True)

# 显示图表
generate_charts()

# 刷新按钮
if st.sidebar.button("🔄 刷新图表"):
    generate_charts()

st.sidebar.markdown("---")
st.sidebar.success("🔍 未转化分析现在有四个维度的深度分析！")
