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
st.set_page_config(page_title="销售数据分析系统", layout="wide")
st.title("🎯 五城市销售数据分析系统")

# 定义数据文件路径（从 GitHub 仓库读取）
DATA_FILE = 'standard_data.json'

# 定义所有城市和阶段
cities = ['从化', '中山', '江门', '南沙二园', '佛山']
stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

# =======================================================
# 1. 数据加载与序列化函数
# =======================================================

def load_standard_data():
    """尝试从 standard_data.json 文件加载数据，如果失败则使用空默认值。"""
    
    # 基础默认值，以防 JSON 文件缺失或格式错误
    empty_cities_data = {city: [0]*6 for city in cities}
    empty_reason_labels = {
        'invalid': ['空号错号', '无人接听', '拒绝沟通', '信息错误'],
        'not_converted': ['需求不符', '预算不足', '竞品选择', '时机不对'],
        'not_client': ['价格问题', '服务担忧', '方案不符', '跟进中'],
        'not_visit': ['时间冲突', '距离太远', '兴趣减弱', '其他安排'],
        'not_deal': ['价格太贵', '被竞品抢走', '资金问题', '决策延迟']
    }
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 使用 get() 确保即使 JSON 缺少键，应用也能使用默认值运行
            st.session_state.cities_data = data.get('cities_data', empty_cities_data)
            st.session_state.reasons_data = data.get('reasons_data', defaultdict(dict))
            st.session_state.reason_labels = data.get('reason_labels', empty_reason_labels)
            st.session_state.cost_per_lead = data.get('cost_per_lead', 320)
            st.sidebar.success("✅ 已从 GitHub 仓库加载标准数据。")
    except FileNotFoundError:
        st.sidebar.error(f"⚠️ 警告：未找到 {DATA_FILE} 文件。请在 GitHub 仓库中创建该文件。")
        # 文件不存在时，使用空数据初始化
        st.session_state.cities_data = empty_cities_data
        st.session_state.reasons_data = defaultdict(dict)
        st.session_state.reason_labels = empty_reason_labels
        st.session_state.cost_per_lead = 320
    except json.JSONDecodeError:
        st.sidebar.error(f"⚠️ 警告：{DATA_FILE} 文件格式错误，请检查 JSON 内容。")
        st.session_state.cities_data = empty_cities_data
        st.session_state.reasons_data = defaultdict(dict)
        st.session_state.reason_labels = empty_reason_labels
        st.session_state.cost_per_lead = 320

def serialize_data_for_export():
    """将当前的 session state 数据整理成 standard_data.json 文件格式"""
    
    # reasons_data 可能包含 defaultdict，需要转为普通 dict 以便序列化
    reasons_data_clean = dict(st.session_state.reasons_data)
    reason_labels_clean = dict(st.session_state.reason_labels)
        
    data_to_save = {
        'cities_data': st.session_state.cities_data,
        'reason_labels': reason_labels_clean,
        'reasons_data': reasons_data_clean,
        'cost_per_lead': st.session_state.cost_per_lead
    }
    
    # 使用 json.dumps 格式化输出，方便复制
    return json.dumps(data_to_save, ensure_ascii=False, indent=4)


# 应用启动时，立即加载数据
if 'cities_data' not in st.session_state:
    load_standard_data()

# ==================== 2. 侧边栏 - 数据输入 UI ====================
st.sidebar.header("📊 核心数据输入")
st.session_state.cost_per_lead = st.sidebar.number_input(
    "单条线索成本(元)", 
    value=st.session_state.get('cost_per_lead', 320), 
    min_value=0, 
    key='sidebar_cost_per_lead'
)
cost_per_lead = st.session_state.cost_per_lead


# 城市数据输入 - 使用折叠器组织
with st.sidebar.expander("🏙️ 各城市转化数据", expanded=True):
    for city in cities:
        st.write(f"**{city}转化数据**")
        cols = st.columns(2)
        values = []
        for i, stage in enumerate(stages):
            col_idx = i % 2
            # 从 session state 读取值，确保使用当前数据
            initial_value = st.session_state.cities_data.get(city, [0]*6)[i]
            
            value = cols[col_idx].number_input(
                f"{stage}",
                value=initial_value,
                key=f"{city}_{stage}",
                min_value=0
            )
            values.append(value)
        st.session_state.cities_data[city] = values
        
        
