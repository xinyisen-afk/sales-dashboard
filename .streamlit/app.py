import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from collections import defaultdict
import numpy as np

# 网页标题和配置
st.set_page_config(page_title="本月销售数据分析系统", layout="wide")
st.title("🎯 本月销售与广告数据分析系统")

# 定义数据文件路径
DATA_FILE = 'standard_data.json'
cities = ['从化', '中山', '江门', '南沙二园', '佛山']
stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

# =======================================================
# 1. 数据加载与序列化函数
# =======================================================

# 默认空数据结构 (更新 creatives_data 字段)
EMPTY_DATA_STRUCTURE = {
    'cities_data': {city: [0]*6 for city in cities},
    'reason_labels': {
        'invalid': ['空号错号', '无人接听', '拒绝沟通', '信息错误'],
        'not_converted': ['需求不符', '预算不足', '竞品选择', '时机不对'],
        'not_client': ['价格问题', '服务担忧', '方案不符', '跟进中'],
        'not_visit': ['时间冲突', '距离太远', '兴趣减弱', '其他安排'],
        'not_deal': ['价格太贵', '被竞品抢走', '资金问题', '决策延迟']
    },
    'reasons_data': defaultdict(dict),
    'cost_per_lead': 320,
    # 更新默认素材数据结构：ID 拆分为 Creative Name 和 Creative ID
    'creatives_data': [
        {"Creative Name": "Default_1", "Creative ID": "A001", "Cost": 0, "Leads": 0, "Valid Leads": 0, "Clients": 0, "Visits": 0, "Deals": 0}
    ]
}

def load_standard_data():
    """尝试加载多月份数据，并设置默认 session state"""
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 确保每个月份都有 creatives_data 字段，并兼容旧的 'ID' 字段
            for month in data:
                if 'creatives_data' not in data[month]:
                    data[month]['creatives_data'] = EMPTY_DATA_STRUCTURE['creatives_data']
                else:
                    # 兼容性处理：如果数据中只有旧的 'ID' 字段，将其拆分为新的两个字段
                    for creative in data[month]['creatives_data']:
                        if 'Creative Name' not in creative and 'ID' in creative:
                            name, id_val = creative['ID'], creative['ID'] # 简单处理：名称和ID初始都等于旧ID
                            if '_' in creative['ID']: # 尝试按约定格式拆分
                                parts = creative['ID'].split('_', 1)
                                name, id_val = parts[0], parts[1]
                            creative['Creative Name'] = name
                            creative['Creative ID'] = id_val
                            del creative['ID']
                        # 确保所有必需的新字段存在
                        if 'Creative Name' not in creative: creative['Creative Name'] = 'Unknown'
                        if 'Creative ID' not in creative: creative['Creative ID'] = 'Unknown'
                            
            st.session_state.all_months_data = data
            st.sidebar.success("✅ 已加载多月份标准数据。")
    except FileNotFoundError:
        st.sidebar.error(f"⚠️ 警告：未找到 {DATA_FILE} 文件。创建默认结构。")
        st.session_state.all_months_data = {"October": EMPTY_DATA_STRUCTURE}
    except json.JSONDecodeError:
        st.sidebar.error(f"⚠️ 警告：{DATA_FILE} 文件格式错误。使用默认结构。")
        st.session_state.all_months_data = {"October": EMPTY_DATA_STRUCTURE}

def serialize_data_for_export():
    """将当前的 session state 中的所有月份数据整理成 JSON 格式"""
    
    data_to_save = {}
    for month, month_data in st.session_state.all_months_data.items():
        data_to_save[month] = month_data.copy()
        if isinstance(data_to_save[month].get('reasons_data'), defaultdict):
            data_to_save[month]['reasons_data'] = dict(data_to_save[month]['reasons_data'])

    return json.dumps(data_to_save, ensure_ascii=False, indent=4)

# 应用启动时，立即加载数据
if 'all_months_data' not in st.session_state:
    load_standard_data()

# ==================== 2. 核心函数定义 (图表和原因输入) ====================

