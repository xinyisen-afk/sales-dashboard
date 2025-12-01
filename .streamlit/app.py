import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 网页标题
st.set_page_config(page_title="产业园销售数据分析系统", layout="wide")
st.title("🏭 三城市产业园销售漏斗分析系统")

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
    stages = ['线索总量', '接通数', '有效线索', '意向客户', '到访客户', '成交客户']

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

# 未转化原因数据 - 按照优化后的五阶段模型
with st.sidebar.expander("🔍 未转化原因数据", expanded=False):
    
    # 1. 未接通原因
    st.subheader("📞 未接通原因")
    no_connect_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        no_connect_data[city] = {
            '号码问题': cols[0].number_input(f"{city}-号码问题", value=2, key=f"no_connect_{city}_1", min_value=0),
            '多次呼转': cols[1].number_input(f"{city}-多次呼转", value=2, key=f"no_connect_{city}_2", min_value=0),
            '直接拒绝': cols[0].number_input(f"{city}-直接拒绝", value=1, key=f"no_connect_{city}_3", min_value=0),
            '非目标联系人': cols[1].number_input(f"{city}-非目标联系人", value=1, key=f"no_connect_{city}_4", min_value=0)
        }
    st.session_state.reasons_data['no_connect'] = no_connect_data

    # 2. 无效线索原因
    st.subheader("❌ 无效线索原因")
    invalid_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        invalid_data[city] = {
            '明确无需求': cols[0].number_input(f"{city}-明确无需求", value=1, key=f"invalid_{city}_1", min_value=0),
            '需求严重不匹配': cols[1].number_input(f"{city}-需求严重不匹配", value=1, key=f"invalid_{city}_2", min_value=0),
            '非目标客群': cols[0].number_input(f"{city}-非目标客群", value=0, key=f"invalid_{city}_3", min_value=0),
            '信息无效': cols[1].number_input(f"{city}-信息无效", value=0, key=f"invalid_{city}_4", min_value=0)
        }
    st.session_state.reasons_data['invalid'] = invalid_data

    # 3. 未转意向客户原因
    st.subheader("🎯 未转意向客户原因")
    not_intention_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        not_intention_data[city] = {
            '区位抗性': cols[0].number_input(f"{city}-区位抗性", value=4, key=f"not_intention_{city}_1", min_value=0),
            '产品不匹配': cols[1].number_input(f"{city}-产品不匹配", value=3, key=f"not_intention_{city}_2", min_value=0),
            '意向度低/周期长': cols[0].number_input(f"{city}-意向度低/周期长", value=2, key=f"not_intention_{city}_3", min_value=0),
            '客户失联': cols[1].number_input(f"{city}-客户失联", value=1, key=f"not_intention_{city}_4", min_value=0)
        }
    st.session_state.reasons_data['not_intention'] = not_intention_data

    # 4. 未到访原因
    st.subheader("🚗 未到访原因")
    not_visit_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        not_visit_data[city] = {
            '选择竞品': cols[0].number_input(f"{city}-选择竞品", value=2, key=f"not_visit_{city}_1", min_value=0),
            '产品/时机不符': cols[1].number_input(f"{city}-产品/时机不符", value=1, key=f"not_visit_{city}_2", min_value=0),
            '邀约失败': cols[0].number_input(f"{city}-邀约失败", value=1, key=f"not_visit_{city}_3", min_value=0),
            '区位一票否决': cols[1].number_input(f"{city}-区位一票否决", value=0, key=f"not_visit_{city}_4", min_value=0)
        }
    st.session_state.reasons_data['not_visit'] = not_visit_data

    # 5. 未成交原因
    st.subheader("💼 未成交原因")
    not_deal_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(2)
        not_deal_data[city] = {
            '价格因素': cols[0].number_input(f"{city}-价格因素", value=2, key=f"not_deal_{city}_1", min_value=0),
            '竞争失利': cols[1].number_input(f"{city}-竞争失利", value=1, key=f"not_deal_{city}_2", min_value=0),
            '客户内部决策变动': cols[0].number_input(f"{city}-客户内部决策变动", value=1, key=f"not_deal_{city}_3", min_value=0),
            '硬性条件不符': cols[1].number_input(f"{city}-硬性条件不符", value=0, key=f"not_deal_{city}_4", min_value=0)
        }
    st.session_state.reasons_data['not_deal'] = not_deal_data

