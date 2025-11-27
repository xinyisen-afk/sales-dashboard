import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_beautiful_funnel_chart(data, title="转化漏斗图"):
    """
    创建美观的漏斗图
    """
    stages = list(data.keys())
    values = list(data.values())
    
    # 计算转化率
    total = values[0]
    conversion_rates = [f"{(v/total*100):.1f}%" for v in values]
    
    # 方法1：渐变色的现代风格漏斗图
    fig1 = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        marker={
            "color": values,
            "colorscale": "Blues",
            "line": {"width": 2, "color": "white"}
        },
        connector={"line": {"color": "royalblue", "dash": "dot", "width": 2}},
        opacity=0.85
    ))
    
    fig1.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': 'darkblue'}
        },
        plot_bgcolor='rgba(248,248,248,0.8)',
        paper_bgcolor='white',
        font=dict(size=12),
        height=500,
        margin=dict(t=80, b=50, l=50, r=50)
    )
    
    # 方法2：水平漏斗图
    fig2 = go.Figure(go.Funnel(
        x=values,
        y=stages,
        orientation="h",
        textposition="inside",
        textinfo="value+percent previous",
        marker={
            "color": px.colors.sequential.Viridis,
            "line": {"width": 2, "color": "white"}
        }
    ))
    
    fig2.update_layout(
        title={
            'text': f"<b>{title} - 水平视图</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        plot_bgcolor='white',
        font=dict(size=12),
        height=400
    )
    
    # 方法3：简单的面积图替代方案
    fig3 = go.Figure()
    
    # 使用饼图样式但保持漏斗逻辑
    fig3.add_trace(go.Bar(
        x=[1] * len(stages),  # 固定宽度
        y=values,
        text=[f"{stage}<br>{value} ({rate})" for stage, value, rate in zip(stages, values, conversion_rates)],
        textposition='auto',
        orientation='v',
        marker=dict(
            color=px.colors.sequential.Plasma,
            line=dict(color='white', width=2)
        ),
        opacity=0.85
    ))
    
    fig3.update_layout(
        title={
            'text': f"<b>{title} - 柱状视图</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        showlegend=False,
        xaxis=dict(showticklabels=False),
        yaxis=dict(title="数量"),
        height=500
    )
    
    return fig1, fig2, fig3

def create_custom_funnel(data, title="转化漏斗图", style="default"):
    """
    创建自定义风格的漏斗图
    """
    stages = list(data.keys())
    values = list(data.values())
    
    if style == "modern":
        # 现代商务风格
        colors = px.colors.sequential.Blues
        bg_color = 'rgba(240,240,240,0.8)'
    elif style == "vibrant":
        # 活力色彩风格
        colors = px.colors.sequential.Viridis
        bg_color = 'white'
    else:
        # 默认风格
        colors = px.colors.sequential.Plotly3
        bg_color = 'rgba(248,248,248,0.8)'
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        textposition="inside",
        textfont=dict(size=14, color="white"),
        marker={
            "color": values,
            "colorscale": colors,
            "line": {"width": 3, "color": "white"}
        },
        connector={"line": {"color": "gray", "width": 2}},
        opacity=0.9
    ))
    
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 22, 'color': 'darkblue', 'family': 'Arial'}
        },
        plot_bgcolor=bg_color,
        paper_bgcolor='white',
        font=dict(size=12, family='Arial'),
        height=550,
        margin=dict(t=80, b=60, l=80, r=80),
        annotations=[
            dict(
                x=0.5,
                y=-0.15,
                xref='paper',
                yref='paper',
                text=f"总转化率: {(values[-1]/values[0]*100):.1f}%",
                showarrow=False,
                font=dict(size=14, color='darkred')
            )
        ]
    )
    
    return fig

