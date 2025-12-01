import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os 
from collections import defaultdict # 用于处理嵌套字典

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
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 使用 get() 避免键错误，提供合理的空默认值
            st.session_state.cities_data = data.get('cities_data', {city: [0]*6 for city in cities})
            st.session_state.reasons_data = data.get('reasons_data', defaultdict(dict))
            st.session_state.reason_labels = data.get('reason_labels', defaultdict(list))
            st.session_state.cost_per_lead = data.get('cost_per_lead', 320)
            st.sidebar.success("✅ 已从 GitHub 仓库加载标准数据。")
    except FileNotFoundError:
        st.sidebar.error(f"⚠️ 警告：未找到 {DATA_FILE} 文件。请在 GitHub 仓库中创建该文件。")
        # 文件不存在时，使用空数据初始化
        st.session_state.cities_data = {city: [0]*6 for city in cities}
        st.session_state.reasons_data = defaultdict(dict)
        st.session_state.reason_labels = defaultdict(list)
        st.session_state.cost_per_lead = 320
    except json.JSONDecodeError:
        st.sidebar.error(f"⚠️ 警告：{DATA_FILE} 文件格式错误，请检查 JSON 内容。")
        st.session_state.cities_data = {city: [0]*6 for city in cities}
        st.session_state.reasons_data = defaultdict(dict)
        st.session_state.reason_labels = defaultdict(list)
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
    
    # 从 session state 读取标签，如果 session state 中没有，则使用空列表
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
            
            # 使用保存的标签作为键来获取初始值，如果标签为空，则默认为 0
            initial_value = city_reason_data.get(label, 0)
            
            value = cols[i].number_input(
                f"{label} ({city})", 
                value=initial_value, 
                key=f"{stage_key}_{city}_{i}",
                min_value=0,
                label_visibility="collapsed" 
            )
            # 只有当标签非空时才保存数据
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

# ==================== 3. 开发者导出面板（实现部署环境下的保存） ====================

st.sidebar.markdown("---")
st.sidebar.header("🔑 开发者数据导出")
st.sidebar.info("**这是部署环境下的“保存”功能！** 点击按钮，复制主页面上生成的 JSON 内容，然后用于更新 GitHub 上的 `standard_data.json` 文件。")

# 点击按钮生成 JSON
if st.sidebar.button("✨ 生成最新的 standard_data.json 内容", type="primary"):
    
    json_output = serialize_data_for_export()
    
    # 在主页面使用 st.code 显示，方便用户复制
    st.header("📋 请复制以下 JSON 内容")
    st.warning("完成复制后，请前往 GitHub 仓库，编辑 standard_data.json 文件，并用以下内容覆盖它。")
    st.code(json_output, language='json', height=500)
    st.toast("JSON 内容已生成在主页面！", icon='🎉')


# ==================== 4. 主图表生成函数 (更新汇总看板) ====================

# 简化 Plotly 函数以保持代码简洁，请确保您本地的函数已定义
def create_beautiful_funnel(df): return px.bar()
def create_simple_reason_chart(df, title): return px.bar()
def create_pie_chart_for_reason(df, city, stage): return px.pie()


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
             visits = values[4] # 到访数量
             deals = values[5]
             
             total_cost = total_leads * cost_per_lead # 消费总数
             valid_rate = (valid_leads / total_leads * 100) if total_leads > 0 else 0
             valid_lead_cost = total_cost / valid_leads if valid_leads > 0 else 0
             client_cost = total_cost / clients if clients > 0 else 0
             visit_cost = total_cost / visits if visits > 0 else 0
             deal_cost = total_cost / deals if deals > 0 else 0
             
             summary_data.append({
                 '城市': city,
                 '线索总量': total_leads,
                 '**到访数量**': visits, # 新增
                 '线索有效率': f"{valid_rate:.1f}%",
                 '**消费总数**': f"¥{total_cost:,.0f}", # 新增
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
        
        csv_export = summary_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⬇️ 下载汇总看板数据 (CSV)",
            data=csv_export,
            file_name='销售数据汇总看板.csv',
            mime='text/csv',
        )

    # ------------------- 总转化漏斗图 -------------------
    with col2:
        st.header("📊 整体转化漏斗")
        
        # 计算整体数据
        total_data = [sum(cities_data[city][i] for city in cities) for i in range(len(stages))]
        funnel_df = pd.DataFrame({'阶段': stages, '数量': total_data})
        
        if total_data[0] > 0:
            fig = create_beautiful_funnel(funnel_df) # 假设此函数已定义
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("数据不足，无法生成整体漏斗图。")

    # ------------------- 城市数据分析 -------------------
    st.markdown("---")
    st.header("城市流失原因深度分析")
    
    # 假设此处是各个城市的详细图表和流失原因分析
    selected_city = st.selectbox("选择城市进行详细分析:", cities)
    
    # ... (此处应是您的详细图表逻辑) ...
    
    # 示例：显示该城市的转化数据
    st.subheader(f"城市: {selected_city} 转化明细")
    city_values = cities_data.get(selected_city, [0]*6)
    city_df = pd.DataFrame({'阶段': stages, '数量': city_values})
    st.dataframe(city_df, hide_index=True)
    
    # 示例：展示某个阶段的流失原因饼图
    if city_values[0] > 0:
        st.subheader(f"{selected_city} 无效线索原因分析")
        
        stage_key = 'invalid'
        city_reasons = reasons_data.get(stage_key, {}).get(selected_city, {})
        reason_df = pd.DataFrame(city_reasons.items(), columns=['原因', '数量'])
        
        if not reason_df.empty and reason_df['数量'].sum() > 0:
            pie_fig = create_pie_chart_for_reason(reason_df, selected_city, stage_key)
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("该城市该阶段无流失原因数据或数据总量为零。")


# ==================== 运行主函数 ====================
if __name__ == "__main__":
    generate_charts()
