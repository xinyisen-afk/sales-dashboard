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
# 新增：初始化原因标签列表
if 'reason_labels' not in st.session_state:
    st.session_state.reason_labels = {
        'invalid': ['空号错号', '无人接听', '拒绝沟通', '信息错误'],
        'not_converted': ['需求不符', '预算不足', '竞品选择', '时机不对'],
        'not_client': ['价格问题', '服务担忧', '方案不符', '跟进中'],
        'not_visit': ['时间冲突', '距离太远', '兴趣减弱', '其他安排'],
        'not_deal': ['价格太贵', '被竞品抢走', '资金问题', '决策延迟']
    }
    
# 默认值
default_values_reasons = {
    'invalid': [3, 2, 1, 1],
    'not_converted': [4, 3, 2, 1],
    'not_client': [4, 2, 2, 1],
    'not_visit': [2, 1, 1, 0],
    'not_deal': [2, 1, 1, 0]
}


# 侧边栏 - 数据输入
st.sidebar.header("📊 核心数据输入")
cost_per_lead = st.sidebar.number_input("单条线索成本(元)", value=320, min_value=0)

# 城市数据输入 - 使用折叠器组织 (保持不变)
cities = ['从化', '中山', '江门']
stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

with st.sidebar.expander("🏙️ 各城市转化数据", expanded=True):
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
        
        
# ======== 核心改动区域：未转化原因数据输入互动化 ========
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
        for i in range(reason_count):
            # 使用用户自定义的标签作为输入框的描述
            label = current_labels[i] 
            
            # 使用默认值或之前的输入值
            default_val = default_values_reasons.get(stage_key, [0]*reason_count)[i]
            
            # 由于 Streamlit 的 key 机制，我们使用固定的 stage_key 和 index 来确保输入框值稳定
            value = cols[i].number_input(
                f"{label} ({city})", 
                value=default_val,
                key=f"{stage_key}_{city}_{i}",
                min_value=0,
                label_visibility="collapsed" # 隐藏上方的标签，使用 col 的 st.write 标题
            )
            # 使用用户自定义的标签作为字典的键
            city_reason_data[label] = value
        reason_data[city] = city_reason_data
        
    st.session_state.reasons_data[stage_key] = reason_data
    
    # 返回最新数据（虽然已保存到 session state，但为了函数规范）
    return reason_data


with st.sidebar.expander("🔍 未转化原因数据", expanded=False):
    
    # 1. 无效线索原因
    create_reason_inputs('invalid', "❌ 无效线索原因", reason_count=4)

    # 2. 未转化线索原因
    create_reason_inputs('not_converted', "📞 未转化线索原因", reason_count=4)

    # 3. 未转化客户原因
    create_reason_inputs('not_client', "👥 未转化客户原因", reason_count=4)

    # 4. 未到访原因
    create_reason_inputs('not_visit', "🚫 未到访原因", reason_count=4)

    # 5. 未成交原因 - 新增
    create_reason_inputs('not_deal', "💸 未成交原因", reason_count=4)

# ==================== 漏斗图函数定义 (保持不变) ====================
# ... (create_beautiful_funnel, create_horizontal_funnel, create_simple_reason_chart, create_pie_chart_for_reason 保持不变)

def create_beautiful_funnel(city_data, city_name, stages):
    """创建美观的漏斗图"""
    values = city_data
    
    color_schemes = {
        '从化': ['#FF6B6B', '#FF8E8E', '#FFB1B1', '#FFD4D4', '#FFE8E8', '#FFF5F5'],
        '中山': ['#4ECDC4', '#88D8D0', '#A8E6DD', '#C8F3EC', '#E1F8F5', '#F0FCFA'],
        '江门': ['#45B7D1', '#7BC9E0', '#9AD6E8', '#B9E3F0', '#D4EDF7', '#EAF6FB']
    }
    
    colors = color_schemes.get(city_name, px.colors.sequential.Blues)
    
    text_colors = []
    for color in colors[:len(values)]:
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