def create_funnel_with_metrics(data, title="转化漏斗分析"):
    """
    创建带详细指标的漏斗图
    """
    stages = list(data.keys())
    values = list(data.values())
    
    # 计算各项指标
    total_users = values[0]
    conversion_rates = [f"{(v/total_users*100):.1f}%" for v in values]
    stage_conversion = []
    for i in range(1, len(values)):
        rate = (values[i] / values[i-1] * 100) if values[i-1] > 0 else 0
        stage_conversion.append(f"{rate:.1f}%")
    
    # 创建主漏斗图
    fig = go.Figure()
    
    fig.add_trace(go.Funnel(
        name="用户数量",
        y=stages,
        x=values,
        textinfo="value+percent initial",
        textposition="inside",
        marker={
            "color": values,
            "colorscale": "Teal",
            "line": {"width": 3, "color": "white"}
        },
        opacity=0.85
    ))
    
    # 添加阶段转化率标注
    annotations = []
    for i, (rate, stage) in enumerate(zip(stage_conversion, stages[1:], strict=False)):
        annotations.append(
            dict(
                x=0.95,
                y=i+1,
                xref="paper",
                yref="y",
                text=f"阶段转化: {rate}",
                showarrow=False,
                bgcolor="lightyellow",
                bordercolor="black",
                borderwidth=1,
                font=dict(size=11, color="black")
            )
        )
    
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': 'darkblue'}
        },
        plot_bgcolor='rgba(240,240,240,0.5)',
        paper_bgcolor='white',
        font=dict(size=12, family='Arial'),
        height=600,
        margin=dict(t=100, b=80, l=100, r=100),
        annotations=annotations
    )
    
    return fig

# 在您的Streamlit应用中使用的示例
if __name__ == '__main__':
    import streamlit as st
    
    st.set_page_config(page_title="优化漏斗图", layout="wide")
    
    st.title("🎯 美观的转化漏斗图优化版")
    
    # 示例数据
    sample_data = {
        "访问量": 10000,
        "产品浏览": 6500,
        "加入购物车": 3200,
        "发起结算": 1800,
        "完成支付": 1200
    }
    
    # 样式选择
    st.sidebar.header("🎨 图表样式设置")
    chart_style = st.sidebar.selectbox(
        "选择图表风格",
        ["default", "modern", "vibrant"],
        format_func=lambda x: {
            "default": "默认风格", 
            "modern": "现代商务", 
            "vibrant": "活力色彩"
        }[x]
    )
    
    # 创建标签页显示不同类型的漏斗图
    tab1, tab2, tab3 = st.tabs(["主要漏斗图", "详细分析", "自定义样式"])
    
    with tab1:
        st.subheader("主要转化漏斗")
        fig1, fig2, fig3 = create_beautiful_funnel_chart(sample_data, "用户转化漏斗")
        st.plotly_chart(fig1, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            st.plotly_chart(fig3, use_container_width=True)
        
    with tab2:
        st.subheader("详细转化分析")
        fig_detailed = create_funnel_with_metrics(sample_data, "详细转化分析")
        st.plotly_chart(fig_detailed, use_container_width=True)
        
    with tab3:
        st.subheader("自定义样式漏斗图")
        fig_custom = create_custom_funnel(sample_data, "自定义样式漏斗", style=chart_style)
        st.plotly_chart(fig_custom, use_container_width=True)
    
    # 自定义数据输入
    st.sidebar.header("📊 自定义数据")
    
    num_stages = st.sidebar.slider("阶段数量", 3, 8, 5)
    
    custom_data = {}
    default_names = ["访问", "浏览", "加购", "结算", "支付", "复购", "推荐", "忠诚"]
    default_values = [10000, 6500, 3200, 1800, 1200, 800, 400, 200]
    
    for i in range(num_stages):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            stage_name = st.text_input(
                f"阶段 {i+1}", 
                value=default_names[i] if i < len(default_names) else f"阶段{i+1}",
                key=f"name_{i}"
            )
        with col2:
            stage_value = st.number_input(
                f"数值", 
                min_value=0, 
                value=default_values[i] if i < len(default_values) else 1000 - i*150,
                key=f"value_{i}"
            )
        custom_data[stage_name] = stage_value
    
    if st.sidebar.button("生成自定义漏斗图", type="primary"):
        st.subheader("自定义漏斗图结果")
        fig_custom_main = create_custom_funnel(custom_data, "自定义转化漏斗", style=chart_style)
        st.plotly_chart(fig_custom_main, use_container_width=True)
        
        # 显示转化率统计
        st.subheader("转化率统计")
        values = list(custom_data.values())
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总转化率", f"{(values[-1]/values[0]*100):.2f}%")
        with col2:
            st.metric("最终转化人数", f"{values[-1]:,}")
        with col3:
            st.metric("流失人数", f"{(values[0]-values[-1]):,}")
