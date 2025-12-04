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
# 1. 数据加载与序列化函数 (与原代码保持一致)
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
        # 使用 utf-8-sig 以处理可能存在的 BOM
        with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            
            for month in data:
                month_data = data[month]
                if 'creatives_data' not in month_data:
                    month_data['creatives_data'] = EMPTY_DATA_STRUCTURE['creatives_data'][:]
                
                # 确保广告素材数据是数字类型
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
        # 2. 修正：使用中文月份作为默认键
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

    return json.dumps(data_to_save, ensure_ascii=False, indent=4)

# 应用启动时，立即加载数据
if 'all_months_data' not in st.session_state:
    load_standard_data()

# ==================== 2. 核心函数定义 (图表和原因输入) (与原代码保持一致) ====================

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
        city_data = reasons_data.get(city, {})
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
        return # 即使没有选择，也要返回，但要保证没有图表或数据框错误

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
            return "🔥 爆款/低成本高转化"
        elif rating == "⭐⭐⭐":
            if pd.isna(row['Valid CPL']) or pd.isna(row['Visit Rate']):
                return "需观察"
            if row['Valid CPL'] < avg_cpl and row['Visit Rate'] / 100 >= avg_rate:
                return "🚀 高效稳定"
            elif row['Valid CPL'] < avg_cpl * 0.8:
                return "✅ CPL优秀"
            elif row['Visit Rate'] / 100 > avg_rate * 1.2:
                return "🌟 到访转化优秀"
            else:
                return "📈 潜力素材"
        elif rating == "⭐⭐":
            return "🧪 需优化/测试中"
        else:
            return "⚠️ 低效"

    df['Rating'] = df.apply(lambda row: get_creative_rating(row, avg_valid_cpl, avg_visit_rate), axis=1)
    df['效率标签'] = df.apply(lambda row: get_efficiency_tag(row, avg_valid_cpl, avg_visit_rate), axis=1)

    # ----------------------------------------------------
    # 🌟 核心指标对比表格
    # ----------------------------------------------------
    st.subheader("📊 核心指标与效率对比")
    display_cols = ['Creative Name', 'Cost', 'Leads', 'Valid Leads', 'Clients', 'Visits', 'Deals', 
                    'Rating', '效率标签', 'Valid Rate', 'Visit Rate', 'Valid CPL', 'Visit CPL']
    
    display_df = df[display_cols].rename(columns={
        'Creative Name': '素材名称',
        'Cost': '总成本', 'Leads': '线索量', 'Valid Leads': '有效线索', 
        'Clients': '客户数', 'Visits': '到访数', 'Deals': '成交数',
        'Valid Rate': '有效线索率', 'Visit Rate': '客户到访率', 
        'Valid CPL': '有效CPL', 'Visit CPL': '到访CPL',
        'Rating': '综合评级'
    })

    # 格式化输出
    format_mapping = {
        '总成本': '¥{:,.0f}', '有效CPL': '¥{:,.0f}', '到访CPL': '¥{:,.0f}',
        '线索量': '{:,.0f}', '有效线索': '{:,.0f}', '客户数': '{:,.0f}',
        '到访数': '{:,.0f}', '成交数': '{:,.0f}',
        '有效线索率': '{:,.1f}%', '客户到访率': '{:,.1f}%',
    }
    
    for col, fmt in format_mapping.items():
        if col in display_df.columns:
            # 使用 applymap 或 apply 来避免 SettingWithCopyWarning，并确保只格式化数字
            # 对于 Streamlit 的 dataframe，直接修改 DataFrame 的副本通常是安全的
            display_df[col] = display_df[col].apply(lambda x: fmt.format(x) if pd.notna(x) and isinstance(x, (int, float)) else x)


    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ----------------------------------------------------
    # 🌟 转化漏斗对比图表
    # ----------------------------------------------------
    st.subheader("📉 单素材转化漏斗详情")
    for name in selected_creatives:
        creative_data = df_full[df_full['Creative Name'] == name].iloc[0].to_dict()
        st.plotly_chart(create_creative_funnel(creative_data, name), use_container_width=True)

