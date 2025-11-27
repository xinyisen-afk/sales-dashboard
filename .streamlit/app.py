import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 网页标题
st.set_page_config(page_title="销售数据分析系统", layout="wide")
st.title("🎯 三城市销售数据分析系统")

# 初始化session state
if 'cities_data' not in st.session_state:
    st.session_state.cities_data = {}
if 'reasons_data' not in st.session_state:
    st.session_state.reasons_data = {}

# 侧边栏 - 数据输入
st.sidebar.header("📊 核心数据输入")
cost_per_lead = st.sidebar.number_input("单条线索成本(元)", value=320, min_value=0)

# 城市数据输入 - 使用折叠器组织
with st.sidebar.expander("🏙️ 各城市转化数据", expanded=True):
    cities = ['从化', '中山', '江门']
    stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

    default_values = {
        '从化': [21, 19, 17, 8, 4, 2],
        '中山': [30, 25, 20, 11, 5, 1], 
        '江门': [6, 6, 5, 5, 1, 0]
    }

    for city in cities:
        st.write(f"**{city}转化数据**")
        cols = st.columns(2)
        values = []
        for i, stage in enumerate(stages):
            col_idx = i % 2
            value = cols[col_idx].number_input(
                f"{stage}", 
                value=default_values[city][i],
                key=f"{city}_{stage}",
                min_value=0
            )
            values.append(value)
        st.session_state.cities_data[city] = values

# 未转化原因数据 - 使用折叠器组织
with st.sidebar.expander("🔍 未转化原因数据", expanded=False):
    
    # 1. 无效线索原因
    st.subheader("❌ 无效线索原因")
    invalid_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        invalid_data[city] = {
            '空号错号': cols[0].number_input(f"{city}-空号错号", value=3, key=f"invalid_{city}_1"),
            '无人接听': cols[1].number_input(f"{city}-无人接听", value=2, key=f"invalid_{city}_2"),
            '拒绝沟通': cols[0].number_input(f"{city}-拒绝沟通", value=1, key=f"invalid_{city}_3"),
            '信息错误': cols[1].number_input(f"{city}-信息错误", value=1, key=f"invalid_{city}_4")
        }
    st.session_state.reasons_data['invalid'] = invalid_data

    # 2. 未转化线索原因
    st.subheader("📞 未转化线索原因")
    not_converted_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        not_converted_data[city] = {
            '需求不符': cols[0].number_input(f"{city}-需求不符", value=4, key=f"not_conv_{city}_1"),
            '预算不足': cols[1].number_input(f"{city}-预算不足", value=3, key=f"not_conv_{city}_2"),
            '竞品选择': cols[0].number_input(f"{city}-竞品选择", value=2, key=f"not_conv_{city}_3"),
            '时机不对': cols[1].number_input(f"{city}-时机不对", value=1, key=f"not_conv_{city}_4")
        }
    st.session_state.reasons_data['not_converted'] = not_converted_data

    # 3. 未转化客户原因
    st.subheader("👥 未转化客户原因")
    not_client_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        not_client_data[city] = {
            '价格问题': cols[0].number_input(f"{city}-价格问题", value=4, key=f"not_client_{city}_1"),
            '服务担忧': cols[1].number_input(f"{city}-服务担忧", value=2, key=f"not_client_{city}_2"),
            '方案不符': cols[0].number_input(f"{city}-方案不符", value=2, key=f"not_client_{city}_3"),
            '跟进中': cols[1].number_input(f"{city}-跟进中", value=1, key=f"not_client_{city}_4")
        }
    st.session_state.reasons_data['not_client'] = not_client_data

    # 4. 未到访原因
    st.subheader("🚫 未到访原因")
    not_visit_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        not_visit_data[city] = {
            '时间冲突': cols[0].number_input(f"{city}-时间冲突", value=2, key=f"not_visit_{city}_1"),
            '距离太远': cols[1].number_input(f"{city}-距离太远", value=1, key=f"not_visit_{city}_2"),
            '兴趣减弱': cols[0].number_input(f"{city}-兴趣减弱", value=1, key=f"not_visit_{city}_3"),
            '其他安排': cols[1].number_input(f"{city}-其他安排", value=0, key=f"not_visit_{city}_4")
        }
    st.session_state.reasons_data['not_visit'] = not_visit_data

    # 5. 未成交原因 - 新增
    st.subheader("💸 未成交原因")
    not_deal_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        not_deal_data[city] = {
            '价格太贵': cols[0].number_input(f"{city}-价格太贵", value=2, key=f"not_deal_{city}_1"),
            '被竞品抢走': cols[1].number_input(f"{city}-被竞品抢走", value=1, key=f"not_deal_{city}_2"),
            '资金问题': cols[0].number_input(f"{city}-资金问题", value=1, key=f"not_deal_{city}_3"),
            '决策延迟': cols[1].number_input(f"{city}-决策延迟", value=0, key=f"not_deal_{city}_4")
        }
    st.session_state.reasons_data['not_deal'] = not_deal_data

