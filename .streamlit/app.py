import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 网页标题
st.set_page_config(page_title="销售数据分析系统", layout="wide")
st.title("🎯 销售数据分析看板")

# 侧边栏 - 数据输入
st.sidebar.header("📊 数据输入")
cost = st.sidebar.number_input("单条线索成本(元)", value=320)

# 简单数据显示
st.header("📈 销售数据概览")

data = {
    '城市': ['从化', '中山', '江门'],
    '线索量': [21, 30, 6],
    '接通数': [19, 25, 6],
    '有效数': [17, 20, 5],
    '客户数': [8, 11, 5],
    '到访数': [4, 0, 1],
    '成交数': [0, 0, 0]
}

df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True)

# 简单图表
st.header("📊 线索量对比")
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(data['城市'], data['线索量'], color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
ax.set_ylabel('线索数量')
st.pyplot(fig)

st.success("✅ 应用部署成功！")
