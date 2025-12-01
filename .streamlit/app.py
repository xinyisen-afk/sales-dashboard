import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 网页标题
st.set_page_config(page_title="销售数据分析系统", layout="wide")
st.title("🎯 五城市销售数据分析系统")

# 定义所有城市
cities = ['从化', '中山', '江门', '南沙二园', '佛山']
stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

# 初始化session state
if 'cities_data' not in st.session_state:
    st.session_state.cities_data = {}
if 'reasons_data' not in st.session_state:
    st.session_state.reasons_data = {}
    
# =======================================================
# 请在这里更新您的【标准转化数据】
# =======================================================
default_values_conversion = {
    '从化': [21, 19, 17, 8, 4, 2],
    '中山': [30, 25, 20, 11, 5, 1],
    '江门': [6, 6, 5, 5, 1, 0], 
    '南沙二园': [31, 26, 20, 11, 0, 0], 
    '佛山': [4, 4, 4, 3, 0, 0]
}
    
# 默认值 - 原因标签
if 'reason_labels' not in st.session_state:
    st.session_state.reason_labels = {
        'invalid': ['空号错号', '无人接听', '拒绝沟通', '信息错误'],
        'not_converted': ['需求不符', '预算不足', '竞品选择', '时机不对'],
        'not_client': ['价格问题', '服务担忧', '方案不符', '跟进中'],
        'not_visit': ['时间冲突', '距离太远', '兴趣减弱', '其他安排'],
        'not_deal': ['价格太贵', '被竞品抢走', '资金问题', '决策延迟']
    }

# 请根据需要更新这里的【标准流失原因数据】
default_values_reasons = {
    'invalid': {
        '从化': [3, 2, 1, 1], '中山': [5, 4, 1, 0], '江门': [0, 1, 0, 0],
        '南沙二园': [3, 2, 0, 0], 
        '佛山': [0, 0, 0, 0] 
    },
    'not_converted': {
        '从化': [4, 3, 2, 1], '中山': [5, 3, 1, 1], '江门': [0, 0, 0, 1],
        '南沙二园': [4, 2, 0, 0], 
        '佛山': [0, 0, 0, 0] 
    },
    'not_client': {
        '从化': [4, 2, 2, 1], '中山': [3, 2, 1, 3], '江门': [0, 0, 0, 0],
        '南沙二园': [3, 2, 1, 3], 
        '佛山': [0, 1, 0, 0] 
    },
    'not_visit': {
        '从化': [2, 1, 1, 0], '中山': [3, 2, 1, 0], '江门': [1, 1, 1, 1],
        '南沙二园': [4, 3, 2, 2], 
        '佛山': [1, 1, 1, 0] 
    },
    'not_deal': {
        '从化': [2, 1, 1, 0], '中山': [3, 2, 1, 0], '江门': [0, 0, 0, 0],
        '南沙二园': [0, 0, 0, 0], 
        '佛山': [0, 0, 0, 0] 
    }
}

# 侧边栏 - 数据输入
st.sidebar.header("📊 核心数据输入")
cost_per_lead = st.sidebar.number_input("单条线索成本(元)", value=320, min_value=0)

# 城市数据输入 - 使用折叠器组织
with st.sidebar.expander("🏙️ 各城市转化数据", expanded=True):
    for city in cities:
        st.write(f"**{city}转化数据**")
        cols = st.columns(2)
        values = []
        for i, stage in enumerate(stages):
            col_idx = i % 2
            value = cols[col_idx].number_input(
                f"{stage}",
                value=default_values_conversion[city][i],
                key=f"{city}_{stage}",
                min_value=0
            )
            values.append(value)
        st.session_state.cities_data[city] = values
        
        