# 未转化原因数据输入互动化函数 (保持不变)
def create_reason_inputs(current_data, stage_key, stage_title, reason_count=4):
    """创建互动式的流失原因标签和数量输入"""
    
    st.subheader(stage_title)
    
    # 1. 原因标签名称
    st.markdown("##### 📌 **原因标签设置 (影响所有城市)**")
    label_cols = st.columns(reason_count)
    current_labels = []
    
    current_default_labels = current_data['reason_labels'].get(stage_key, [''] * 4)
    
    for i in range(reason_count):
        label = label_cols[i].text_input(
            f"原因 {i+1} 名称", 
            value=current_default_labels[i] if len(current_default_labels) > i else '',
            key=f"label_{current_data['month']}_{stage_key}_{i}"
        )
        current_labels.append(label)
    current_data['reason_labels'][stage_key] = current_labels 
    
    # 2. 各城市流失数量
    st.markdown("##### 🔢 **各城市流失数量**")
    
    new_reason_data_for_stage = {} 
    
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(reason_count)
        
        city_initial_data = current_data['reasons_data'].get(stage_key, {}).get(city, {})
        city_reason_data = {} 
        
        for i in range(reason_count):
            label = current_labels[i] 
            initial_value = city_initial_data.get(label, 0)
            
            value = cols[i].number_input(
                f"{label} ({city})", 
                value=initial_value, 
                key=f"{current_data['month']}_{stage_key}_{city}_{i}",
                min_value=0,
                label_visibility="collapsed" 
            )
            if label:
                city_reason_data[label] = value
                
        new_reason_data_for_stage[city] = city_reason_data
        
    current_data['reasons_data'][stage_key] = new_reason_data_for_stage

# Plotly 图表函数 (漏斗图, 销售部分，保持不变)
def create_beautiful_funnel(city_data, city_name, stages):
    """创建美观的垂直漏斗图"""
    values = city_data
    color_schemes = {
        '从化': ['#FF6B6B', '#FF8E8E', '#FFB1B1', '#FFD4D4', '#FFE8E8', '#FFF5F5'],
        '中山': ['#4ECDC4', '#88D8D0', '#A8E6DD', '#C8F3EC', '#E1F8F5', '#F0FCFA'],
        '江门': ['#45B7D1', '#7BC9E0', '#9AD6E8', '#B9E3F0', '#D4EDF7', '#EAF6FB'],
        '南沙二园': ['#96CEB4', '#B4E0C8', '#D2F0DC', '#E8F8F0', '#F2FBF4', '#F7FDF9'], 
        '佛山': ['#FFD700', '#FFE64D', '#FFF099', '#FFF7CC', '#FFFBF0', '#FFFDF8'] 
    }
    colors = color_schemes.get(city_name, px.colors.sequential.Blues)
    text_colors = ["white"] * 3 + ["black"] * 3
    
    fig = go.Figure(go.Funnel(
        y=stages, x=values, textposition="inside", textinfo="value+percent initial",
        textfont=dict(size=12, color=text_colors, weight="bold"),
        marker=dict(color=colors[:len(values)], line=dict(width=2, color="darkgray")),
        connector=dict(line=dict(color="rgba(128,128,128,0.5)", width=2, dash="dot")),
        opacity=0.85
    ))
    fig.update_layout(
        title={'text': f"<b>{city_name}转化漏斗</b>",'x': 0.5, 'xanchor': 'center','font': {'size': 16, 'color': '#2C3E50'}},
        plot_bgcolor='rgba(248,248,248,0.8)', paper_bgcolor='white', font=dict(size=11), height=450,
        margin=dict(t=60, b=40, l=60, r=40), showlegend=False
    )
    return fig