def create_data_edit_page(current_month, current_data):
    # 1. 设置全局成本
    st.header("💵 默认线索成本设置")
    default_cost = current_data.get('cost_per_lead', 320)
    new_cost = st.number_input(f"全局平均线索成本 (CPL, ¥)", min_value=1, value=default_cost, key=f"{current_month}_cpl")
    current_data['cost_per_lead'] = new_cost
    st.markdown(f"**当前线索成本:** ¥{new_cost:,.0f}")
    st.markdown("---")

    # 2. 城市销售数据输入
    st.header("🏡 城市销售数据输入")
    st.markdown("输入各城市在销售漏斗各阶段的数据：")
    
    cities_data_list = []
    for city in cities:
        values = current_data['cities_data'].get(city, [0]*6)
        row = [city] + values
        cities_data_list.append(row)
    
    # 创建 DataFrame 进行编辑
    columns = ["城市"] + stages
    cities_df = pd.DataFrame(cities_data_list, columns=columns)
    cities_df = cities_df.set_index('城市')
    
    edited_df = st.data_editor(
        cities_df,
        column_config={
            stage: st.column_config.NumberColumn(stage, min_value=0, format="%d") 
            for stage in stages
        },
        use_container_width=True,
        key=f"{current_month}_city_editor"
    )

    # 检查是否有编辑变动并更新 Session State
    if not edited_df.equals(cities_df):
        new_cities_data = edited_df.apply(lambda row: row.tolist(), axis=1).to_dict()
        current_data['cities_data'] = new_cities_data
        st.toast("城市销售数据已在内存中更新。", icon="📝")

    st.markdown("---")

    # 3. 流失原因归因输入
    st.header("🛑 流失原因归因数据输入")
    st.info("💡 **操作提示：** 首先设置标签名称 (如: 空号错号)，然后为每个城市输入对应数量。")
    
    cols_reason = st.columns(3)
    
    with cols_reason[0]:
        create_reason_inputs(current_data, 'invalid', "❌ 无效线索原因归因 (线索量 -> 接通数)")
    with cols_reason[1]:
        create_reason_inputs(current_data, 'not_converted', "📞 未转化线索原因归因 (接通数 -> 有效数)")
    with cols_reason[2]:
        create_reason_inputs(current_data, 'not_client', "👥 未转化客户原因归因 (有效数 -> 客户数)")
    
    cols_visit_deal = st.columns(2)
    with cols_visit_deal[0]:
        create_reason_inputs(current_data, 'not_visit', "🚫 未到访原因归因 (客户数 -> 到访数)", reason_count=3)
    with cols_visit_deal[1]:
        create_reason_inputs(current_data, 'not_deal', "💸 未成交原因归因 (到访数 -> 成交数)", reason_count=3)

    st.markdown("---")
    
    # 4. 广告素材效果输入
    st.header("🖼️ 广告素材效果输入")
    st.markdown("输入单个广告素材的投放成本和转化数据：")

    creative_df = pd.DataFrame(current_data.get('creatives_data', []))
    
    # 定义列配置，确保数据类型和格式正确
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
        st.toast("广告素材数据已在内存中更新。", icon="📝")

# =======================================================
# 5. 【替换内容】 新的推广逻辑与创意策略页面函数
# =======================================================

