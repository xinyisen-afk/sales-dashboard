import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_beautiful_funnel_chart(data, title="转化漏斗图"):
    """
    创建美观的漏斗图
    """
    stages = list(data.keys())
    values = list(data.values())
    
    # 方法1：渐变色的现代风格漏斗图
    fig1 = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        textposition="inside",
        marker={
            "color": values,
            "colorscale": "Blues",
            "line": {"width": 2, "color": "white"}
        },
        connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}},
        opacity=0.8
    ))
    
    fig1.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': 'darkblue'}
        },
        plot_bgcolor='rgba(240,240,240,0.8)',
        paper_bgcolor='white',
        font=dict(size=12),
        height=500
    )
    
    # 方法2：水平漏斗图
    fig2 = go.Figure(go.Funnel(
        x=values,
        y=stages,
        orientation="h",
        textinfo="value+percent previous",
        textposition="inside",
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
    
    # 方法3：带面积效果的漏斗图
    fig3 = go.Figure()
    
    # 添加漏斗区域
    fig3.add_trace(go.Funnelarea(
        text=stages,
        values=values,
        marker=dict(
            colors=px.colors.sequential.Plasma,
            line=dict(color='white', width=2)
        ),
        textinfo="label+value+percent initial",
        opacity=0.85
    ))
    
    fig3.update_layout(
        title={
            'text': f"<b>{title} - 面积视图</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        showlegend=False,
        height=500
    )
    
    return fig1, fig2, fig3

def create_animated_funnel(data, title="动态转化漏斗"):
    """
    创建带动画效果的漏斗图
    """
    stages = list(data.keys())
    values = list(data.values())
    
    fig = go.Figure()
    
    # 添加初始状态
    fig.add_trace(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        textposition="inside",
        marker={
            "color": values,
            "colorscale": "Viridis",
            "line": {"width": 2, "color": "white"}
        },
        opacity=0
    ))
    
    # 创建动画帧
    frames = []
    for i in range(len(values)):
        visible = [False] * len(values)
        visible[i] = True
        
        frames.append(go.Frame(
            data=[go.Funnel(
                y=stages[:i+1],
                x=values[:i+1],
                textinfo="value+percent initial",
                textposition="inside",
                marker={
                    "color": values[:i+1],
                    "colorscale": "Viridis",
                    "line": {"width": 2, "color": "white"}
                },
                opacity=0.8
            )],
            name=f"frame{i}"
        ))
    
    fig.frames = frames
    
    fig.update_layout(
        title={
            'text': f"<b>{title}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        updatemenus=[{
            "type": "buttons",
            "buttons": [
                {
                    "label": "播放",
                    "method": "animate",
                    "args": [None, {"frame": {"duration": 1000, "redraw": True}}]
                }
            ]
        }],
        height=500
    )
    
    return fig

# 在您的Streamlit应用中使用的示例
if __name__ == '__main__':
    import streamlit as st
    
    st.set_page_config(page_title="优化漏斗图", layout="wide")
    
    st.title("🎯 美观的转化漏斗图")
    
    # 示例数据
    sample_data = {
        "访问量": 10000,
        "产品浏览": 6500,
        "加入购物车": 3200,
        "发起结算": 1800,
        "完成支付": 1200
    }
    
    # 创建标签页显示不同类型的漏斗图
    tab1, tab2, tab3, tab4 = st.tabs(["现代风格", "水平视图", "面积视图", "动态效果"])
    
    with tab1:
        st.subheader("现代风格漏斗图")
        fig1, _, _ = create_beautiful_funnel_chart(sample_data, "用户转化漏斗")
        st.plotly_chart(fig1, use_container_width=True)
        
    with tab2:
        st.subheader("水平漏斗图")
        _, fig2, _ = create_beautiful_funnel_chart(sample_data, "用户转化漏斗")
        st.plotly_chart(fig2, use_container_width=True)
        
    with tab3:
        st.subheader("面积漏斗图")
        _, _, fig3 = create_beautiful_funnel_chart(sample_data, "用户转化漏斗")
        st.plotly_chart(fig3, use_container_width=True)
        
    with tab4:
        st.subheader("动态漏斗图")
        fig4 = create_animated_funnel(sample_data, "动态转化漏斗")
        st.plotly_chart(fig4, use_container_width=True)
    
    # 自定义数据输入
    st.sidebar.header("自定义漏斗数据")
    
    num_stages = st.sidebar.slider("阶段数量", 3, 8, 5)
    
    custom_data = {}
    for i in range(num_stages):
        stage_name = st.sidebar.text_input(f"阶段 {i+1} 名称", 
                                         value=["访问", "浏览", "加购", "结算", "支付"][i] 
                                         if i < 5 else f"阶段{i+1}")
        stage_value = st.sidebar.number_input(f"阶段 {i+1} 数值", 
                                            min_value=0, 
                                            value=[10000, 6500, 3200, 1800, 1200][i] 
                                            if i < 5 else 1000 - i*200)
        custom_data[stage_name] = stage_value
    
    if st.sidebar.button("生成自定义漏斗图"):
        st.subheader("自定义漏斗图")
        fig_custom, _, _ = create_beautiful_funnel_chart(custom_data, "自定义转化漏斗")
        st.plotly_chart(fig_custom, use_container_width=True)
