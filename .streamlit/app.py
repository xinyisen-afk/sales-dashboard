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

# 1. 修正：默认月份改为中文（假设十月和十一月是您最常用的月份）
DEFAULT_MONTH_1 = "十一月"
DEFAULT_MONTH_2 = "十二月"
DEFAULT_MONTHS_KEYS = [DEFAULT_MONTH_1, DEFAULT_MONTH_2]


# =======================================================
# 1. 数据加载与序列化函数 (更新：兼容 Creative Theme)
# =======================================================

# 默认空数据结构 (更新: 添加 Creative Theme)
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
    # 🆕 更新：添加 Creative Theme 字段
    'creatives_data': [
        {"Creative Name": "Default_1", "Creative ID": "A001", "Link": "http://example.com", "Cost": 0, "Leads": 0, "Valid Leads": 0, "Clients": 0, "Visits": 0, "Deals": 0, "Creative Theme": "其他"}
    ]
}

def load_standard_data():
    """尝试加载多月份数据，并设置默认 session state"""
    try:
        # 使用 utf-8-sig 以处理可能存在的 BOM
        with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            
            for month in data:
                month_data = data[month]
                if 'creatives_data' not in month_data:
                    month_data['creatives_data'] = EMPTY_DATA_STRUCTURE['creatives_data'][:]
                
                # 确保广告素材数据是数字类型，并添加默认 Creative Theme
                for creative in month_data['creatives_data']:
                    for key in ["Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals"]:
                        try:
                            creative[key] = float(creative.get(key, 0))
                        except:
                            creative[key] = 0
                    if 'Creative Theme' not in creative: # 兼容旧数据
                        creative['Creative Theme'] = '未分类'
                            
            st.session_state.all_months_data = data
            st.sidebar.success("✅ 已加载多月份标准数据。")
    except FileNotFoundError:
        st.sidebar.error(f"⚠️ 警告：未找到 {DATA_FILE} 文件。创建默认结构。")
        st.session_state.all_months_data = {
            DEFAULT_MONTH_1: EMPTY_DATA_STRUCTURE.copy(),
            DEFAULT_MONTH_2: EMPTY_DATA_STRUCTURE.copy()
        }
    except json.JSONDecodeError:
        st.sidebar.error(f"⚠️ 警告：{DATA_FILE} 文件格式错误。使用默认结构。")
        st.session_state.all_months_data = {
            DEFAULT_MONTH_1: EMPTY_DATA_STRUCTURE.copy(),
            DEFAULT_MONTH_2: EMPTY_DATA_STRUCTURE.copy()
        }
    except Exception as e:
        st.sidebar.error(f"⚠️ 警告：加载数据时发生未知错误：{e}。使用默认结构。")
        st.session_state.all_months_data = {
            DEFAULT_MONTH_1: EMPTY_DATA_STRUCTURE.copy(),
            DEFAULT_MONTH_2: EMPTY_DATA_STRUCTURE.copy()
        }


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
        
        # 🆕 确保 creatives_data 中所有字段都存在，以便 JSON 结构统一
        if 'creatives_data' in data_to_save[month]:
            for creative in data_to_save[month]['creatives_data']:
                if 'Creative Theme' not in creative:
                    creative['Creative Theme'] = '未分类'

    return json.dumps(data_to_save, ensure_ascii=False, indent=4)

# 应用启动时，立即加载数据
if 'all_months_data' not in st.session_state:
    load_standard_data()

# ==================== 2. 核心函数定义 (图表和原因输入) (保持不变) ====================

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

