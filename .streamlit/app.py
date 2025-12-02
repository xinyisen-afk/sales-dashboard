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
st.info("💡 **重要提示：** 数据更改将实时更新图表，但不会自动保存到文件。请点击侧边栏的 **'生成最新的 JSON 数据'** 按钮，复制内容并手动更新您的 `standard_data.json` 文件。")

# 定义数据文件路径
DATA_FILE = 'standard_data.json'
cities = ['从化', '中山', '江门', '南沙二园', '佛山']
stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

# 默认月份 (十一月)
DEFAULT_MONTH = "November"

# =======================================================
# 1. 数据加载与序列化函数
# =======================================================

# 默认空数据结构
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
    'creatives_data': [
        {"Creative Name": "Default_1", "Creative ID": "A001", "Link": "http://example.com", "Cost": 0, "Leads": 0, "Valid Leads": 0, "Clients": 0, "Visits": 0, "Deals": 0}
    ]
}

def load_standard_data():
    """尝试加载多月份数据，并设置默认 session state"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            
            for month in data:
                month_data = data[month]
                if 'creatives_data' not in month_data:
                    month_data['creatives_data'] = EMPTY_DATA_STRUCTURE['creatives_data'][:]
                
                for creative in month_data['creatives_data']:
                    for key in ["Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals"]:
                        try:
                            creative[key] = float(creative.get(key, 0))
                        except:
                            creative[key] = 0
                            
            st.session_state.all_months_data = data
            st.sidebar.success("✅ 已加载多月份标准数据。")
    except FileNotFoundError:
        st.sidebar.error(f"⚠️ 警告：未找到 {DATA_FILE} 文件。创建默认结构。")
        st.session_state.all_months_data = {DEFAULT_MONTH: EMPTY_DATA_STRUCTURE}
    except json.JSONDecodeError:
        st.sidebar.error(f"⚠️ 警告：{DATA_FILE} 文件格式错误。使用默认结构。")
        st.session_state.all_months_data = {DEFAULT_MONTH: EMPTY_DATA_STRUCTURE}
    except Exception as e:
        st.sidebar.error(f"⚠️ 警告：加载数据时发生未知错误：{e}。使用默认结构。")
        st.session_state.all_months_data = {DEFAULT_MONTH: EMPTY_DATA_STRUCTURE}


def serialize_data_for_export():
    """将当前的 session state 中的所有月份数据整理成 JSON 格式"""
    data_to_save = {}
    for month, month_data in st.session_state.all_months_data.items():
        data_to_save[month] = month_data.copy()
        
        # 确保 defaultdict 被转换为标准 dict 才能序列化
        if isinstance(data_to_save[month].get('reasons_data'), defaultdict):
            data_to_save[month]['reasons_data'] = dict(data_to_save[month]['reasons_data'])
        
        if 'reasons_data' in data_to_save[month]:
            for stage_key in data_to_save[month]['reasons_data']:
                if isinstance(data_to_save[month]['reasons_data'][stage_key], defaultdict):
                    data_to_save[month]['reasons_data'][stage_key] = dict(data_to_save[month]['reasons_data'][stage_key])
                
                for city_key in data_to_save[month]['reasons_data'][stage_key]:
                     if isinstance(data_to_save[month]['reasons_data'][stage_key][city_key], defaultdict):
                          data_to_save[month]['reasons_data'][stage_key][city_key] = dict(data_to_save[month]['reasons_data'][stage_key][city_key])

    return json.dumps(data_to_save, ensure_ascii=False, indent=4)

# 应用启动时，立即加载数据
if 'all_months_data' not in st.session_state:
    load_standard_data()

# ==================== 2. 核心函数定义 (图表和原因输入) ====================

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
    
    new_reason_data_for_stage = defaultdict(dict) 
    
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
                city_reason_data[label] = int(value) 
                
        new_reason_data_for_stage[city] = city_reason_data
        
    current_data['reasons_data'][stage_key] = dict(new_reason_data_for_stage)

# --- [所有图表函数保持不变] ---

def create_beautiful_funnel(city_data, city_name, stages):
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

def create_horizontal_funnel(city_data, city_name, stages):
    values = city_data
    horizontal_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD700', '#DDA0DD']
    valid_values = [v if v > 0 else 0.1 for v in values]
    
    fig = go.Figure(go.Funnel(
        y=stages, x=valid_values, orientation="h", textposition="inside", textinfo="value+percent initial",
        textfont=dict(size=11, color="white", weight="bold"),
        marker=dict(color=horizontal_colors[:len(values)], line=dict(width=2, color="white")),
        opacity=0.9
    ))
    fig.update_layout(
        title={'text': f"<b>{city_name}水平视图</b>",'x': 0.5, 'xanchor': 'center', 'font': {'size': 14, 'color': '#2C3E50'}},
        plot_bgcolor='rgba(248,248,248,0.8)', paper_bgcolor='white', height=400,
        margin=dict(t=50, b=40, l=80, r=40)
    )
    return fig

def create_simple_reason_chart(reasons_data_for_stage, title, cities):
    cols_count = 3
    rows_count = int(np.ceil(len(cities) / cols_count))
    
    fig = make_subplots(rows=rows_count, cols=cols_count, 
                        subplot_titles=[f'{city}{title}' for city in cities],
                        horizontal_spacing=0.1, vertical_spacing=0.2)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for i, city in enumerate(cities):
        city_data = reasons_data_for_stage.get(city, {})
        valid_data = {k: v for k, v in city_data.items() if k and v > 0} 
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
    
    fig.update_layout(height=max(400, rows_count * 400), showlegend=False, title_text=f"<b>{title}分析</b>", title_x=0.5)
    return fig

def create_pie_chart_for_reason(reasons_data_for_stage, title, cities):
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
    
    fig.update_layout(height=max(400, rows_count * 400), showlegend=False, title_text=f"<b>{title}占比分析</b>", title_x=0.5)
    return fig

def create_creative_funnel(creative_data, creative_name):
    stages_names = ["线索量", "有效线索", "客户数", "到访数", "成交数"]
    values = [
        creative_data.get('Leads', 0), creative_data.get('Valid Leads', 0), 
        creative_data.get('Clients', 0), creative_data.get('Visits', 0), creative_data.get('Deals', 0)
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

# --- [图表函数结束] ---


# --- [generate_sales_charts 和 generate_creative_charts 保持不变] ---

def generate_sales_charts(current_data):
    cities_data = current_data['cities_data']
    reasons_data = current_data['reasons_data']
    cost_per_lead = current_data.get('cost_per_lead', 320)
    
    col1, col2 = st.columns([3, 2])
    with col1:
        st.header("📈 数据汇总看板")
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
        
        total_leads_agg = sum(cities_data.get(city, [0]*6)[0] for city in cities)
        valid_leads_agg = sum(cities_data.get(city, [0]*6)[2] for city in cities)
        clients_agg = sum(cities_data.get(city, [0]*6)[3] for city in cities)
        visits_agg = sum(cities_data.get(city, [0]*6)[4] for city in cities)
        deals_agg = sum(cities_data.get(city, [0]*6)[5] for city in cities)
        total_cost_agg = total_leads_agg * cost_per_lead
        
        summary_data = []
        agg_metrics = calculate_metrics(total_leads_agg, valid_leads_agg, clients_agg, visits_agg, deals_agg, total_cost_agg)
        aggregate_row = {
            '城市': '**汇总**', '线索总量': total_leads_agg, '**到访数量**': visits_agg,
            '**消费总数**': f"¥{total_cost_agg:,.0f}", **agg_metrics 
        }
        summary_data.append(aggregate_row)
        
        for city in cities:
             values = cities_data.get(city, [0]*6)
             total_leads, valid_leads, clients, visits, deals = values[0], values[2], values[3], values[4], values[5]
             total_cost = total_leads * cost_per_lead
             city_metrics = calculate_metrics(total_leads, valid_leads, clients, visits, deals, total_cost)
             summary_data.append({
                 '城市': city, '线索总量': total_leads, '**到访数量**': visits,
                 '**消费总数**': f"¥{total_cost:,.0f}", **city_metrics
             })
        
        summary_df = pd.DataFrame(summary_data)
        new_cols_order = ['城市', '线索总量', '**到访数量**', '**消费总数**', '线索有效率', '有效线索成本', '客户成本', '到访成本', '成交成本']
        summary_df = summary_df[new_cols_order]
        st.dataframe(summary_df, use_container_width=True)

    with col2:
        st.header("🔢 线索量分布")
        leads_data = [cities_data.get(city, [0])[0] for city in cities]
        fig_pie = px.pie(values=leads_data, names=cities, title='', color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD700'])
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=350, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.header("🎨 转化漏斗分析")
    tab1, tab2 = st.tabs(["🎯 垂直漏斗图", "📊 水平视图"])
    city_display_groups = [cities[:3], cities[3:]] 
    
    with tab1:
        st.subheader("垂直漏斗图")
        for group in city_display_groups:
            cols = st.columns(len(group))
            for i, city in enumerate(group):
                with cols[i]:
                    st.plotly_chart(create_beautiful_funnel(cities_data.get(city, [0]*6), city, stages), use_container_width=True)
    
    with tab2:
        st.subheader("水平漏斗图")
        for group in city_display_groups:
            cols = st.columns(len(group))
            for i, city in enumerate(group):
                with cols[i]:
                    st.plotly_chart(create_horizontal_funnel(cities_data.get(city, [0]*6), city, stages), use_container_width=True)
    
    st.header("🔍 未转化客户深度分析 - 柱状图")
    tabs = st.tabs(["❌ 无效线索原因", "📞 未转化线索原因", "👥 未转化客户原因", "🚫 未到访原因", "💸 未成交原因"])
    keys = ['invalid', 'not_converted', 'not_client', 'not_visit', 'not_deal']
    titles = ["无效线索原因", "未转化线索原因", "未转化客户原因", "未到访原因", "未成交原因"]
    
    for tab, key, title in zip(tabs, keys, titles):
        with tab:
            st.plotly_chart(create_simple_reason_chart(reasons_data.get(key, {}), title, cities), use_container_width=True)

    st.header("🥧 未转化客户深度分析 - 饼图")
    pie_tabs = st.tabs([f"❌ {titles[0]}分布", f"📞 {titles[1]}分布", f"👥 {titles[2]}分布", f"🚫 {titles[3]}分布", f"💸 {titles[4]}分布"])
    
    for tab, key, title in zip(pie_tabs, keys, titles):
        with tab:
            st.plotly_chart(create_pie_chart_for_reason(reasons_data.get(key, {}), title, cities), use_container_width=True)


def generate_creative_charts(current_data):
    st.header("🖼️ 广告素材效果分析")
    creatives_data = current_data.get('creatives_data', [])
    if not creatives_data:
        st.warning("当前月份没有广告素材数据。请前往 '⚙️ 数据编辑' 标签页添加数据。")
        return

    df = pd.DataFrame(creatives_data)
    numeric_cols = ["Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    df['CPL'] = df['Cost'] / df['Leads'].replace(0, np.nan)
    df['Valid CPL'] = df['Cost'] / df['Valid Leads'].replace(0, np.nan)
    df['Client CPL'] = df['Cost'] / df['Clients'].replace(0, np.nan)
    df['Visit CPL'] = df['Cost'] / df['Visits'].replace(0, np.nan)
    df['Deal CPL'] = df['Cost'] / df['Deals'].replace(0, np.nan)
    
    df['Valid Rate'] = (df['Valid Leads'] / df['Leads'].replace(0, np.nan)) * 100
    df['Client Rate'] = (df['Clients'] / df['Valid Leads'].replace(0, np.nan)) * 100
    df['Visit Rate'] = (df['Visits'] / df['Clients'].replace(0, np.nan)) * 100 
    df['Deal Rate'] = (df['Deals'] / df['Visits'].replace(0, np.nan)) * 100
    
    metric_map = {
        'Creative Name': '素材简称', 'Creative ID': '素材ID', 'Link': '素材链接', 'Cost': '总成本',
        'Leads': '线索量', 'Valid Leads': '有效线索', 'Clients': '客户数', 'Visits': '到访数', 'Deals': '成交数',
        'CPL': '线索成本 (CPL)', 'Valid CPL': '有效线索成本', 'Client CPL': '客户获取成本',
        'Visit CPL': '到访成本', 'Deal CPL': '成交成本', 'Valid Rate': '线索有效率',
        'Client Rate': '有效线索转化率', 'Visit Rate': '客户到访率', 'Deal Rate': '到访成交率'
    }

    format_mapping = {
        'Cost': '¥{:,.0f}'.format, 'CPL': '¥{:,.0f}'.format, 'Valid CPL': '¥{:,.0f}'.format, 
        'Client CPL': '¥{:,.0f}'.format, 'Visit CPL': '¥{:,.0f}'.format, 'Deal CPL': '¥{:,.0f}'.format,
        'Valid Rate': '{:.1f}%'.format, 'Client Rate': '{:.1f}%'.format, 'Visit Rate': '{:.1f}%'.format, 
        'Deal Rate': '{:.1f}%'.format
    }

    st.subheader("核心指标数据表")
    display_df = df.copy()
    cols_to_display = ["Creative Name", "Creative ID", "Link", "Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals", 
                       "Valid Rate", "Client Rate", "Visit Rate", "Deal Rate", 
                       "CPL", "Valid CPL", "Client CPL", "Visit CPL", "Deal CPL"] 

    for col, func in format_mapping.items():
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: func(x) if pd.notna(x) and x is not None else '/')
    
    display_df = display_df[cols_to_display].rename(columns=metric_map)
    st.dataframe(display_df, use_container_width=True)

    st.header("📊 素材成本指标对比")
    cost_metrics = ['CPL', 'Valid CPL', 'Client CPL', 'Visit CPL', 'Deal CPL']
    
    df_cost_melt = df.melt(id_vars='Creative Name', value_vars=cost_metrics, var_name='成本类型', value_name='成本金额').dropna(subset=['成本金额']) 
    df_cost_melt['成本类型'] = df_cost_melt['成本类型'].map(lambda x: metric_map.get(x, x))
    df_cost_melt = df_cost_melt[df_cost_melt['成本金额'] != np.inf]

    fig_costs = px.bar(df_cost_melt, x='Creative Name', y='成本金额', color='成本类型', barmode='group', text='成本金额', title='各素材分阶段成本对比')
    fig_costs.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside')
    fig_costs.update_layout(height=500, xaxis_title=metric_map['Creative Name'], yaxis_title="成本金额 (元)", legend_title_text='成本类型')
    st.plotly_chart(fig_costs, use_container_width=True)

    st.subheader("转化率对比")
    df_melt_rate = df[['Creative Name', 'Valid Rate', 'Client Rate', 'Visit Rate', 'Deal Rate']].rename(columns=metric_map).melt(
        id_vars=metric_map['Creative Name'], 
        value_vars=[metric_map['Valid Rate'], metric_map['Client Rate'], metric_map['Visit Rate'], metric_map['Deal Rate']],
        var_name='指标', value_name='百分比'
    )
                      
    fig_rate = px.bar(df_melt_rate, x=metric_map['Creative Name'], y='百分比', color='指标', barmode='group', title='各环节转化率对比')
    fig_rate.update_layout(height=450, yaxis_title="转化率 (%)", xaxis_title=metric_map['Creative Name'])
    st.plotly_chart(fig_rate, use_container_width=True)

    st.header("🎯 单素材转化漏斗分析")
    cols_per_row = 3
    funnel_cols = st.columns(cols_per_row)
    for i, row in df.iterrows():
        with funnel_cols[i % cols_per_row]:
            st.plotly_chart(create_creative_funnel(row, row['Creative Name']), use_container_width=True)

# --- [generate_sales_charts 和 generate_creative_charts 结束] ---


# ==================== 5. 侧边栏及主应用入口 ====================

# 1. 侧边栏：定义当前月份和添加新月份
st.sidebar.markdown("---")
st.sidebar.header("🗓️ 月份管理")

available_months = sorted(st.session_state.all_months_data.keys(), reverse=True)
current_month = st.sidebar.radio("选择/编辑月份:", available_months, key="month_selector_sidebar") 
st.session_state.current_month = current_month

current_data = st.session_state.all_months_data[current_month]
current_data['month'] = current_month 

# 2. 侧边栏 - 数据输入 UI
st.sidebar.header(f"📊 {current_month}核心数据输入")
current_data['cost_per_lead'] = st.sidebar.number_input(
    "单条线索成本(元)", 
    value=current_data.get('cost_per_lead', 320), 
    min_value=0, 
    key=f'{current_month}_sidebar_cost_per_lead'
)

# 城市数据输入
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
            values.append(int(value))
        current_data['cities_data'][city] = values
        
# 流失原因输入
with st.sidebar.expander(f"🔍 {current_month}流失原因数据", expanded=False):
    create_reason_inputs(current_data, 'invalid', "❌ 无效线索原因", reason_count=4)
    create_reason_inputs(current_data, 'not_converted', "📞 未转化线索原因", reason_count=4)
    create_reason_inputs(current_data, 'not_client', "👥 未转化客户原因", reason_count=4)
    create_reason_inputs(current_data, 'not_visit', "🚫 未到访原因", reason_count=4)
    create_reason_inputs(current_data, 'not_deal', "💸 未成交原因", reason_count=4)

# 添加新月份功能
st.sidebar.markdown("---")
new_month = st.sidebar.text_input("新增月份名称 (例如：December)", key="new_month_input")
if st.sidebar.button("➕ 创建新月份数据"):
    if new_month and new_month not in st.session_state.all_months_data:
        new_data = {
            'cities_data': {city: [0]*6 for city in cities},
            'reason_labels': {k: list(v) for k, v in EMPTY_DATA_STRUCTURE['reason_labels'].items()},
            'reasons_data': defaultdict(dict),
            'cost_per_lead': current_data.get('cost_per_lead', 320),
            'creatives_data': EMPTY_DATA_STRUCTURE['creatives_data'][:]
        }
        st.session_state.all_months_data[new_month] = new_data
        
        # 强制重新运行以加载新月份 (不需要保存文件，因为是手动流程)
        st.rerun() 

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
    
with edit_tab:
    st.header(f"⚙️ {current_month} - 广告素材数据编辑")
    st.warning("您可以在表格中直接编辑数据，更改将实时更新内存中的图表。")
    
    creative_df = pd.DataFrame(current_data.get('creatives_data', []))
    
    column_config = {
        "Creative Name": st.column_config.TextColumn("素材简称", required=True),
        "Creative ID": st.column_config.TextColumn("素材ID", required=True),
        "Link": st.column_config.TextColumn("素材链接"),
        "Cost": st.column_config.NumberColumn("总成本", min_value=0, format="¥%d"),
        "Leads": st.column_config.NumberColumn("线索量", min_value=0),
        "Valid Leads": st.column_config.NumberColumn("有效线索", min_value=0),
        "Clients": st.column_config.NumberColumn("客户数", min_value=0),
        "Visits": st.column_config.NumberColumn("到访数", min_value=0),
        "Deals": st.column_config.NumberColumn("成交数", min_value=0)
    }

    # 使用 st.data_editor 恢复互动编辑
    edited_df = st.data_editor(
        creative_df,
        column_config=column_config,
        num_rows="dynamic", 
        use_container_width=True,
        key=f"{current_month}_creative_editor"
    )

    # 检查是否有编辑变动并更新 Session State
    if not edited_df.equals(creative_df):
        new_creative_data = edited_df.to_dict('records')
        current_data['creatives_data'] = new_creative_data
        # 仅更新内存，不保存，不rerun

# 7. 开发者面板 - 核心：生成 JSON 数据

st.sidebar.markdown("---")
st.sidebar.header("💾 手动数据持久化")
st.sidebar.info("请在完成所有编辑后，点击下方按钮生成 JSON 代码，并手动复制到您的 `standard_data.json` 文件中。")

# 关键按钮：生成 JSON
if st.sidebar.button("✨ 生成最新的 JSON 数据", type="primary"):
    json_output = serialize_data_for_export()
    
    st.header("📋 请复制以下 JSON 内容（替换 standard_data.json 文件）")
    st.code(json_output, language='json', height=500)
    st.toast("JSON 内容已在主页面生成！", icon='🎉')