# ==================== 新增分析函数 ====================
def create_loss_analysis_chart():
    """创建未转化原因总体分析图"""
    fig = make_subplots(
        rows=2, 
        cols=3,
        subplot_titles=[
            '从化-未转化原因分布', '中山-未转化原因分布', '江门-未转化原因分布',
            '从化-各阶段流失率', '中山-各阶段流失率', '江门-各阶段流失率'
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # 颜色方案
    stage_colors = ['#FF6B6B', '#FF8E53', '#FFD166', '#06D6A0', '#118AB2']
    stage_labels = ['未接通', '无效线索', '未转意向', '未到访', '未成交']
    
    for i, city in enumerate(cities):
        # 第一行：未转化原因分布饼图
        stage_data = []
        labels = []
        
        for stage in ['no_connect', 'invalid', 'not_intention', 'not_visit', 'not_deal']:
            data = st.session_state.reasons_data[stage][city]
            total = sum(data.values())
            stage_data.append(total)
        
        # 只显示有数据的部分
        valid_indices = [idx for idx, val in enumerate(stage_data) if val > 0]
        valid_data = [stage_data[idx] for idx in valid_indices]
        valid_labels = [stage_labels[idx] for idx in valid_indices]
        valid_colors = [stage_colors[idx] for idx in valid_indices]
        
        if sum(valid_data) > 0:
            fig.add_trace(
                go.Pie(
                    labels=valid_labels,
                    values=valid_data,
                    marker=dict(colors=valid_colors),
                    hole=0.4,
                    showlegend=False,
                    textinfo='percent+label'
                ),
                row=1, col=i+1
            )
        
        # 第二行：各阶段流失率柱状图
        cities_data = st.session_state.cities_data[city]
        if len(cities_data) >= 6:
            loss_rates = []
            for j in range(len(cities_data)-1):
                if cities_data[j] > 0:
                    loss_rate = (cities_data[j] - cities_data[j+1]) / cities_data[j] * 100
                    loss_rates.append(loss_rate)
                else:
                    loss_rates.append(0)
            
            loss_stages = ['线索→接通', '接通→有效', '有效→意向', '意向→到访', '到访→成交']
            
            fig.add_trace(
                go.Bar(
                    x=loss_stages,
                    y=loss_rates,
                    marker_color='#45B7D1',
                    name='流失率',
                    text=[f'{rate:.1f}%' for rate in loss_rates],
                    textposition='auto'
                ),
                row=2, col=i+1
            )
            fig.update_yaxes(title_text="流失率(%)", range=[0, 100], row=2, col=i+1)
    
    fig.update_layout(
        height=800,
        showlegend=False,
        title_text="<b>未转化客户深度分析总览</b>",
        title_x=0.5
    )
    return fig

def create_cross_city_comparison():
    """创建跨城市原因对比图"""
    all_reasons_data = {}
    
    # 收集所有原因类型
    for stage in ['no_connect', 'invalid', 'not_intention', 'not_visit', 'not_deal']:
        stage_data = st.session_state.reasons_data[stage]
        for city in cities:
            for reason, count in stage_data[city].items():
                if reason not in all_reasons_data:
                    all_reasons_data[reason] = {city_val: 0 for city_val in cities}
                all_reasons_data[reason][city] = count
    
    # 选择TOP 10原因
    reason_totals = {reason: sum(data.values()) for reason, data in all_reasons_data.items()}
    top_reasons = sorted(reason_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    for i, city in enumerate(cities):
        city_counts = [all_reasons_data[reason][city] for reason, _ in top_reasons]
        fig.add_trace(go.Bar(
            name=city,
            y=[reason for reason, _ in top_reasons],
            x=city_counts,
            orientation='h',
            marker_color=colors[i],
            text=city_counts,
            textposition='auto'
        ))
    
    fig.update_layout(
        title="<b>Top 10未转化原因 - 三城市对比</b>",
        barmode='group',
        height=500,
        xaxis_title="数量",
        yaxis_title="未转化原因",
        showlegend=True
    )
    
    return fig

def create_stage_analysis_tabs():
    """创建各阶段详细分析标签页"""
    stage_configs = {
        'no_connect': {
            'title': '📞 未接通分析',
            'description': '首次接触未能与关键人建立有效沟通',
            'color': '#FF6B6B'
        },
        'invalid': {
            'title': '❌ 无效线索分析',
            'description': '接通后判断无跟进价值的线索',
            'color': '#FF8E53'
        },
        'not_intention': {
            'title': '🎯 未转意向分析',
            'description': '已沟通但未能激发进一步了解的欲望',
            'color': '#FFD166'
        },
        'not_visit': {
            'title': '🚗 未到访分析',
            'description': '有意向但未能促成现场看房',
            'color': '#06D6A0'
        },
        'not_deal': {
            'title': '💼 未成交分析',
            'description': '到访后未能签约成交',
            'color': '#118AB2'
        }
    }
    
    tabs = st.tabs([config['title'] for config in stage_configs.values()])
    
    for i, (stage_key, config) in enumerate(stage_configs.items()):
        with tabs[i]:
            st.markdown(f"<h3 style='color:{config['color']}'>{config['title']}</h3>", unsafe_allow_html=True)
            st.caption(config['description'])
            
            # 创建两个图表：分布图和城市对比图
            col1, col2 = st.columns(2)
            
            with col1:
                # 各城市该阶段原因分布
                stage_data = st.session_state.reasons_data[stage_key]
                fig1 = make_subplots(rows=1, cols=3, subplot_titles=[f'{city}' for city in cities])
                
                for j, city in enumerate(cities):
                    reasons = list(stage_data[city].keys())
                    counts = list(stage_data[city].values())
                    
                    fig1.add_trace(
                        go.Bar(
                            x=reasons,
                            y=counts,
                            marker_color=config['color'],
                            showlegend=False,
                            text=counts,
                            textposition='auto'
                        ),
                        row=1, col=j+1
                    )
                
                fig1.update_layout(
                    height=400,
                    title_text=f"<b>各城市{config['title']}分布</b>",
                    showlegend=False
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # 该阶段原因堆叠柱状图
                reasons = list(stage_data[cities[0]].keys())
                fig2 = go.Figure()
                
                for city in cities:
                    counts = list(stage_data[city].values())
                    fig2.add_trace(go.Bar(
                        name=city,
                        x=reasons,
                        y=counts,
                        text=counts,
                        textposition='auto'
                    ))
                
                fig2.update_layout(
                    barmode='group',
                    height=400,
                    title_text=f"<b>{config['title']} - 三城市对比</b>",
                    xaxis_title="原因类型",
                    yaxis_title="数量",
                    showlegend=True
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # 显示关键洞察
            st.markdown("### 📊 关键洞察")
            total_counts = {}
            for city in cities:
                total = sum(stage_data[city].values())
                total_counts[city] = total
            
            # 找出最主要的原因
            for city in cities:
                if total_counts[city] > 0:
                    main_reason = max(stage_data[city], key=stage_data[city].get)
                    main_count = stage_data[city][main_reason]
                    percentage = (main_count / total_counts[city]) * 100
                    
                    st.info(f"**{city}**：最主要原因为 **{main_reason}**，占比 **{percentage:.1f}%** ({main_count}/{total_counts[city]})")

# ==================== 原有的漏斗图函数 ====================
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

# ==================== 主图表生成函数 ====================
def generate_charts():
    cities_data = st.session_state.cities_data
    reasons_data = st.session_state.reasons_data

    # ==================== 汇总看板表格 + 线索量分布 ====================
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
                '有效线索成本': f"¥{valid_lead_cost:.0f}" if valid_lead_cost > 0 else "/",
                '客户成本': f"¥{client_cost:.0f}" if client_cost > 0 else "/",
                '到访成本': f"¥{visit_cost:.0f}" if visit_cost > 0 else "/",
                '成交成本': f"¥{deal_cost:.0f}" if deal_cost > 0 else "/"
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
    
    with col2:
        st.header("🔢 线索量分布")
        leads_data = [cities_data[city][0] for city in cities]
        
        fig_pie = px.pie(
            values=leads_data,
            names=cities,
            title='',
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

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

    # ==================== 新增：未转化客户深度分析 ====================
    st.header("🔍 未转化客户深度分析")
    st.markdown("基于五阶段转化漏斗模型：**未接通 → 无效线索 → 未转意向 → 未到访 → 未成交**")
    
    # 总览图表
    st.subheader("📊 总体分析")
    fig_loss_overall = create_loss_analysis_chart()
    st.plotly_chart(fig_loss_overall, use_container_width=True)
    
    # 跨城市对比
    st.subheader("🌍 跨城市原因对比")
    fig_cross_city = create_cross_city_comparison()
    st.plotly_chart(fig_cross_city, use_container_width=True)
    
    # 各阶段详细分析
    st.subheader("📋 各阶段详细分析")
    create_stage_analysis_tabs()
    
    # ==================== 洞察与建议 ====================
    st.header("💡 洞察与建议")
    
    # 计算关键指标
    insights_data = []
    for city in cities:
        values = cities_data[city]
        total_leads = values[0]
        deals = values[5]
        
        # 计算总转化率
        overall_rate = (deals / total_leads * 100) if total_leads > 0 else 0
        
        # 找出最大的流失点
        max_loss_stage = ''
        max_loss_rate = 0
        
        for i in range(len(values)-1):
            if values[i] > 0:
                loss_rate = (values[i] - values[i+1]) / values[i] * 100
                if loss_rate > max_loss_rate:
                    max_loss_rate = loss_rate
                    max_loss_stage = stages[i]
        
        # 找出主要未转化原因
        main_reason = ''
        main_reason_count = 0
        for stage_data in reasons_data.values():
            city_data = stage_data[city]
            for reason, count in city_data.items():
                if count > main_reason_count:
                    main_reason_count = count
                    main_reason = reason
        
        insights_data.append({
            '城市': city,
            '总转化率': f"{overall_rate:.1f}%",
            '主要流失点': max_loss_stage,
            '流失率': f"{max_loss_rate:.1f}%",
            '主要未转化原因': main_reason if main_reason_count > 0 else "暂无数据"
        })
    
    insights_df = pd.DataFrame(insights_data)
    st.dataframe(insights_df, use_container_width=True)
    
    # 基于洞察提供建议
    st.markdown("### 🎯 优化建议")
    
    for city in cities:
        values = cities_data[city]
        total_leads = values[0]
        deals = values[5]
        
        if deals == 0:
            st.warning(f"**{city}**：暂无成交，建议重点检查 **线索质量** 和 **销售跟进策略**，确保有效线索的筛选和跟进效率。")
        elif total_leads > 0:
            overall_rate = deals / total_leads * 100
            if overall_rate < 10:
                st.warning(f"**{city}**：转化率偏低 ({overall_rate:.1f}%)，建议优化转化漏斗中的薄弱环节。")
            elif overall_rate > 20:
                st.success(f"**{city}**：转化表现良好 ({overall_rate:.1f}%)，建议保持当前策略并尝试扩大线索规模。")
            else:
                st.info(f"**{city}**：转化率中等 ({overall_rate:.1f}%)，有提升空间，建议针对性优化流失率最高的环节。")

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
5. 关注"洞察与建议"获取优化方向
""")

st.sidebar.success("✅ 系统优化完成！基于五阶段漏斗模型")