# 3. 修正：保留计数为 0 的原因标签
def create_simple_reason_chart(reasons_data_for_stage, title, cities):
    cols_count = 3
    rows_count = int(np.ceil(len(cities) / cols_count))
    
    fig = make_subplots(rows=rows_count, cols=cols_count, 
                        subplot_titles=[f'{city}{title}' for city in cities],
                        horizontal_spacing=0.1, vertical_spacing=0.2)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for i, city in enumerate(cities):
        city_data = reasons_data_for_stage.get(city, {})
        
        # 修正逻辑：保留所有标签，零值用 0 显示
        reasons = []
        counts = []
        for k, v in city_data.items():
            if k: # 排除空标签
                reasons.append(k)
                counts.append(int(v) if v is not None else 0)
        
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
        # 饼图必须过滤掉 0 值，否则 Plotly 会报错或显示异常
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

    df_full = pd.DataFrame(creatives_data)
    numeric_cols = ["Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals"]
    for col in numeric_cols:
        df_full[col] = pd.to_numeric(df_full[col], errors='coerce').fillna(0)

    # 🆕 确保 Creative Theme 列存在并填充默认值
    if 'Creative Theme' not in df_full.columns:
        df_full['Creative Theme'] = '未分类'
    df_full['Creative Theme'] = df_full['Creative Theme'].fillna('未分类') 

    # ----------------------------------------------------
    # 🌟 素材对比选择器
    # ----------------------------------------------------
    all_creative_names = df_full['Creative Name'].tolist()
    
    st.subheader("🔍 素材对比与筛选")
    selected_creatives = st.multiselect(
        "选择要对比的广告素材 (推荐选择 2-4 个进行深度对比)",
        options=all_creative_names,
        default=all_creative_names[:3] if len(all_creative_names) >= 3 else all_creative_names,
        key=f"{current_data['month']}_creative_selector"
    )

    if not selected_creatives:
        st.warning("请至少选择一个素材进行分析。")
        return

    # 根据选择器筛选数据
    df = df_full[df_full['Creative Name'].isin(selected_creatives)].copy()
    
    # ----------------------------------------------------
    # 计算核心指标 
    # ----------------------------------------------------
    df['CPL'] = df['Cost'] / df['Leads'].replace(0, np.nan)
    df['Valid CPL'] = df['Cost'] / df['Valid Leads'].replace(0, np.nan)
    df['Client CPL'] = df['Cost'] / df['Clients'].replace(0, np.nan)
    df['Visit CPL'] = df['Cost'] / df['Visits'].replace(0, np.nan)
    df['Deal CPL'] = df['Cost'] / df['Deals'].replace(0, np.nan)
    
    df['Valid Rate'] = (df['Valid Leads'] / df['Leads'].replace(0, np.nan)) * 100
    df['Client Rate'] = (df['Clients'] / df['Valid Leads'].replace(0, np.nan)) * 100
    df['Visit Rate'] = (df['Visits'] / df['Clients'].replace(0, np.nan)) * 100 
    df['Deal Rate'] = (df['Deals'] / df['Visits'].replace(0, np.nan)) * 100
    
    # ----------------------------------------------------
    # 🌟 评级与标签化计算
    # ----------------------------------------------------

    df_valid = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['Valid CPL', 'Visit Rate', 'Deal CPL'], how='all')

    avg_valid_cpl = df_valid['Valid CPL'].mean() if not df_valid.empty else 0
    avg_visit_rate = df_valid['Visit Rate'].mean() / 100 if not df_valid.empty else 0

    def get_creative_rating(row, avg_cpl, avg_rate):
        if pd.isna(row['Valid CPL']) or pd.isna(row['Visit Rate']):
            return "N/A"
        
        score = 0
        
        if avg_cpl > 0 and row['Valid CPL'] < avg_cpl * 0.8:
            score += 2
        elif avg_cpl > 0 and row['Valid CPL'] < avg_cpl * 1.1:
            score += 1
            
        if avg_rate > 0 and row['Visit Rate'] / 100 > avg_rate * 1.2:
            score += 2
        elif avg_rate > 0 and row['Visit Rate'] / 100 > avg_rate * 0.9:
            score += 1

        if row['Deals'] > 0:
            score += 1
            
        if score >= 4:
            return "⭐⭐⭐⭐"
        elif score >= 2:
            return "⭐⭐⭐"
        elif score >= 1:
            return "⭐⭐"
        else:
            return "⭐"

    def get_efficiency_tag(row, avg_cpl, avg_rate):
        rating = row['Rating']
        if rating == "⭐⭐⭐⭐":
            return "明星素材 (加大预算)"
        elif rating == "⭐":
            if avg_cpl > 0 and row['Valid CPL'] > avg_cpl * 1.5:
                return "成本极高 (立即暂停)"
            elif avg_cpl > 0 and row['Valid CPL'] > avg_cpl * 1.1:
                return "成本过高 (优化创意)"
            elif avg_rate > 0 and row['Visit Rate'] / 100 < avg_rate * 0.7 and row['Valid Leads'] > 0:
                return "到访率低 (线索质量差)"
            return "表现平庸 (观望/测试)"
        return "稳健素材"

    df['Rating'] = df.apply(lambda row: get_creative_rating(row, avg_valid_cpl, avg_visit_rate), axis=1)
    df['Efficiency Tag'] = df.apply(lambda row: get_efficiency_tag(row, avg_valid_cpl, avg_visit_rate), axis=1)

    # ----------------------------------------------------
    # 📝 自动化建议摘要
    # ----------------------------------------------------
    
    st.subheader("💡 投放策略建议摘要")
    
    star_creatives = df[df['Rating'] == "⭐⭐⭐⭐"]
    low_deal_high_cost = df[
        (df['Deal CPL'] == df['Deal CPL'].max()) & (df['Deal CPL'].notna()) & (df['Deals'] > 0)
    ]
    
    summary_points = []
    
    if not star_creatives.empty:
        best_name = star_creatives.iloc[0]['Creative Name']
        summary_points.append(f"🥇 **明星素材：** **{best_name}** 表现出色，其有效线索成本（¥{star_creatives.iloc[0]['Valid CPL']:,.0f}）显著低于平均值。建议**立即增加预算**，进一步放大效果。")
    
    if not low_deal_high_cost.empty:
        worst_name = low_deal_high_cost.iloc[0]['Creative Name']
        worst_cost = low_deal_high_cost.iloc[0]['Deal CPL']
        summary_points.append(f"💸 **高风险素材：** **{worst_name}** 的成交成本高达 **¥{worst_cost:,.0f}**，属于高成本低效区。建议**暂停投放**或彻底优化其创意和定向。")

    low_visit_rate = df[(df['Visit Rate'] == df['Visit Rate'].min()) & (df['Clients'] > 0)]
    if avg_visit_rate > 0 and not low_visit_rate.empty and low_visit_rate.iloc[0]['Visit Rate'] < avg_visit_rate * 100 * 0.5:
        low_rate_name = low_visit_rate.iloc[0]['Creative Name']
        low_rate_value = low_visit_rate.iloc[0]['Visit Rate']
        summary_points.append(f"📉 **转化瓶颈：** 素材 **{low_rate_name}** 的客户到访率仅有 **{low_rate_value:.1f}%**，远低于平均水平。这可能表明其吸引的线索质量差，需关注**素材内容与目标受众的匹配度**。")
        
    if not summary_points:
        summary_points.append("✅ 当前素材表现较为平稳，没有明显的极端优劣情况。建议在成本和转化率平均水平附近进行微调。")

    for point in summary_points:
        st.markdown(f"* {point}")
    
    st.markdown("---")

    # ----------------------------------------------------
    # 📊 数据表格和图表 (只显示筛选后的素材)
    # ----------------------------------------------------
    
    metric_map = {
        'Creative Name': '素材简称', 'Creative ID': '素材ID', 'Link': '素材链接', 'Cost': '总成本',
        'Leads': '线索量', 'Valid Leads': '有效线索', 'Clients': '客户数', 'Visits': '到访数', 'Deals': '成交数',
        'CPL': '线索成本 (CPL)', 'Valid CPL': '有效线索成本', 'Client CPL': '客户获取成本',
        'Visit CPL': '到访成本', 'Deal CPL': '成交成本', 'Valid Rate': '线索有效率',
        'Client Rate': '有效线索转化率', 'Visit Rate': '客户到访率', 'Deal Rate': '到访成交率',
        'Rating': '评级',
        'Efficiency Tag': '效率标签',
        'Creative Theme': '创意主题' # 🆕
    }

    format_mapping = {
        'Cost': '¥{:,.0f}'.format, 'CPL': '¥{:,.0f}'.format, 'Valid CPL': '¥{:,.0f}'.format, 
        'Client CPL': '¥{:,.0f}'.format, 'Visit CPL': '¥{:,.0f}'.format, 'Deal CPL': '¥{:,.0f}'.format,
        'Valid Rate': '{:.1f}%'.format, 'Client Rate': '{:.1f}%'.format, 'Visit Rate': '{:.1f}%'.format, 
        'Deal Rate': '{:.1f}%'.format
    }

    st.subheader("核心指标数据表")
    
    cols_to_display = ["Creative Name", "Creative Theme", "Rating", "Efficiency Tag", "Cost", "Leads", "Valid Leads", "Clients", 
                        "Visits", "Deals", "Valid Rate", "Client Rate", "Visit Rate", "Deal Rate", 
                        "Valid CPL", "Client CPL", "Visit CPL", "Deal CPL"] 

    display_df = df.copy()
    
    for col, func in format_mapping.items():
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: func(x) if pd.notna(x) and x is not None and x != np.inf and x != -np.inf else '/')
    
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
    cols_per_row = min(len(selected_creatives), 4) 
    funnel_cols = st.columns(cols_per_row)
    for i, row in df.iterrows():
        with funnel_cols[i % cols_per_row]:
            st.plotly_chart(create_creative_funnel(row, row['Creative Name']), use_container_width=True)