# ======== 未转化原因数据输入互动化函数 ========
def create_reason_inputs(stage_key, stage_title, reason_count=4):
    """创建互动式的流失原因标签和数量输入"""
    
    st.subheader(stage_title)
    
    # 1. 首先让用户输入原因标签名称 (全局标签)
    st.markdown("##### 📌 **原因标签设置 (影响所有城市)**")
    label_cols = st.columns(reason_count)
    current_labels = []
    for i in range(reason_count):
        label = label_cols[i].text_input(
            f"原因 {i+1} 名称", 
            value=st.session_state.reason_labels[stage_key][i],
            key=f"label_{stage_key}_{i}"
        )
        current_labels.append(label)
    st.session_state.reason_labels[stage_key] = current_labels # 保存更新后的标签
    
    # 2. 然后为每个城市输入对应数量
    st.markdown("##### 🔢 **各城市流失数量**")
    reason_data = {}
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(reason_count)
        city_reason_data = {}
        
        city_default_values = default_values_reasons.get(stage_key, {}).get(city, [0]*reason_count)
        
        for i in range(reason_count):
            label = current_labels[i] 
            
            value = cols[i].number_input(
                f"{label} ({city})", 
                value=city_default_values[i], 
                key=f"{stage_key}_{city}_{i}",
                min_value=0,
                label_visibility="collapsed" 
            )
            city_reason_data[label] = value
        reason_data[city] = city_reason_data
        
    st.session_state.reasons_data[stage_key] = reason_data
    
    return reason_data


with st.sidebar.expander("🔍 未转化原因数据", expanded=False):
    
    create_reason_inputs('invalid', "❌ 无效线索原因", reason_count=4)
    create_reason_inputs('not_converted', "📞 未转化线索原因", reason_count=4)
    create_reason_inputs('not_client', "👥 未转化客户原因", reason_count=4)
    create_reason_inputs('not_visit', "🚫 未到访原因", reason_count=4)
    create_reason_inputs('not_deal', "💸 未成交原因", reason_count=4)

# ==================== 漏斗图函数定义 ====================
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
    
    text_colors = []
    for color in colors[:len(values)]:
        if color in ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']:
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

def create_simple_reason_chart(reason_data, title):
    """创建简单的柱状图分析，适应5个城市，使用2行3列布局"""
    fig = make_subplots(rows=2, cols=3, 
                        subplot_titles=[f'{city}{title}' for city in cities],
                        horizontal_spacing=0.1, vertical_spacing=0.2)
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for i, city in enumerate(cities):
        city_data = reason_data[city]
        reasons = list(city_data.keys())
        counts = list(city_data.values())
        
        row_idx = 1 if i < 3 else 2
        col_idx = (i % 3) + 1
        
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
            row=row_idx, col=col_idx
        )
        fig.update_xaxes(title_text="数量", row=row_idx, col=col_idx)
    
    fig.update_layout(
        height=800, 
        showlegend=False,
        title_text=f"<b>{title}分析</b>",
        title_x=0.5
    )
    return fig

def create_pie_chart_for_reason(reason_data, title):
    """为原因数据创建饼图分析，适应5个城市，使用2行3列布局"""
    fig = make_subplots(
        rows=2, 
        cols=3, 
        subplot_titles=[f'{city}{title}占比' for city in cities],
        specs=[[{"type": "pie"}, {"type": "pie"}, {"type": "pie"}],
               [{"type": "pie"}, {"type": "pie"}, {"type": "pie"}]]
    )
    
    for i, city in enumerate(cities):
        city_data = reason_data[city]
        reasons = list(city_data.keys())
        counts = list(city_data.values())
        
        row_idx = 1 if i < 3 else 2
        col_idx = (i % 3) + 1
        
        fig.add_trace(
            go.Pie(
                labels=reasons,
                values=counts,
                name=city,
                textinfo='percent+label',
                showlegend=False,
                hole=0.4
            ),
            row=row_idx, col=col_idx
        )
    
    fig.update_layout(
        height=800,
        showlegend=False,
        title_text=f"<b>{title}占比分析</b>",
        title_x=0.5
    )
    return fig