# 未转化原因数据输入互动化函数
def create_reason_inputs(stage_key, stage_title, reason_count=4):
    """创建互动式的流失原因标签和数量输入"""
    
    st.subheader(stage_title)
    
    # 1. 原因标签名称
    st.markdown("##### 📌 **原因标签设置 (影响所有城市)**")
    label_cols = st.columns(reason_count)
    current_labels = []
    
    current_default_labels = st.session_state.reason_labels.get(stage_key, [''] * 4)
    
    for i in range(reason_count):
        label = label_cols[i].text_input(
            f"原因 {i+1} 名称", 
            value=current_default_labels[i] if len(current_default_labels) > i else '',
            key=f"label_{stage_key}_{i}"
        )
        current_labels.append(label)
    st.session_state.reason_labels[stage_key] = current_labels 
    
    # 2. 各城市流失数量
    st.markdown("##### 🔢 **各城市流失数量**")
    reason_data = st.session_state.reasons_data.get(stage_key, {})
    
    for city in cities:
        st.write(f"**{city}**")
        cols = st.columns(reason_count)
        city_reason_data = reason_data.get(city, {})
        
        for i in range(reason_count):
            label = current_labels[i] 
            
            initial_value = city_reason_data.get(label, 0)
            
            value = cols[i].number_input(
                f"{label} ({city})", 
                value=initial_value, 
                key=f"{stage_key}_{city}_{i}",
                min_value=0,
                label_visibility="collapsed" 
            )
            if label:
                city_reason_data[label] = value
        reason_data[city] = city_reason_data
        
    st.session_state.reasons_data[stage_key] = reason_data


with st.sidebar.expander("🔍 未转化原因数据", expanded=False):
    create_reason_inputs('invalid', "❌ 无效线索原因", reason_count=4)
    create_reason_inputs('not_converted', "📞 未转化线索原因", reason_count=4)
    create_reason_inputs('not_client', "👥 未转化客户原因", reason_count=4)
    create_reason_inputs('not_visit', "🚫 未到访原因", reason_count=4)
    create_reason_inputs('not_deal', "💸 未成交原因", reason_count=4)

# ==================== 3. 开发者导出面板（GitHub 部署环境下的保存） ====================

st.sidebar.markdown("---")
st.sidebar.header("🔑 开发者数据导出")
st.sidebar.info("**这是部署环境下的“保存”功能！** 点击按钮，复制主页面上生成的 JSON 内容，然后用于更新 GitHub 上的 `standard_data.json` 文件。")

if st.sidebar.button("✨ 生成最新的 standard_data.json 内容", type="primary"):
    json_output = serialize_data_for_export()
    
    st.header("📋 请复制以下 JSON 内容")
    st.warning("完成复制后，请前往 GitHub 仓库，编辑 standard_data.json 文件，并用以下内容覆盖它。")
    st.code(json_output, language='json', height=500)
    st.toast("JSON 内容已生成在主页面！", icon='🎉')


# ==================== 4. Plotly 图表函数定义 (保证代码完整性) ====================

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
    text_colors = ["white"] * 3 + ["black"] * 3 # 简单判断文本颜色
    
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
    """创建水平漏斗图"""
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

def create_simple_reason_chart(reasons_data, title, cities):
    """创建多城市流失原因柱状图分析"""
    fig = make_subplots(rows=2, cols=3, 
                        subplot_titles=[f'{city}{title}' for city in cities],
                        horizontal_spacing=0.1, vertical_spacing=0.2)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for i, city in enumerate(cities):
        city_data = reasons_data.get(city, {})
        reasons = list(city_data.keys())
        counts = list(city_data.values())
        
        row_idx = 1 if i < 3 else 2
        col_idx = (i % 3) + 1
        
        fig.add_trace(
            go.Bar(name=city, y=reasons, x=counts, orientation='h', marker_color=colors[:len(reasons)],
                   text=counts, textposition='auto', showlegend=False),
            row=row_idx, col=col_idx
        )
        fig.update_xaxes(title_text="数量", row=row_idx, col=col_idx)
    
    fig.update_layout(height=800, showlegend=False, title_text=f"<b>{title}分析</b>", title_x=0.5)
    return fig

def create_pie_chart_for_reason(reasons_data, title, cities):
    """创建多城市流失原因饼图分析"""
    fig = make_subplots(rows=2, cols=3, subplot_titles=[f'{city}{title}占比' for city in cities],
                        specs=[[{"type": "pie"}, {"type": "pie"}, {"type": "pie"}],
                               [{"type": "pie"}, {"type": "pie"}, {"type": "pie"}]])
    
    for i, city in enumerate(cities):
        city_data = reasons_data.get(city, {})
        reasons = list(city_data.keys())
        counts = list(city_data.values())
        
        row_idx = 1 if i < 3 else 2
        col_idx = (i % 3) + 1
        
        fig.add_trace(
            go.Pie(labels=reasons, values=counts, name=city, textinfo='percent+label',
                   showlegend=False, hole=0.4),
            row=row_idx, col=col_idx
        )
    
    fig.update_layout(height=800, showlegend=False, title_text=f"<b>{title}占比分析</b>", title_x=0.5)
    return fig

# ==================== 5. 主图表生成函数 (包含汇总看板更新) ====================