def create_promotion_logic_page():
    """生成具有手绘精美感的推广逻辑与创意策略页面内容"""
    st.markdown("""
# ✨ 【中创产业园】推广逻辑与创意策略

---
## 💡 核心战略总览：驱动购买的“三大维度”
---

| 🎯 栏目 I: 购买契机 (Why Buy?) | ⚡ 栏目 II: 行业痛点 (Specific Pain) | 🎬 栏目 III: 制作素材重点 (Creative Focus) |
| :--- | :--- | :--- |
| **资产升级与远见** | **合规、技术与生态** | **情景剧与硬核背书** |

---

## 栏目 I：💰 购买契机 (Why Buy?)

> 聚焦老板的**“心理账户”**：是为房东打工，还是为自己投资？是求稳，还是求发展？

### 🏷️ 1. 产业扩张与增长受限
* **痛点切入：** 订单爆满，生产线塞不下，新设备没地方放。
* **核心需求：** 需灵活可扩展的空间 和强大的生产配套（如充足电力）。
* **沟通核心：** **“效率”**与**“解放”**。

### 🏷️ 2. 经营风险与合规保障
* **痛点切入：** 害怕环保/消防突查被停产。深知产权不清的租地是企业“定时炸弹”。
* **核心需求：** 寻求合规生产环境 和独立、完整的红本产权证。
* **沟通核心：** **“安心”**与**“确权”**。

### 🏷️ 3. 成本优化与资产升级
* **痛点切入：** 厌恶租金年年涨，利润被侵蚀。惧怕搬迁带来的停产、损耗与员工流失。
* **核心需求：** 变租为购，锁定核心经营成本。将消费性支出转化为增值的固定资产。
* **沟通核心：** **“掌控”**与**“锁定”**。

### 🏷️ 4. 品牌形象与财富传承
* **痛点切入：** 破旧厂房影响公司形象和订单签约。希望为子女留下一份看得见、摸得着的实业基业。
* **核心需求：** 现代化、园林式的厂区形象；将利润转化为可传承的实体资产。
* **沟通核心：** **“形象”**与**“远见”**。

---

## 栏目 II：🏗️ 行业痛点 (Specific Pain)

> 聚焦**“生存压力”**：解决各行各业最具体的“卡脖子”难题。

### 🏷️ 1. 强监管与高风险行业
* **代表行业：** 日用化学品、食品加工、五金注塑。
* **痛点：** 涉及危化品落户难。生产废水处理难度大、成本高。
* **关键方案：** “污水管网到位，预处理后直排”解决环保难题。提供专业化管理和合规准入。

### 🏷️ 2. 高技术与稳定性要求
* **代表行业：** 医疗器械、精密制造、新材料。
* **痛点：** 地址变更意味着医疗器械产品注册证需重新申报，耗时耗钱。设备精密，对电力稳定、地面平整度有极致要求。
* **关键方案：** 购买厂房锁定生产地址，**一劳永逸**。提供卓越的厂房参数和稳定的双回路电。

### 🏷️ 3. 供应链与生态协同
* **代表行业：** 汽车零部件、化妆品包材。
* **痛点：** 需紧跟核心客户或品牌方布局，降低物流和打样成本。供应链脆弱，一个零部件断供整条线停摆。
* **关键方案：** 园区位于战略区位，形成产业集群，实现**“零距离协同”**。

### 🏷️ 4. 品牌与人才引力
* **代表行业：** 化妆品品牌方、工业装备、电子信息。
* **痛点：** 核心技术人才不愿去偏远、环境差的工业区。厂房形象与高端科技企业的定位不匹配。
* **关键方案：** 完善的生活配套（公寓、食堂、咖啡厅）吸引并留住核心人才。现代化园区形象为品牌背书。

---

## 栏目 III：🎥 制作素材重点 (Creative Focus)

> 聚焦**“感官冲击”**：通过对比和故事，快速击中老板的决策神经。

### 🏷️ 1. 痛点情景剧：焦虑与解脱
* **视频类型：** 30秒短剧，情绪驱动。
* **核心镜头：** 老板在拥挤车间里“挤空间”；财务总监拿着连年上涨的租金报表叹气。
* **创意高潮：** **“新老厂房的时空切换”**：老板从老旧车间穿越到中创现代化厂房，表情震撼和向往。

### 🏷️ 2. 价值证明：硬核资产
* **视频类型：** 数据化、理性说服片。
* **核心镜头：** 特写**“红本产权证”**和银行票据，强调“压舱石”作用。拍摄高承重、大跨度车间内部，突出可安装大型设备的潜力。
* **话术植入：** 算一笔“十年账”，强调变消费性支出为资产性投资。

### 🏷️ 3. 赋能升级：高效与生态
* **视频类型：** 效率流程展示片。
* **核心镜头：** 物流叉车在园区内顺畅通行，人车分流设计。拍摄园区内上下游企业负责人进行商务交流和沙龙会议。
* **创意点：** 展现供应链从“通讯录”搬到**“隔壁楼”**，告别断供风险。

### 🏷️ 4. 形象提升与人才引力
* **视频类型：** 品牌形象宣传片。
* **核心镜头：** 航拍园区全景，突出园林式、现代化的外观。客户被高端环境震撼，当场签约的场景。
* **创意点：** 重点展现自建公寓、食堂、咖啡厅、健身房等，打造“磁力场”，证明企业实力与品味。
    """)

# =======================================================
# 6. 主应用逻辑 (Main Function)
# =======================================================

def main():
    # 侧边栏：选择月份
    st.sidebar.header("🗓️ 数据月份选择")
    all_months = list(st.session_state.all_months_data.keys())
    
    # 确保默认月份在列表中，否则添加
    for month in DEFAULT_MONTHS_KEYS:
        if month not in all_months:
            all_months.insert(0, month)

    selected_month = st.sidebar.selectbox(
        "选择当前查看/编辑的月份", 
        options=all_months,
        index=0
    )
    
    # 获取当前月份数据
    if selected_month not in st.session_state.all_months_data:
        st.session_state.all_months_data[selected_month] = EMPTY_DATA_STRUCTURE.copy()
    
    current_data = st.session_state.all_months_data[selected_month]
    current_data['month'] = selected_month
    
    # 主体：创建标签页
    tab_titles = ["📈 销售数据概览", "🖼️ 推广素材效果", "📝 推广逻辑与创意策略", "⚙️ 数据编辑"]
    tab1, tab2, tab3, tab4 = st.tabs(tab_titles)

    with tab1:
        generate_sales_charts(current_data)

    with tab2:
        generate_creative_charts(current_data)
        
    with tab3:
        # **这里替换了旧的推广逻辑内容**
        create_promotion_logic_page() 

    with tab4:
        create_data_edit_page(selected_month, current_data)

    # 7. 开发者面板 - 核心：生成 JSON 数据
    st.sidebar.markdown("---")
    st.sidebar.header("🛠️ 开发者工具")
    
    if st.sidebar.button("生成最新的 JSON 数据"):
        json_output = serialize_data_for_export()
        st.sidebar.code(json_output, language='json')
        st.sidebar.download_button(
            label="下载标准 JSON",
            data=json_output,
            file_name="standard_data.json",
            mime="application/json"
        )
        st.sidebar.success("请复制或下载此内容，手动更新您的 `standard_data.json` 文件！")


if __name__ == '__main__':
    main()