def create_pie_chart_for_reason(reason_data, title):
    """为原因数据创建饼图分析"""
    fig = make_subplots(
        rows=1, 
        cols=3, 
        subplot_titles=[f'{city}{title}占比' for city in cities],
        specs=[[{"type": "pie"}, {"type": "pie"}, {"type": "pie"}]]
    )
    
    for i, city in enumerate(cities):
        city_data = reason_data[city]
        reasons = list(city_data.keys())
        counts = list(city_data.values())
        
        fig.add_trace(
            go.Pie(
                labels=reasons,
                values=counts,
                name=city,
                textinfo='percent+label',
                showlegend=False,
                hole=0.4
            ),
            row=1, col=i+1
        )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        title_text=f"<b>{title}占比分析</b>",
        title_x=0.5
    )
    return fig

# ==================== 交互式文字洞察生成函数 (保持不变) ====================
def get_top_reason(reason_data, city, default_message="无明显流失"):
    """获取某个城市某个流失阶段的主要原因及其占比"""
    city_data = reason_data.get(city, {})
    if not city_data:
        return default_message
    
    total = sum(city_data.values())
    if total == 0:
        return default_message

    # 找到数量最多的原因
    max_reason = max(city_data, key=city_data.get)
    max_count = city_data[max_reason]
    percentage = (max_count / total) * 100
    
    # 构建洞察文本
    return f"**{max_reason}**（**{max_count}**条，占比 **{percentage:.1f}%**）"

def generate_insights(reasons_data):
    """生成并展示未转化客户深度分析的文字洞察"""
    st.header("💡 转化流失关键洞察")
    
    # 定义分析的阶段和对应的数据键
    analysis_stages = {
        "无效线索": ('invalid', "❌ 线索阶段，主要流失原因为:"),
        "未转化线索": ('not_converted', "📞 接通阶段，线索未有效的主要原因在于:"),
        "未转化客户": ('not_client', "👥 有效线索未转化为客户，主要流失原因为:"),
        "未到访": ('not_visit', "🚫 客户未到访的关键障碍是:"),
        "未成交": ('not_deal', "💸 到访后未成交的瓶颈是:")
    }
    
    
    cols = st.columns(len(cities)) # 每行三个城市
    
    for city_index, city in enumerate(cities):
        with cols[city_index]:
            st.subheader(f"城市: {city}")
            st.markdown("---")
            
            for stage_name, (data_key, prefix) in analysis_stages.items():
                
                # 获取该阶段的主要原因洞察
                top_reason_text = get_top_reason(reasons_data.get(data_key, {}), city)
                
                # 使用不同的颜色和图标来区分阶段
                icon = {
                    "无效线索": "⛔",
                    "未转化线索": "🗣️",
                    "未转化客户": "💰",
                    "未到访": "🛣️",
                    "未成交": "💔"
                }.get(stage_name, "➡️")
                
                st.markdown(f"""
                    #### {icon} {stage_name}
                    {prefix} {top_reason_text}
                """)
                
            st.markdown("---")


# ==================== 主图表生成函数 ====================
def generate_charts():
    cities_data = st.session_state.cities_data
    reasons_data = st.session_state.reasons_data

    # ... (数据汇总、成本分析、转化漏斗等部分保持不变) ...
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

    # ==================== 交互式文字洞察 ====================
    generate_insights(reasons_data)

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

    # ==================== 未转化客户深度分析 - 饼图 ====================
    st.header("🥧 未转化客户深度分析 - 饼图")
    
    pie_tab1, pie_tab2, pie_tab3, pie_tab4, pie_tab5 = st.tabs([
        "❌ 无效线索占比",
        "📞 未转化线索占比",
        "👥 未转化客户占比",
        "🚫 未到访占比",
        "💸 未成交占比"
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

st.sidebar.success("✅ 系统优化完成！")