def generate_charts():
    cities_data = st.session_state.cities_data
    reasons_data = st.session_state.reasons_data
    cost_per_lead = st.session_state.cost_per_lead

    # ------------------- 汇总看板 (Summary Dashboard) -------------------
    col1, col2 = st.columns([3, 2])
    with col1:
        st.header("📈 数据汇总看板")
        
        summary_data = []
        for city in cities:
             values = cities_data.get(city, [0]*6)
             
             total_leads = values[0]
             valid_leads = values[2]
             clients = values[3]
             visits = values[4] # 到访数量 (新增)
             deals = values[5]
             
             total_cost = total_leads * cost_per_lead # 消费总数 (新增)
             valid_rate = (valid_leads / total_leads * 100) if total_leads > 0 else 0
             valid_lead_cost = total_cost / valid_leads if valid_leads > 0 else 0
             client_cost = total_cost / clients if clients > 0 else 0
             visit_cost = total_cost / visits if visits > 0 else 0
             deal_cost = total_cost / deals if deals > 0 else 0
             
             summary_data.append({
                 '城市': city,
                 '线索总量': total_leads,
                 '**到访数量**': visits, # 新增
                 '**消费总数**': f"¥{total_cost:,.0f}", # 新增
                 '线索有效率': f"{valid_rate:.1f}%",
                 '有效线索成本': f"¥{valid_lead_cost:,.0f}" if valid_lead_cost > 0 else "/",
                 '客户成本': f"¥{client_cost:,.0f}" if client_cost > 0 else "/",
                 '到访成本': f"¥{visit_cost:,.0f}" if visit_cost > 0 else "/",
                 '成交成本': f"¥{deal_cost:,.0f}" if deal_cost > 0 else "/"
             })
        
        summary_df = pd.DataFrame(summary_data)
        
        # 优化列顺序
        new_cols_order = ['城市', '线索总量', '**到访数量**', '**消费总数**', '线索有效率', '有效线索成本', '客户成本', '到访成本', '成交成本']
        summary_df = summary_df[new_cols_order]
        
        st.dataframe(summary_df, use_container_width=True)
        
        # CSV 导出按钮
        csv_export = summary_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⬇️ 下载汇总看板数据 (CSV)",
            data=csv_export,
            file_name='销售数据汇总看板.csv',
            mime='text/csv',
        )

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

    # ------------------- 成本分析 -------------------
    st.header("💰 各阶段成本分析")
    # 此处省略成本分析图的代码，与上一个回答中相同

    # ------------------- 转化漏斗 -------------------
    st.header("🎨 转化漏斗分析")
    tab1, tab2 = st.tabs(["🎯 垂直漏斗图", "📊 水平视图"])
    
    with tab1:
        st.subheader("垂直漏斗图")
        cols = st.columns(3)
        for i, city in enumerate(cities):
            city_data = cities_data.get(city, [0]*6)
            with cols[i % 3]:
                if i < 3 or (i >= 3 and i < 5): # 确保布局是3+2
                    fig_funnel = create_beautiful_funnel(city_data, city, stages)
                    st.plotly_chart(fig_funnel, use_container_width=True)
    
    with tab2:
        st.subheader("水平漏斗图")
        cols = st.columns(3)
        for i, city in enumerate(cities):
            city_data = cities_data.get(city, [0]*6)
            with cols[i % 3]:
                if i < 3 or (i >= 3 and i < 5):
                    fig_h = create_horizontal_funnel(city_data, city, stages)
                    st.plotly_chart(fig_h, use_container_width=True)
    
    # ------------------- 未转化客户深度分析 - 柱状图 -------------------
    st.header("🔍 未转化客户深度分析 - 柱状图")
    reason_tab_bar1, reason_tab_bar2, reason_tab_bar3, reason_tab_bar4, reason_tab_bar5 = st.tabs([
        "❌ 无效线索原因", "📞 未转化线索原因", "👥 未转化客户原因", "🚫 未到访原因", "💸 未成交原因"
    ])
    
    with reason_tab_bar1:
        fig_invalid_bar = create_simple_reason_chart(reasons_data['invalid'], "无效线索原因", cities)
        st.plotly_chart(fig_invalid_bar, use_container_width=True)
    
    # ... (其他柱状图Tabs类似) ...

    # ------------------- 未转化客户深度分析 - 饼图 -------------------
    st.header("🥧 未转化客户深度分析 - 饼图")
    pie_tab1, pie_tab2, pie_tab3, pie_tab4, pie_tab5 = st.tabs([
        "❌ 无效线索**原因分布**", "📞 未转化线索**原因分布**", "👥 未转化客户**原因分布**", "🚫 未到访**原因分布**", "💸 未成交**原因分布**"
    ])
    
    with pie_tab1:
        fig_invalid_pie = create_pie_chart_for_reason(reasons_data['invalid'], "无效线索原因", cities)
        st.plotly_chart(fig_invalid_pie, use_container_width=True)
    
    # ... (其他饼图Tabs类似) ...


# 显示图表
if __name__ == "__main__":
    generate_charts()
    
# 操作提示
st.sidebar.markdown("---")
st.sidebar.success("✅ **请记住：** 在您修改数字后，务必点击上方的 **'生成最新的 standard_data.json 内容'** 按钮，并将结果复制粘贴回 GitHub！")
