import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 完全不用中文字体设置
# 网页标题
st.set_page_config(page_title="Sales Analysis System", layout="wide")
st.title("🎯 Three Cities Sales Analysis System")

# 侧边栏 - 数据输入
st.sidebar.header("📊 Data Input")

# 成本输入
cost_per_lead = st.sidebar.number_input("Cost per Lead (Yuan)", value=320, min_value=0)

# 城市数据输入
st.sidebar.subheader("City Conversion Data")

cities_data = {}
cities = ['Conghua', 'Zhongshan', 'Jiangmen']
stages = ['Leads', 'Connected', 'Valid', 'Clients', 'Visits', 'Deals']

# 默认转化数据
default_values = {
    'Conghua': [21, 19, 17, 8, 4, 0],
    'Zhongshan': [30, 25, 20, 11, 0, 0], 
    'Jiangmen': [6, 6, 5, 5, 1, 0]
}

for city in cities:
    st.sidebar.write(f"**{city} Data**")
    values = []
    for i, stage in enumerate(stages):
        value = st.sidebar.number_input(
            f"{city}-{stage}", 
            value=default_values[city][i],
            key=f"{city}_{stage}"
        )
        values.append(value)
    
    cities_data[city] = {'stages': stages, 'values': values}

# 未转化原因数据输入
st.sidebar.subheader("Reasons for No Conversion")

reasons_categories = {
    'Conghua': ['Location', 'Unknown', 'Industry', 'Price'],
    'Zhongshan': ['Location', 'Unknown', 'Industry', 'Budget'],
    'Jiangmen': ['Following', 'Location', 'Unknown']
}

reasons_data = {}

for city in cities:
    st.sidebar.write(f"**{city} Reasons**")
    city_reasons = {}
    
    default_counts = {
        'Conghua': [6, 3, 3, 3],
        'Zhongshan': [3, 2, 2, 2],
        'Jiangmen': [1, 1, 2]
    }
    
    for j, reason in enumerate(reasons_categories[city]):
        value = st.sidebar.number_input(
            f"{city}-{reason}",
            value=default_counts[city][j],
            min_value=0,
            key=f"reason_{city}_{reason}"
        )
        city_reasons[reason] = value
    
    reasons_data[city] = city_reasons