# =======================================================
# 🆕 3. 优化后的推广逻辑与创意策略标签页函数 (V2: 细分标签页 - 增加数据驱动分析)
# =======================================================

def generate_marketing_logic_page_v2():
    st.header("💡 产业园区推广逻辑与创意策略总览")
    st.markdown("> 本页面拆分梳理了项目的核心营销逻辑、行业痛点、素材创意主题和营销漏斗应用，是**汇报和内容创作**的指导手册。")
    st.markdown("---")
    
    # 获取当前月份的广告素材数据，用于策略页面的数据驱动分析
    current_data = st.session_state.all_months_data[st.session_state.current_month]
    creatives_data = current_data.get('creatives_data', [])
    df_full = pd.DataFrame(creatives_data)
    
    # 确保所有数字列已转换
    numeric_cols = ["Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals"]
    for col in numeric_cols:
        df_full[col] = pd.to_numeric(df_full[col], errors='coerce').fillna(0)
    
    # 计算核心指标 (与 generate_creative_charts 保持一致)
    df_full['Valid CPL'] = df_full['Cost'] / df_full['Valid Leads'].replace(0, np.nan)
    df_full['Visit Rate'] = (df_full['Visits'] / df_full['Clients'].replace(0, np.nan)) * 100 
    
    # 确保 Creative Theme 存在
    if 'Creative Theme' not in df_full.columns:
        df_full['Creative Theme'] = '未分类'
    df_full['Creative Theme'] = df_full['Creative Theme'].fillna('未分类')


    # 定义四个子标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "💰 核心通用价值 (宏观)", 
        "⚙️ 行业痛点与解法 (专业)", 
        "🎬 创意主题与脚本 (落地)",
        "📈 策略与漏斗应用 (指导)"
    ])

    # --- Tab 1: 核心通用价值 (宏观) ---
    with tab1:
        st.subheader("1.1 核心通用价值点：吸引大众关注")
        st.markdown("这些价值点是**品牌宣传和初期引流素材**的核心切入点，适用于大范围公域流量。")

        col_values = st.columns(4)
        
        # 价值点数据 (基于用户思维导图 - 通用类)
        generic_values = {
            "💰 成本优势与低门槛": {
                "icon": "💸", 
                "keywords": "价格直报、首付二成、综合成本优势", 
                "detail": "直接给出低价或灵活金融方案，降低客户决策门槛，抓住对成本敏感的受众。"
            },
            "📈 资产保障与收益": {
                "icon": "🏦", 
                "keywords": "投资属性、专属政策红利、长期稳定", 
                "detail": "强调资产价值和政策稀缺性，将购买转化为一种可靠的投资行为，说服决策层。"
            },
            "🌐 园区配套与实力": {
                "icon": "🏭", 
                "keywords": "硬件参数、产业集群、龙头背书", 
                "detail": "展现园区强大的硬件基础设施和已有的产业链生态，满足企业对稳定运营和发展环境的需求。"
            },
            "🤝 软性服务与信任": {
                "icon": "🏆", 
                "keywords": "一站式服务、成功案例、问题解决", 
                "detail": "通过承诺和案例展示服务能力和专业度，建立客户信任感，打消对新环境的顾虑。"
            }
        }
        
        for i, (title, data) in enumerate(generic_values.items()):
            with col_values[i]:
                st.markdown(f"""
                <div style="padding: 15px; border-radius: 10px; border-left: 5px solid #FF6B6B; background-color: #fff0f0; height: 200px;">
                    <h5 style="margin-top: 0; color: #2C3E50;">{data['icon']} **{title}**</h5>
                    <p style="font-size: 13px; margin-bottom: 5px;">**切入点：** {data['keywords']}</p>
                    <p style="font-size: 13px; color: #555; line-height: 1.3;">{data['detail']}</p>
                </div>
                """, unsafe_allow_html=True)
                
    # --- Tab 2: 行业痛点与解法 (专业) ---
    with tab2:
        st.subheader("2.1 垂直行业痛点分析与解法矩阵")
        st.markdown("这是**高意向转化**的关键，素材必须直击行业刚需，展现专业性和排他性。")

        industry_data = [
            {
                "行业": "化工新材料", 
                "核心痛点": "危化品储存/生产合规难；环评审批慢且成本高。", 
                "我们的解法 (卖点)": "**安全合规专区：** **专属的危化品储存设施**，协助企业**一站式完成环评**，快速投产。",
                "素材/脚本主题": "《为什么您的环评总不过？看我们如何 30 天拿证》"
            },
            {
                "行业": "精密制造/高耗能", 
                "核心痛点": "电力不稳定影响生产；设备需超重承载和高洁净度。", 
                "我们的解法 (卖点)": "**高标准基础设施：** **双回路供电**（99.99%稳定供电），**4T/㎡楼板承重**，提供**超洁净生产环境**。",
                "素材/脚本主题": "《重型设备福音：双回路供电让您的生产永不宕机》"
            },
            {
                "行业": "美妆/医疗器械", 
                "核心痛点": "严格的 GMP/GSP 认证要求；园区形象与品牌不匹配。", 
                "我们的解法 (卖点)": "**品牌认证级厂房：** 现成**通过国家认证**的洁净车间，**高端园区设计**，助力品牌形象升级。",
                "素材/脚本主题": "《美妆新国货：拎包入住 GMP 认证工厂的秘密》"
            }
        ]
        
        # 将数据转换为 DataFrame 用于 Streamlit 展示
        df_industry = pd.DataFrame(industry_data)
        st.dataframe(
            df_industry.style.set_properties(**{'font-size': '14px', 'text-align': 'left'})
                            .set_table_styles([{'selector': 'th', 'props': [('background-color', '#4ECDC4'), ('color', 'white'), ('font-size', '14px')]}]),
            use_container_width=True,
            hide_index=True
        )

    # --- Tab 3: 创意主题与脚本 (落地) ---
    with tab3:
        st.subheader("3.1 核心创意主题与脚本结构建议 (静态指导)")
        st.markdown("此表为**视频制作团队**提供直接的素材主题和制作模板。")

        creative_themes = [
            {"主题类型": "价格/促销 (通用)", "逻辑切入点": "成本优势/首付政策", "脚本结构": "痛点（高房租）→ 解决方案（园区低价）→ 稀缺性（政策福利）→ CTA（立即咨询）。"},
            {"主题类型": "实景展示 (通用)", "逻辑切入点": "配套实力/区位", "脚本结构": "航拍（宏大叙事）→ 核心配套（电力、承重）细节特写 → 园区生活场景 → CTA（预约到访）。"},
            {"主题类型": "行业专业解说 (行业痛点)", "逻辑切入点": "痛点解法（如：环评）", "脚本结构": "抛出行业尖锐痛点（**化工合规太难**）→ 专家访谈或动画演示解法（**展示我们独有资质**）→ 成功案例对比 → CTA（获取白皮书）。"},
            {"主题类型": "客户证言 (信任)", "逻辑切入点": "成功案例/服务过程", "脚本结构": "客户入驻前后的对比 → 客户亲自讲述**解决了哪些实际问题** → 感谢和推荐 → CTA（与我们联系）。"}
        ]
        
        df_creative = pd.DataFrame(creative_themes)
        st.table(df_creative)
        
        st.caption("🚀 建议：高成本投入的素材应侧重于**行业专业解说**，以获取高价值线索。")
        
        st.markdown("---")
        st.subheader("📊 创意主题效果对比 (基于当前数据)")
        
        if df_full.empty or df_full['Leads'].sum() == 0:
             st.warning("当前月份没有素材数据或线索量为零，无法进行主题效果分析。请在 '⚙️ 数据编辑' 中输入数据。")
        else:
            # 🆕 核心代码：按 Creative Theme 分组聚合
            
            # 1. 计算主题平均指标
            theme_agg = df_full.groupby('Creative Theme').agg(
                素材数量=('Creative Name', 'count'),
                平均有效线索成本=('Valid CPL', 'mean'),
                平均客户到访率=('Visit Rate', 'mean'),
                总成交数=('Deals', 'sum')
            ).reset_index()

            # 2. 格式化输出
            theme_agg['平均有效线索成本'] = theme_agg['平均有效线索成本'].apply(lambda x: f"¥{x:,.0f}" if pd.notna(x) and x != np.inf else 'N/A')
            theme_agg['平均客户到访率'] = theme_agg['平均客户到访率'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else 'N/A')
            
            # 3. 排序和展示
            theme_agg = theme_agg.sort_values(by='总成交数', ascending=False)
            
            metric_map = {
                'Creative Theme': '创意主题', '素材数量': '素材数量', 
                '平均有效线索成本': '平均有效线索成本 (越低越好)', 
                '平均客户到访率': '平均客户到访率 (越高越好)',
                '总成交数': '总成交数'
            }
            theme_agg.rename(columns=metric_map, inplace=True)
            
            st.dataframe(
                theme_agg, 
                use_container_width=True, 
                hide_index=True
            )
            
            st.markdown("""
            **📈 策略汇报洞察 (基于主题对比数据)：**
            * ✅ **高效主题确认：** 观察 **'平均有效线索成本 (越低越好)'** 这一列，成本最低的主题应被标记为**“明星创意”**，建议**加大预算**。
            * ⚠️ **低质主题预警：** 观察 **'平均客户到访率 (越高越好)'** 这一列，到访率低且线索量大的主题，说明吸引的线索质量差，应**立即优化**或**暂停投放**。
            """)
        

    # --- Tab 4: 策略与漏斗应用 (指导) ---
    with tab4:
        st.subheader("4.1 推广逻辑在 AIPL 营销漏斗中的应用")
        st.markdown("确保营销资源投入与客户所处的转化阶段精确匹配。")

        strategy_data = [
            {"AIPL 阶段": "A - 认知 (Awareness)", "核心目标": "**扩大触达，制造话题**", "应用逻辑": "成本优势、低门槛金融（**通用价值**）", "内容形式": "大众信息流短视频、促销海报"},
            {"AIPL 阶段": "I - 兴趣 (Interest)", "核心目标": "筛选意向客户，**建立品牌认知**", "应用逻辑": "资产投资属性、园区配套实力（**通用价值**）", "内容形式": "专业公众号文章、园区航拍大片、成功案例集"},
            {"AIPL 阶段": "P - 购买 (Purchase)", "核心目标": "**精准转化线索，促使留资**", "应用逻辑": "垂直行业痛点与独家解法（**行业痛点**）", "内容形式": "高专业度问答、白皮书下载、垂直媒体广告、搜索广告"},
            {"AIPL 阶段": "L - 忠诚 (Loyalty)", "核心目标": "促进**到访和最终成交**", "应用逻辑": "软性服务、金融方案、问题解决过程（**通用价值**）", "内容形式": "专属销售跟进材料、私域路演活动"}
        ]
        
        df_strategy = pd.DataFrame(strategy_data)
        st.table(df_strategy)
        st.caption("✅ 投放检查点：检查 P 阶段素材（行业痛点）是否吸引了高意向线索，如果有效线索成本高，应回溯 A 和 I 阶段的通用素材是否覆盖面过广。")


