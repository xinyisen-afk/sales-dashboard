import streamlit as st
import pandas as pd
import numpy as np

# 网页标题
st.set_page_config(page_title="销售数据分析系统", layout="wide")
st.title("🎯 三城市销售数据分析系统")

# 侧边栏 - 数据输入
st.sidebar.header("📊 数据输入")
cost_per_lead = st.sidebar.number_input("单条线索成本(元)", value=320, min_value=0)

# 城市数据输入
st.sidebar.subheader("各城市转化数据")

cities_data = {}
cities = ['从化', '中山', '江门']
stages = ['线索量', '接通数', '有效数', '客户数', '到访数', '成交数']

default_values = {
    '从化': [21, 19, 17, 8, 4, 0],
    '中山': [30, 25, 20, 11, 0, 0], 
    '江门': [6, 6, 5, 5, 1, 0]
}

for city in cities:
    st.sidebar.write(f"**{city}转化数据**")
    values = []
    for i, stage in enumerate(stages):
        value = st.sidebar.number_input(
            f"{city}-{stage}", 
            value=default_values[city][i],
            key=f"{city}_{stage}"
        )
        values.append(value)
    cities_data[city] = values

# 生成图表函数
def generate_charts():
    # ==================== 汇总看板表格 ====================
    st.header("📈 数据汇总看板")
    
    summary_data = []
    for city in cities:
        values = cities_data[city]
        total_leads = values[0]
        valid_leads = values[2]
        clients = values[3]
        
        total_cost = total_leads * cost_per_lead
        valid_rate = (valid_leads / total_leads * 100) if total_leads > 0 else 0
        valid_lead_cost = total_cost / valid_leads if valid_leads > 0 else float('inf')
        client_cost = total_cost / clients if clients > 0 else float('inf')
        
        summary_data.append([
            city, total_leads, f"{valid_rate:.1f}%", f"{cost_per_lead:.0f}",
            f"{valid_lead_cost:.0f}" if valid_lead_cost != float('inf') else "无限大",
            f"{client_cost:.0f}" if client_cost != float('inf') else "无限大"
        ])

    summary_df = pd.DataFrame(summary_data, 
                             columns=['城市', '线索总量', '线索有效率', '线索成本', '线索有效成本', '客户成本'])
    st.dataframe(summary_df, use_container_width=True)

    # ==================== 成本分析 - 使用Streamlit原生图表 ====================
    st.header("💰 成本分析")
    
    # 创建成本数据
    cost_data = []
    for city in cities:
        values = cities_data[city]
        total_cost = values[0] * cost_per_lead
        
        costs = {
            '城市': city,
            '线索成本': cost_per_lead,
            '有效线索成本': total_cost / values[2] if values[2] > 0 else 0,
            '客户成本': total_cost / values[3] if values[3] > 0 else 0
        }
        cost_data.append(costs)
    
    cost_df = pd.DataFrame(cost_data).set_index('城市')
    st.bar_chart(cost_df)

    # ==================== 转化漏斗 - 使用水平条形图 ====================
    st.header("📊 转化漏斗分析")
    
    for city in cities:
        st.subheader(f"{city}转化漏斗")
        values = cities_data[city]
        
        # 创建漏斗数据
        funnel_data = pd.DataFrame({
            '阶段': stages,
            '数量': values
        }).set_index('阶段')
        
        # 使用水平条形图模拟漏斗
        st.bar_chart(funnel_data.T)  # 转置为水平显示

    # ==================== 线索量对比 ====================
    st.header("🔢 线索量对比")
    leads_data = pd.DataFrame({
        '城市': cities,
        '线索量': [cities_data[city][0] for city in cities]
    }).set_index('城市')
    st.bar_chart(leads_data)

# 显示图表
generate_charts()

# 刷新按钮
if st.sidebar.button("🔄 刷新图表"):
    generate_charts()