# ==================== 漏斗图函数定义 ====================
def create_beautiful_funnel(city_data, city_name, stages):
    """创建美观的漏斗图"""
    values = city_data
    
    color_schemes = {
        '从化': ['#FF6B6B', '#FF8E8E', '#FFB1B1', '#FFD4D4', '#FFE8E8', '#FFF5F5'],
        '中山': ['#4ECDC4', '#88D8D0', '#A8E6DD', '#C8F3EC', '#E1F8F5', '#F0FCFA'],
        '江门': ['#45B7D1', '#7BC9E0', '#9AD6E8', '#B9E3F0', '#D4EDF7', '#EAF6FB']
    }
    
    colors = color_schemes.get(city_name, px.colors.sequential.Blues)
    
    # 根据背景色深浅自动选择文字颜色
    text_colors = []
    for color in colors[:len(values)]:
        # 简单的亮度计算，选择对比度足够的文字颜色
        if color in ['#FF6B6B', '#FF8E8E', '#4ECDC4', '#45B7D1']:
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
    """创建水平漏斗图"""
    values = city_data
    
    horizontal_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD700', '#DDA0DD']
    
    # 确保数据有效
    valid_values = [v if v > 0 else 0.1 for v in values]  # 避免除零错误
    
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

def create_simple_reason_chart(reason_data, title):
    """创建简单的柱状图分析"""
    fig = make_subplots(rows=1, cols=3, subplot_titles=[f'{city}{title}' for city in cities])
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for i, city in enumerate(cities):
        city_data = reason_data[city]
        reasons = list(city_data.keys())
        counts = list(city_data.values())
        
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
    
    fig.update_layout(
        height=400,
        showlegend=False,
        title_text=f"<b>{title}分析</b>",
        title_x=0.5
    )
    return fig
    
# ==================== 主图表生成函数 ====================
def generate_charts():
    cities_data = st.session_state.cities_data
    reasons_data = st.session_state.reasons_data

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

    # ==================== 成本分析 ====================
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

    # ==================== 转化漏斗 ====================
    st.header("🎨 转化漏斗分析")
    
    tab1, tab2 = st.tabs(["🎯 垂直漏斗图", "📊 水平视图"])
    
    with tab1:
        st.subheader("垂直漏斗图")
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
        st.subheader("水平漏斗图")
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

    # ==================== 未转化客户深度分析 ====================
    st.header("🔍 未转化客户深度分析")
    
    reason_tab1, reason_tab2, reason_tab3, reason_tab4, reason_tab5 = st.tabs([
        "❌ 无效线索原因", 
        "📞 未转化线索原因", 
        "👥 未转化客户原因", 
        "🚫 未到访原因",
        "💸 未成交原因"
    ])
    
    with reason_tab1:
        st.subheader("无效线索原因分析")
        fig_invalid_bar = create_simple_reason_chart(reasons_data['invalid'], "无效线索原因")
        st.plotly_chart(fig_invalid_bar, use_container_width=True)
    
    with reason_tab2:
        st.subheader("未转化线索原因分析（接通但无效）")
        fig_not_conv_bar = create_simple_reason_chart(reasons_data['not_converted'], "未转化线索原因")
        st.plotly_chart(fig_not_conv_bar, use_container_width=True)
    
    with reason_tab3:
        st.subheader("未转化客户原因分析（有效但未成客户）")
        fig_not_client_bar = create_simple_reason_chart(reasons_data['not_client'], "未转化客户原因")
        st.plotly_chart(fig_not_client_bar, use_container_width=True)
    
    with reason_tab4:
        st.subheader("未到访原因分析（客户但未到访）")
        fig_not_visit_bar = create_simple_reason_chart(reasons_data['not_visit'], "未到访原因")
        st.plotly_chart(fig_not_visit_bar, use_container_width=True)
    
    with reason_tab5:
        st.subheader("未成交原因分析（到访但未成交）")
        fig_not_deal_bar = create_simple_reason_chart(reasons_data['not_deal'], "未成交原因")
        st.plotly_chart(fig_not_deal_bar, use_container_width=True)

    # ==================== 底部汇总图表 ====================
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

# 操作提示
st.sidebar.markdown("---")
st.sidebar.info("""
**💡 使用提示：**
1. 点击展开器修改数据
2. 数据会自动保存和更新
3. 使用标签页切换不同视图
4. 所有图表都是交互式的
""")

st.sidebar.success("✅ 系统优化完成！")