# ==================== 5. 侧边栏及主应用入口 (与原代码保持一致) ====================

# 1. 侧边栏：定义当前月份和添加新月份
st.sidebar.markdown("---")
st.sidebar.header("🗓️ 月份管理")

available_months = sorted(st.session_state.all_months_data.keys(), reverse=True)

# 3. 修正：设置中文月份的默认选择
default_index = 0
try:
    default_index = available_months.index(DEFAULT_MONTH_2)
except ValueError:
    pass

current_month = st.sidebar.radio("选择/编辑月份:", available_months, index=default_index, key="month_selector_sidebar") 
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
new_month = st.sidebar.text_input("新增月份名称 (例如：一月)", key="new_month_input")
if st.sidebar.button("➕ 创建新月份数据"):
    if new_month and new_month not in st.session_state.all_months_data:
        # 复制现有月份的默认数据结构，以保持 reason_labels 一致
        new_data = st.session_state.all_months_data[available_months[0]].copy()
        new_data['cities_data'] = {city: [0]*6 for city in cities}
        new_data['reasons_data'] = defaultdict(dict)
        new_data['creatives_data'] = EMPTY_DATA_STRUCTURE['creatives_data'][:]
        
        st.session_state.all_months_data[new_month] = new_data
        
        st.rerun() 