# Plotly 图表函数 (流失原因柱状图和饼图, 保持不变)
def create_simple_reason_chart(reasons_data_for_stage, title, cities):
    """创建多城市流失原因柱状图分析，显示0值的原因名称"""
    
    cols_count = 3
    rows_count = int(np.ceil(len(cities) / cols_count))
    
    fig = make_subplots(rows=rows_count, cols=cols_count, 
                        subplot_titles=[f'{city}{title}' for city in cities],
                        horizontal_spacing=0.1, vertical_spacing=0.2)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for i, city in enumerate(cities):
        city_data = reasons_data_for_stage.get(city, {})
        valid_data = {k: v for k, v in city_data.items() if k}
        reasons = list(valid_data.keys())
        counts = list(valid_data.values())
        
        row_idx = (i // cols_count) + 1
        col_idx = (i % cols_count) + 1
        
        if reasons:
            fig.add_trace(
                go.Bar(name=city, y=reasons, x=counts, orientation='h', marker_color=colors[:len(reasons)],
                       text=counts, textposition='auto', showlegend=False),
                row=row_idx, col=col_idx
            )
        fig.update_xaxes(title_text="数量", row=row_idx, col=col_idx)
    
    fig.update_layout(height=rows_count * 400, showlegend=False, title_text=f"<b>{title}分析</b>", title_x=0.5)
    return fig

def create_pie_chart_for_reason(reasons_data_for_stage, title, cities):
    """创建多城市流失原因饼图分析"""
    
    cols_count = 3
    rows_count = int(np.ceil(len(cities) / cols_count))

    fig = make_subplots(rows=rows_count, cols=cols_count, subplot_titles=[f'{city}{title}占比' for city in cities],
                        specs=[[{"type": "pie"}] * cols_count] * rows_count)
    
    for i, city in enumerate(cities):
        city_data = reasons_data_for_stage.get(city, {})
        valid_data = {k: v for k, v in city_data.items() if v > 0 and k}
        reasons = list(valid_data.keys())
        counts = list(valid_data.values())
        
        row_idx = (i // cols_count) + 1
        col_idx = (i % cols_count) + 1
        
        if counts:
            fig.add_trace(
                go.Pie(labels=reasons, values=counts, name=city, textinfo='percent+label',
                       showlegend=False, hole=0.4),
                row=row_idx, col=col_idx
            )
    
    fig.update_layout(height=rows_count * 400, showlegend=False, title_text=f"<b>{title}占比分析</b>", title_x=0.5)
    return fig

# 新增：素材漏斗图创建函数
def create_creative_funnel(creative_data, creative_name):
    """创建素材转化漏斗图"""
    stages_names = ["线索量", "有效线索", "客户数", "到访数", "成交数"]
    values = [
        creative_data['Leads'], creative_data['Valid Leads'], 
        creative_data['Clients'], creative_data['Visits'], creative_data['Deals']
    ]
    
    colors = px.colors.sequential.Plasma_r[:len(values)]
    text_colors = ["white"] * 3 + ["black"] * 2
    
    fig = go.Figure(go.Funnel(
        y=stages_names, x=values, textposition="inside", textinfo="value+percent initial",
        textfont=dict(size=12, color=text_colors, weight="bold"),
        marker=dict(color=colors, line=dict(width=2, color="darkgray")),
        connector=dict(line=dict(color="rgba(128,128,128,0.5)", width=2, dash="dot")),
        opacity=0.85
    ))
    fig.update_layout(
        title={'text': f"<b>{creative_name} 转化漏斗</b>",'x': 0.5, 'xanchor': 'center','font': {'size': 16, 'color': '#2C3E50'}},
        plot_bgcolor='rgba(248,248,248,0.8)', paper_bgcolor='white', font=dict(size=11), height=450,
        margin=dict(t=60, b=40, l=60, r=40), showlegend=False
    )
    return fig

# =======================================================
# 3. 销售数据总览看板函数 (保持不变)
# =======================================================

def generate_sales_charts(current_data):
    
    cities_data = current_data['cities_data']
    reasons_data = current_data['reasons_data']
    cost_per_lead = current_data['cost_per_lead']
    
    # ------------------- 汇总看板 (Summary Dashboard) -------------------
    col1, col2 = st.columns([3, 2])
    with col1:
        st.header("📈 数据汇总看板")
        
        # 辅助函数：计算并格式化成本/率
        def calculate_metrics(total_leads, valid_leads, clients, visits, deals, total_cost):
            valid_rate = (valid_leads / total_leads * 100) if total_leads > 0 else 0
            valid_lead_cost = total_cost / valid_leads if valid_leads > 0 else 0
            client_cost = total_cost / clients if clients > 0 else 0
            visit_cost = total_cost / visits if visits > 0 else 0
            deal_cost = total_cost / deals if deals > 0 else 0
            
            return {
                '线索有效率': f"{valid_rate:.1f}%",
                '有效线索成本': f"¥{valid_lead_cost:,.0f}" if valid_lead_cost > 0 else "/",
                '客户成本': f"¥{client_cost:,.0f}" if client_cost > 0 else "/",
                '到访成本': f"¥{visit_cost:,.0f}" if visit_cost > 0 else "/",
                '成交成本': f"¥{deal_cost:,.0f}" if deal_cost > 0 else "/"
            }
        
        # 1. 计算汇总数据
        total_leads_agg = sum(cities_data.get(city, [0]*6)[0] for city in cities)
        valid_leads_agg = sum(cities_data.get(city, [0]*6)[2] for city in cities)
        clients_agg = sum(cities_data.get(city, [0]*6)[3] for city in cities)
        visits_agg = sum(cities_data.get(city, [0]*6)[4] for city in cities)
        deals_agg = sum(cities_data.get(city, [0]*6)[5] for city in cities)
        total_cost_agg = total_leads_agg * cost_per_lead
        
        summary_data = []

        # 2. 添加 '汇总' 行
        agg_metrics = calculate_metrics(total_leads_agg, valid_leads_agg, clients_agg, visits_agg, deals_agg, total_cost_agg)
        aggregate_row = {
            '城市': '**汇总**',
            '线索总量': total_leads_agg,
            '**到访数量**': visits_agg,
            '**消费总数**': f"¥{total_cost_agg:,.0f}",
            **agg_metrics 
        }
        summary_data.append(aggregate_row)
        
        # 3. 循环添加城市数据
        for city in cities:
             values = cities_data.get(city, [0]*6)
             
             total_leads = values[0]
             valid_leads = values[2]
             clients = values[3]
             visits = values[4] 
             deals = values[5]
             
             total_cost = total_leads * cost_per_lead
             
             city_metrics = calculate_metrics(total_leads, valid_leads, clients, visits, deals, total_cost)
             
             summary_data.append({
                 '城市': city,
                 '线索总量': total_leads,
                 '**到访数量**': visits,
                 '**消费总数**': f"¥{total_cost:,.0f}",
                 **city_metrics
             })
        
        summary_df = pd.DataFrame(summary_data)
        new_cols_order = ['城市', '线索总量', '**到访数量**', '**消费总数**', '线索有效率', '有效线索成本', '客户成本', '到访成本', '成交成本']
        summary_df = summary_df[new_cols_order]
        
        st.dataframe(summary_df, use_container_width=True)

    # ------------------- 总转化漏斗图 -------------------
    with col2:
        st.header("🔢 线索量分布")
        leads_data = [cities_data.get(city, [0])[0] for city in cities]
        
        fig_pie = px.pie(
            values=leads_data, names=cities, title='', 
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD700']
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=350, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    # ------------------- 转化漏斗 -------------------
    st.header("🎨 转化漏斗分析")
    tab1, tab2 = st.tabs(["🎯 垂直漏斗图", "📊 水平视图"])
    
    city_display_groups = [cities[:3], cities[3:]] 
    
    with tab1:
        st.subheader("垂直漏斗图")
        for group in city_display_groups:
            cols = st.columns(len(group))
            for i, city in enumerate(group):
                city_data = cities_data.get(city, [0]*6)
                with cols[i]:
                    fig_funnel = create_beautiful_funnel(city_data, city, stages)
                    st.plotly_chart(fig_funnel, use_container_width=True)
    
    with tab2:
        st.subheader("水平漏斗图")
        for group in city_display_groups:
            cols = st.columns(len(group))
            for i, city in enumerate(group):
                city_data = cities_data.get(city, [0]*6)
                with cols[i]:
                    # create_horizontal_funnel 函数未给出，这里仅调用垂直图
                    # fig_h = create_horizontal_funnel(city_data, city, stages)
                    # 避免报错，使用垂直图替代
                    fig_h = create_beautiful_funnel(city_data, city, stages) 
                    st.plotly_chart(fig_h, use_container_width=True)
    
    # ------------------- 未转化客户深度分析 (流失原因图表) -------------------
    st.header("🔍 未转化客户深度分析 - 柱状图")
    reason_tab_bar1, reason_tab_bar2, reason_tab_bar3, reason_tab_bar4, reason_tab_bar5 = st.tabs([
        "❌ 无效线索原因", "📞 未转化线索原因", "👥 未转化客户原因", "🚫 未到访原因", "💸 未成交原因"
    ])
    
    with reason_tab_bar1:
        fig_invalid_bar = create_simple_reason_chart(reasons_data['invalid'], "无效线索原因", cities)
        st.plotly_chart(fig_invalid_bar, use_container_width=True)
    
    with reason_tab_bar2:
        fig_not_converted_bar = create_simple_reason_chart(reasons_data['not_converted'], "未转化线索原因", cities)
        st.plotly_chart(fig_not_converted_bar, use_container_width=True)
        
    with reason_tab_bar3:
        fig_not_client_bar = create_simple_reason_chart(reasons_data['not_client'], "未转化客户原因", cities)
        st.plotly_chart(fig_not_client_bar, use_container_width=True)

    with reason_tab_bar4:
        fig_not_visit_bar = create_simple_reason_chart(reasons_data['not_visit'], "未到访原因", cities)
        st.plotly_chart(fig_not_visit_bar, use_container_width=True)
        
    with reason_tab_bar5:
        fig_not_deal_bar = create_simple_reason_chart(reasons_data['not_deal'], "未成交原因", cities)
        st.plotly_chart(fig_not_deal_bar, use_container_width=True)

    st.header("🥧 未转化客户深度分析 - 饼图")
    pie_tab1, pie_tab2, pie_tab3, pie_tab4, pie_tab5 = st.tabs([
        "❌ 无效线索**原因分布**", "📞 未转化线索**原因分布**", "👥 未转化客户**原因分布**", "🚫 未到访**原因分布**", "💸 未成交**原因分布**"
    ])
    
    with pie_tab1:
        fig_invalid_pie = create_pie_chart_for_reason(reasons_data['invalid'], "无效线索原因", cities)
        st.plotly_chart(fig_invalid_pie, use_container_width=True)
    
    with pie_tab2:
        fig_not_converted_pie = create_pie_chart_for_reason(reasons_data['not_converted'], "未转化线索原因", cities)
        st.plotly_chart(fig_not_converted_pie, use_container_width=True)

    with pie_tab3:
        fig_not_client_pie = create_pie_chart_for_reason(reasons_data['not_client'], "未转化客户原因", cities)
        st.plotly_chart(fig_not_client_pie, use_container_width=True)
        
    with pie_tab4:
        fig_not_visit_pie = create_pie_chart_for_reason(reasons_data['not_visit'], "未到访原因", cities)
        st.plotly_chart(fig_not_visit_pie, use_container_width=True)

    with pie_tab5:
        fig_not_deal_pie = create_pie_chart_for_reason(reasons_data['not_deal'], "未成交原因", cities)
        st.plotly_chart(fig_not_deal_pie, use_container_width=True)


# =======================================================
# 4. 广告素材分析看板函数 (重构以支持新需求)
# =======================================================

def generate_creative_charts(current_data):
    st.header("🖼️ 广告素材效果分析")
    
    creatives_data = current_data.get('creatives_data', [])
    if not creatives_data:
        st.warning("当前月份没有广告素材数据。请前往 '⚙️ 数据编辑' 标签页添加数据。")
        return

    df = pd.DataFrame(creatives_data)

    # 确保列名是可用的
    required_cols = ["Creative Name", "Creative ID", "Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"数据中缺少必需的列: {col}，请检查数据结构。")
            return
            
    # 计算核心指标
    df['CPL'] = df['Cost'] / df['Leads'].replace(0, np.nan)
    df['Valid CPL'] = df['Cost'] / df['Valid Leads'].replace(0, np.nan)
    df['Client CPL'] = df['Cost'] / df['Clients'].replace(0, np.nan)
    df['Visit CPL'] = df['Cost'] / df['Visits'].replace(0, np.nan) # 新增到访成本
    df['Deal CPL'] = df['Cost'] / df['Deals'].replace(0, np.nan) # 新增成交成本
    
    df['Valid Rate'] = (df['Valid Leads'] / df['Leads'].replace(0, np.nan)) * 100
    df['Client Rate'] = (df['Clients'] / df['Valid Leads'].replace(0, np.nan)) * 100
    df['Visit Rate'] = (df['Visits'] / df['Clients'].replace(0, np.nan)) * 100 
    df['Deal Rate'] = (df['Deals'] / df['Visits'].replace(0, np.nan)) * 100
    
    # 核心指标中文映射
    metric_map = {
        'Creative Name': '素材简称',
        'Creative ID': '素材ID',
        'Cost': '总成本',
        'Leads': '线索量',
        'Valid Leads': '有效线索',
        'Clients': '客户数',
        'Visits': '到访数',
        'Deals': '成交数',
        'CPL': '线索成本 (CPL)',
        'Valid CPL': '有效线索成本',
        'Client CPL': '客户获取成本',
        'Visit CPL': '到访成本',
        'Deal CPL': '成交成本',
        'Valid Rate': '线索有效率',
        'Client Rate': '有效线索转化率',
        'Visit Rate': '客户到访率', 
        'Deal Rate': '到访成交率'
    }

    # 格式化显示
    format_mapping = {
        'Cost': '¥{:,.0f}'.format,
        'CPL': '¥{:,.0f}'.format,
        'Valid CPL': '¥{:,.0f}'.format,
        'Client CPL': '¥{:,.0f}'.format,
        'Visit CPL': '¥{:,.0f}'.format,
        'Deal CPL': '¥{:,.0f}'.format,
        'Valid Rate': '{:.1f}%'.format,
        'Client Rate': '{:.1f}%'.format,
        'Visit Rate': '{:.1f}%'.format, 
        'Deal Rate': '{:.1f}%'.format
    }

    # 1. 核心数据表
    st.subheader("核心指标数据表")
    display_df = df.copy()
    
    cols_to_display = ["Creative Name", "Creative ID", "Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals", 
                       "Valid Rate", "Client Rate", "Visit Rate", "Deal Rate", 
                       "CPL", "Valid CPL", "Client CPL", "Visit CPL", "Deal CPL"]

    # 应用格式化
    for col, func in format_mapping.items():
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: func(x) if pd.notna(x) else '/')
    
    # 更改列名为中文
    display_df = display_df[cols_to_display].rename(columns=metric_map)
    
    st.dataframe(display_df, use_container_width=True)

    # 2. 成本指标对比图 (新增)
    st.header("📊 素材成本指标对比")
    cost_metrics = ['CPL', 'Valid CPL', 'Client CPL', 'Visit CPL', 'Deal CPL']
    
    df_cost_melt = df.melt(
        id_vars='Creative Name',
        value_vars=cost_metrics,
        var_name='成本类型',
        value_name='成本金额'
    ).dropna(subset=['成本金额']) # 移除成本为 NaN 的行

    df_cost_melt['成本类型'] = df_cost_melt['成本类型'].map(metric_map)

    fig_costs = px.bar(
        df_cost_melt,
        x='Creative Name',
        y='成本金额',
        color='成本类型',
        barmode='group',
        text='成本金额',
        title='各素材分阶段成本对比',
        color_discrete_map={
            metric_map['CPL']: '#00bfa5',
            metric_map['Valid CPL']: '#4E79A7',
            metric_map['Client CPL']: '#E15759',
            metric_map['Visit CPL']: '#F28E2B',
            metric_map['Deal CPL']: '#76B7B2',
        }
    )
    
    fig_costs.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside')
    fig_costs.update_layout(
        height=500,
        xaxis_title=metric_map['Creative Name'],
        yaxis_title="成本金额 (元)",
        uniformtext_minsize=8, 
        uniformtext_mode='hide',
        legend_title_text='成本类型'
    )
    st.plotly_chart(fig_costs, use_container_width=True)


    # 3. 转化率对比图 (保持不变)
    st.subheader("转化率对比")
    
    df_melt_rate = df[['Creative Name', 'Valid Rate', 'Client Rate', 'Visit Rate', 'Deal Rate']].rename(columns=metric_map).melt(
        id_vars=metric_map['Creative Name'], 
        value_vars=[metric_map['Valid Rate'], metric_map['Client Rate'], metric_map['Visit Rate'], metric_map['Deal Rate']],
        var_name='指标', 
        value_name='百分比'
    )
                      
    fig_rate = px.bar(df_melt_rate, x=metric_map['Creative Name'], y='百分比', color='指标', barmode='group',
                      title='各环节转化率对比',
                      color_discrete_map={
                          metric_map['Valid Rate']: '#1E88E5', 
                          metric_map['Client Rate']: '#FFC107', 
                          metric_map['Visit Rate']: '#009688', 
                          metric_map['Deal Rate']: '#9C27B0' 
                      })
    fig_rate.update_layout(height=450, yaxis_title="转化率 (%)", xaxis_title=metric_map['Creative Name'])
    st.plotly_chart(fig_rate, use_container_width=True)


    # 4. 每个素材的漏斗图 (新增)
    st.header("🎯 单素材转化漏斗分析")
    
    num_creatives = len(df)
    cols_per_row = 3
    num_rows = int(np.ceil(num_creatives / cols_per_row))
    
    # 创建一个空的图表列表，然后分行展示
    funnel_cols = st.columns(cols_per_row)
    
    for i, row in df.iterrows():
        creative_name = row['Creative Name']
        
        # 确定当前素材在哪一行哪一列
        col_index = i % cols_per_row
        
        with funnel_cols[col_index]:
            fig_funnel = create_creative_funnel(row, creative_name)
            st.plotly_chart(fig_funnel, use_container_width=True)


# ==================== 5. 侧边栏及主应用入口 (集成标签页) ====================

# 1. 侧边栏：定义当前月份和添加新月份
st.sidebar.markdown("---")
st.sidebar.header("🗓️ 月份管理")

available_months = sorted(st.session_state.all_months_data.keys(), reverse=True)
current_month = st.sidebar.radio("选择/编辑月份:", available_months, key="month_selector")
st.session_state.current_month = current_month

current_data = st.session_state.all_months_data[current_month]
current_data['month'] = current_month # 注入月份名，用于 key

# 2. 侧边栏 - 数据输入 UI (使用当前月份的数据)
st.sidebar.header(f"📊 {current_month}核心数据输入")
current_data['cost_per_lead'] = st.sidebar.number_input(
    "单条线索成本(元)", 
    value=current_data.get('cost_per_lead', 320), 
    min_value=0, 
    key=f'{current_month}_sidebar_cost_per_lead'
)

# 城市数据输入 - 使用折叠器组织 (保持不变)
with st.sidebar.expander(f"🏙️ {current_month}城市转化数据", expanded=True):
    for city in cities:
        st.write(f"**{city}转化数据**")
        cols = st.columns(2)
        values = []
        for i, stage in enumerate(stages):
            col_idx = i % 2
            initial_value = current_data['cities_data'].get(city, [0]*6)[i]
            
            value = cols[col_idx].number_input(
                f"{stage}",
                value=initial_value,
                key=f"{current_month}_{city}_{stage}",
                min_value=0
            )
            values.append(value)
        current_data['cities_data'][city] = values
        
with st.sidebar.expander(f"🔍 {current_month}流失原因数据", expanded=False):
    create_reason_inputs(current_data, 'invalid', "❌ 无效线索原因", reason_count=4)
    create_reason_inputs(current_data, 'not_converted', "📞 未转化线索原因", reason_count=4)
    create_reason_inputs(current_data, 'not_client', "👥 未转化客户原因", reason_count=4)
    create_reason_inputs(current_data, 'not_visit', "🚫 未到访原因", reason_count=4)
    create_reason_inputs(current_data, 'not_deal', "💸 未成交原因", reason_count=4)

# 添加新月份功能 (保持不变)
st.sidebar.markdown("---")
new_month = st.sidebar.text_input("新增月份名称 (例如：November)")
if st.sidebar.button("➕ 创建新月份数据"):
    if new_month and new_month not in st.session_state.all_months_data:
        new_data = {
            'cities_data': {city: [0]*6 for city in cities},
            'reason_labels': {k: list(v) for k, v in EMPTY_DATA_STRUCTURE['reason_labels'].items()},
            'reasons_data': defaultdict(dict),
            'cost_per_lead': current_data.get('cost_per_lead', 320),
            'creatives_data': EMPTY_DATA_STRUCTURE['creatives_data']
        }
        st.session_state.all_months_data[new_month] = new_data
        st.experimental_rerun()

# 6. 主应用入口 (集成标签页)
sales_tab, creative_tab, edit_tab = st.tabs([
    "💰 销售数据总览", 
    "🖼️ 广告素材效果分析",
    "⚙️ 数据编辑"
])

with sales_tab:
    generate_sales_charts(current_data)

with creative_tab:
    generate_creative_charts(current_data)
    
with edit_tab: # 数据编辑标签页 (更新了素材字段)
    st.header(f"⚙️ {current_month} - 广告素材数据编辑")
    st.warning("请在此处编辑、添加或删除广告素材的数据。编辑完成后，数据会自动更新到分析页面。")
    
    # 广告素材数据输入
    df_creatives = pd.DataFrame(current_data.get('creatives_data', EMPTY_DATA_STRUCTURE['creatives_data']))
    
    # 定义可编辑的列类型 (更新为 Creative Name 和 Creative ID)
    column_config = {
        "Creative Name": st.column_config.TextColumn("素材简称", required=True),
        "Creative ID": st.column_config.TextColumn("素材ID", required=True),
        "Cost": st.column_config.NumberColumn("成本 (¥)", required=True, min_value=0),
        "Leads": st.column_config.NumberColumn("线索量", required=True, min_value=0),
        "Valid Leads": st.column_config.NumberColumn("有效线索", required=True, min_value=0),
        "Clients": st.column_config.NumberColumn("客户数", required=True, min_value=0),
        "Visits": st.column_config.NumberColumn("到访数", required=True, min_value=0),
        "Deals": st.column_config.NumberColumn("成交数", required=True, min_value=0),
    }
    
    # 确保只显示新字段并使用新的列配置
    display_cols = ["Creative Name", "Creative ID", "Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals"]
    
    # 兼容性处理：如果加载的数据有旧的ID字段，需要过滤掉
    if 'ID' in df_creatives.columns:
        df_creatives = df_creatives.drop(columns=['ID'])

    edited_df = st.data_editor(
        df_creatives[display_cols],
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key=f"{current_month}_creative_data_editor_main"
    )
    
    # 将编辑后的 DataFrame 转换回 list of dicts 存入 current_data
    current_data['creatives_data'] = edited_df.to_dict('records')
    
# 7. 导出面板 (导出所有月份数据) (保持不变)
st.sidebar.markdown("---")
st.sidebar.header("🔑 开发者数据导出")
st.sidebar.info("请在修改数据或标签后，点击此按钮，复制 **所有月份** 的 JSON 内容用于更新 GitHub 上的 `standard_data.json` 文件。")

if st.sidebar.button("✨ 生成最新的 standard_data.json 内容", type="primary"):
    json_output = serialize_data_for_export()
    
    st.header("📋 请复制以下 JSON 内容")
    st.warning("完成后，请前往 GitHub 仓库，编辑 standard_data.json 文件，并用以下内容覆盖它。")
    st.code(json_output, language='json', height=500)
    st.toast("JSON 内容已生成在主页面！", icon='🎉')