# 生成图表函数
def generate_charts():
    # 颜色设置
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    reason_colors = ['#FF9999', '#99CCFF', '#99FF99', '#FFD700', '#C9A0FF']

    # ==================== 汇总看板表格 ====================
    st.header("📈 Data Summary Dashboard")
    
    # 计算汇总数据
    summary_data = []
    for city in cities:
        values = cities_data[city]['values']
        total_leads = values[0]
        valid_leads = values[2]
        clients = values[3]
        visits = values[4]
        deals = values[5]
        
        total_cost = total_leads * cost_per_lead
        lead_cost = cost_per_lead
        valid_lead_cost = total_cost / valid_leads if valid_leads > 0 else float('inf')
        client_cost = total_cost / clients if clients > 0 else float('inf')
        visit_cost = total_cost / visits if visits > 0 else float('inf')
        deal_cost = total_cost / deals if deals > 0 else float('inf')
        valid_rate = (valid_leads / total_leads * 100) if total_leads > 0 else 0
        
        summary_data.append([
            city, total_leads, f"{valid_rate:.1f}%", f"{lead_cost:.0f}",
            f"{valid_lead_cost:.0f}" if valid_lead_cost != float('inf') else "N/A",
            f"{client_cost:.0f}" if client_cost != float('inf') else "N/A",
            f"{visit_cost:.0f}" if visit_cost != float('inf') else "N/A",
            f"{deal_cost:.0f}" if deal_cost != float('inf') else "N/A"
        ])

    # 显示汇总表格
    summary_df = pd.DataFrame(summary_data, 
                             columns=['City', 'Total Leads', 'Valid Rate', 'Lead Cost', 
                                     'Valid Lead Cost', 'Client Cost', 'Visit Cost', 'Deal Cost'])
    st.dataframe(summary_df, use_container_width=True)

    # ==================== 成本柱状图 ====================
    st.header("💰 Cost Analysis")
    
    try:
        fig_cost, axes_cost = plt.subplots(1, 3, figsize=(18, 6))
        
        cost_labels = ['Leads', 'Connected', 'Valid', 'Clients', 'Visits', 'Deals']
        
        for i, city in enumerate(cities):
            values = cities_data[city]['values']
            total_cost = values[0] * cost_per_lead
            
            stage_costs = []
            stage_labels = []
            for j in range(len(values)):
                if values[j] > 0:
                    cost = total_cost / values[j]
                    stage_costs.append(cost)
                    stage_labels.append(f'{cost_labels[j]}\n({values[j]})')
            
            bars = axes_cost[i].bar(range(len(stage_costs)), stage_costs, color=colors[:len(stage_costs)], alpha=0.8)
            
            for bar, cost in zip(bars, stage_costs):
                height = bar.get_height()
                axes_cost[i].text(bar.get_x() + bar.get_width()/2., height + 20,
                                f'{cost:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
            
            axes_cost[i].set_title(f'{city}', fontsize=12, fontweight='bold')
            axes_cost[i].set_ylabel('Cost (Yuan)', fontsize=10)
            axes_cost[i].set_xticks(range(len(stage_labels)))
            axes_cost[i].set_xticklabels(stage_labels, fontsize=8, rotation=45)
            
            if stage_costs:
                axes_cost[i].set_ylim(0, max(stage_costs) * 1.2)
            
            axes_cost[i].spines['top'].set_visible(False)
            axes_cost[i].spines['right'].set_visible(False)
        
        st.pyplot(fig_cost)
        plt.close(fig_cost)
    except Exception as e:
        st.error(f"Cost chart error: {e}")

    # ==================== 漏斗图 ====================
    st.header("📊 Conversion Funnel Analysis")
    
    try:
        fig_funnel, axes_funnel = plt.subplots(1, 3, figsize=(18, 8))
        
        for i, city in enumerate(cities):
            values = cities_data[city]['values']
            stages_list = ['Leads', 'Connected', 'Valid', 'Clients', 'Visits', 'Deals']
            
            max_value = max(values)
            centered_values = [(max_value - value) / 2 for value in values]
            
            conversion_rates = []
            for j in range(len(values)):
                if j == 0:
                    conversion_rates.append(100.0)
                else:
                    rate = (values[j] / values[j-1]) * 100 if values[j-1] > 0 else 0
                    conversion_rates.append(rate)
            
            for j, (stage, value, centered_val) in enumerate(zip(stages_list, values, centered_values)):
                axes_funnel[i].barh(stage, value, left=centered_val, color=colors[j], alpha=0.8, height=0.6)
            
            axes_funnel[i].set_xlim(0, max_value + 2)
            axes_funnel[i].invert_yaxis()
            axes_funnel[i].set_xticks([])
            
            for j, (stage, value, rate, centered_val) in enumerate(zip(stages_list, values, conversion_rates, centered_values)):
                number_x = centered_val + value / 2
                percent_x = centered_val + value + 0.2
                
                axes_funnel[i].text(number_x, j, f'{value}', 
                                  va='center', ha='center', fontsize=10, fontweight='bold',
                                  color='white')
                
                if j > 0:
                    axes_funnel[i].text(percent_x, j, f'({rate:.1f}%)', 
                                      va='center', ha='left', fontsize=9, fontweight='bold',
                                      color='black')
                elif j == 0:
                    axes_funnel[i].text(percent_x, j, '(Base)', 
                                      va='center', ha='left', fontsize=9, fontweight='bold',
                                      color='black')
            
            axes_funnel[i].set_title(f'{city}', fontsize=12, fontweight='bold')
            
            for spine in axes_funnel[i].spines.values():
                spine.set_visible(False)
        
        st.pyplot(fig_funnel)
        plt.close(fig_funnel)
    except Exception as e:
        st.error(f"Funnel chart error: {e}")

    # ==================== 未转化客户原因分析 ====================
    st.header("❓ Reasons for No Conversion")
    
    try:
        fig_reason, axes_reason = plt.subplots(1, 3, figsize=(16, 5))
        
        for i, city in enumerate(cities):
            reason_data = reasons_data[city]
            reasons = list(reason_data.keys())
            counts = list(reason_data.values())
            
            bars = axes_reason[i].barh(reasons, counts, color=reason_colors[:len(reasons)], alpha=0.8, height=0.5)
            
            for bar, count in zip(bars, counts):
                width = bar.get_width()
                axes_reason[i].text(width + 0.05, bar.get_y() + bar.get_height()/2, 
                                  f'{count}', ha='left', va='center', fontsize=10, fontweight='bold')
            
            axes_reason[i].set_title(f'{city}', fontsize=12, fontweight='bold')
            axes_reason[i].set_xlabel('Count', fontsize=10)
            axes_reason[i].set_xlim(0, max(counts) + 1)
            
            axes_reason[i].set_xticks([])
            axes_reason[i].tick_params(left=False, labelsize=9)
            axes_reason[i].spines['top'].set_visible(False)
            axes_reason[i].spines['right'].set_visible(False)
            axes_reason[i].spines['bottom'].set_visible(False)
        
        plt.tight_layout(pad=2.0)
        st.pyplot(fig_reason)
        plt.close(fig_reason)
    except Exception as e:
        st.error(f"Reasons chart error: {e}")

# 默认显示图表
generate_charts()

# 刷新按钮
if st.sidebar.button("🔄 Refresh Charts"):
    generate_charts()