# 6. 主应用入口 (集成标签页)

sales_tab, creative_tab, logic_tab, edit_tab = st.tabs([
    "💰 销售数据总览", 
    "🖼️ 广告素材效果分析",
    "💡 推广逻辑与创意策略", # 🆕 细分后的标签页
    "⚙️ 数据编辑"
])

with sales_tab:
    generate_sales_charts(current_data)

with creative_tab:
    generate_creative_charts(current_data)

# 🆕 新标签页的调用 V2
with logic_tab:
    generate_marketing_logic_page_v2()
    
with edit_tab:
    st.header(f"⚙️ {current_month} - 广告素材数据编辑")
    st.warning("您可以在表格中直接编辑数据，更改将实时更新内存中的图表。请在编辑完成后，手动重新运行程序以刷新 '广告素材效果分析' 标签页。")
    
    creative_df = pd.DataFrame(current_data.get('creatives_data', []))
    
    # 🆕 确保 Creative Theme 列存在，用于 data_editor
    if 'Creative Theme' not in creative_df.columns:
        creative_df['Creative Theme'] = '未分类'

    column_config = {
        "Creative Name": st.column_config.TextColumn("素材简称", required=True),
        "Creative ID": st.column_config.TextColumn("素材ID", required=True),
        "Link": st.column_config.TextColumn("素材链接"),
        "Cost": st.column_config.NumberColumn("总成本", min_value=0, format="¥%d"),
        "Leads": st.column_config.NumberColumn("线索量", min_value=0),
        "Valid Leads": st.column_config.NumberColumn("有效线索", min_value=0),
        "Clients": st.column_config.NumberColumn("客户数", min_value=0),
        "Visits": st.column_config.NumberColumn("到访数", min_value=0),
        "Deals": st.column_config.NumberColumn("成交数", min_value=0),
        # 🆕 添加 Creative Theme 下拉框配置
        "Creative Theme": st.column_config.SelectboxColumn(
            "创意主题",
            options=["价格优势", "配套实力", "行业痛点-化工", "行业痛点-制造", "客户证言", "其他", "未分类"], # 增加选项
            required=True
        )
    }

    edited_df = st.data_editor(
        creative_df,
        column_config=column_config,
        num_rows="dynamic", 
        use_container_width=True,
        key=f"{current_month}_creative_editor"
    )

    # 检查是否有编辑变动并更新 Session State
    if not edited_df.equals(creative_df):
        # 将 DataFrame 转换为字典列表，用于更新 Session State
        new_creative_data = edited_df.to_dict('records')
        
        # ⚠️ 确保只包含 DataFrame 中的列，避免意外的 index/level 列
        final_creative_data = []
        expected_keys = ["Creative Name", "Creative ID", "Link", "Cost", "Leads", "Valid Leads", "Clients", "Visits", "Deals", "Creative Theme"]
        for record in new_creative_data:
            new_record = {k: record.get(k, 0) for k in expected_keys}
            final_creative_data.append(new_record)

        current_data['creatives_data'] = final_creative_data
        st.toast("广告素材数据已在内存中更新。", icon="📝")

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