# ==================== 主图表生成函数 ====================
def generate_charts():
    cities_data = st.session_state.cities_data
    reasons_data = st.session_state.reasons_data

    # ==================== 汇总看板表格 + 线索量分布 ====================
    col1, col2 = st.columns([3, 2]) 
    
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
        
        # === 1. 新增代码：下载按钮 ===
        csv_export = summary_df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="⬇️ 下载汇总看板数据 (CSV)",
            data=csv_export,
            file_name='销售数据汇总看板.csv',
            mime='text/csv',
        )
        # =============================
    
    with col2:
        st.header("🔢 线索量分布")
        leads_data = [cities_data[city][0] for city in cities]
        
        fig_pie = px.pie(
            values=leads_data,
            names=cities,
            title='',
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD700']
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=350, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    # ==================== 成本分析 ====================
    st.header("💰 各阶段成本分析")
    
    fig_cost = make_subplots(rows=2, cols=3, 
                             subplot_titles=[f'{city}成本分析' for city in cities])
    
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
        
        row_idx = 1 if i < 3 else 2
        col_idx = (i % 3) + 1
        
        fig_cost.add_trace(
            go.Bar(
                name=city,
                x=cost_labels,
                y=stage_costs,
                marker_color=colors,
                text=[f'¥{cost:.0f}' if cost > 0 else '/' for cost in stage_costs],
                textposition='auto',
                showlegend=False
            ),
            row=row_idx, col=col_idx
        )
        
        fig_cost.update_xaxes(title_text="阶段", row=row_idx, col=col_idx)
        fig_cost.update_yaxes(title_text="成本(元)", row=row_idx, col=col_idx)
    
    fig_cost.update_layout(height=800, showlegend=False)
    st.plotly_chart(fig_cost, use_container_width=True)

    # ==================== 转化漏斗 ====================
    st.header("🎨 转化漏斗分析")
    st.markdown("该功能使用 **标签页（Tabs）** 展示不同维度的漏斗图。")
    
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
        col_row2_1, col_row2_2, _ = st.columns([1, 1, 1]) 
        cols_row2 = [col_row2_1, col_row2_2]
        for i in range(2):
            city = cities[i + 3]
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
    
    # ==================== 未转化客户深度分析 - 柱状图 ====================
    st.header("🔍 未转化客户深度分析 - 柱状图")
    
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

    # ==================== 未转化客户深度分析 - 饼图 (修复 Tab 标题) ====================
    st.header("🥧 未转化客户深度分析 - 饼图")
    
    pie_tab1, pie_tab2, pie_tab3, pie_tab4, pie_tab5 = st.tabs([
        "❌ 无效线索**原因分布**",
        "📞 未转化线索**原因分布**",
        "👥 未转化客户**原因分布**",
        "🚫 未到访**原因分布**",
        "💸 未成交**原因分布**"
    ])
    
    with pie_tab1:
        st.subheader("无效线索原因占比分析")
        fig_invalid_pie = create_pie_chart_for_reason(reasons_data['invalid'], "无效线索原因")
        st.plotly_chart(fig_invalid_pie, use_container_width=True)
    
    with pie_tab2:
        st.subheader("未转化线索原因占比分析")
        fig_not_conv_pie = create_pie_chart_for_reason(reasons_data['not_converted'], "未转化线索原因")
        st.plotly_chart(fig_not_conv_pie, use_container_width=True)
    
    with pie_tab3:
        st.subheader("未转化客户原因占比分析")
        fig_not_client_pie = create_pie_chart_for_reason(reasons_data['not_client'], "未转化客户原因")
        st.plotly_chart(fig_not_client_pie, use_container_width=True)
    
    with pie_tab4:
        st.subheader("未到访原因占比分析")
        fig_not_visit_pie = create_pie_chart_for_reason(reasons_data['not_visit'], "未到访原因")
        st.plotly_chart(fig_not_visit_pie, use_container_width=True)
    
    with pie_tab5:
        st.subheader("未成交原因占比分析")
        fig_not_deal_pie = create_pie_chart_for_reason(reasons_data['not_deal'], "未成交原因")
        st.plotly_chart(fig_not_deal_pie, use_container_width=True)


# 显示图表
generate_charts()

# 操作提示
st.sidebar.markdown("---")
st.sidebar.info("""
**💡 使用提示：**
1. 点击展开器修改数据
2. **在流失原因设置中，可以自定义标签名称！**
3. 数据会自动保存和更新
4. 使用标签页切换不同视图
5. 所有图表和洞察都是交互式的
""")

st.sidebar.success("✅ 系统已修复并优化，新增 CSV 导出功能！")
