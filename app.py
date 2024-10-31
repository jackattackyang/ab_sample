import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import norm
import math
import plotly.express as px
import plotly.graph_objects as go



st.set_page_config(
    page_title="Sample Size Calculator",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

st.title('A/B Test Sample Size Calculator')

st.sidebar.header('Parameters')
p1 = st.sidebar.number_input('Baseline Conversion Rate (%)', value=20.0, step=1.0,
        format="%.2f",)
mde = st.sidebar.number_input('Minimum Detectable Effect (%)', value=5.0, step=1.0, format="%.2f",)
mde_type = st.sidebar.radio("Effect Type", ["Absolute", "Relative"])


power = st.sidebar.slider(
    'Statistical Power (1-β): ',
    min_value=65,
    max_value=95,
    value=80,
    step=5,
    key='beta',
    format="%.0f%%",
    help='Percent of time when the minimum effect size will be detected, assuming it exists.',
)
alpha = st.sidebar.slider(
    'Significance level (α): ',
    min_value=1,
    max_value=10,
    value=5,
    step=1,
    key='alpha',
    format="%.0f%%",
    help='Percent of time when a difference will be detected, assuming NONE exists. Also known as false positive or type I error',
)
st.sidebar.markdown("Reference: [Evan Miller's Online A/B Testing Tools](https://www.evanmiller.org/ab-testing/sample-size.html)")

alpha /= 100
power /= 100
p1 /= 100
mde /= 100
if mde_type == 'Absolute':
    p2 = p1 + mde
else:
    p2 = p1 * (1+mde)

n2 = 0.5
n1 = 1-n2
k = n1 / n2

p_pooled = (p1+p2)/2
pooled_var = p_pooled * (1-p_pooled) * (1+1/k)
var_1 = p1 * (1-p1)
var_2 = p2 * (1-p2)
individual_var = var_1 + var_2
z_alpha = stats.norm.ppf(1 - alpha / 2)
z_beta = stats.norm.ppf(power)
n2 = ((z_alpha * math.sqrt(pooled_var) + z_beta * math.sqrt(individual_var)) / abs(p1-p2))**2
n1 = n2*k

col1, col2, col3 = st.columns([1, 1, 1])  # Adjust ratios to center properly
with col2:
    st.write(f"## {n1:.0f}")
    st.caption("Sample size per variation")

std_dev_null = math.sqrt(p_pooled * (1-p_pooled) * (1/n1+1/n2))
std_dev_alternate = math.sqrt(var_1 / n1 + var_2 / n2)
x = np.linspace(p1 - 4 * std_dev_null, p2 + 4 * std_dev_alternate, 1000)

# PDFs of normal distributions using scipy.stats
y1 = norm.pdf(x, loc=p1, scale=std_dev_null)
# y1 = norm.pdf(x)*individual_var + p2-p1
y2 = norm.pdf(x, loc=p2, scale=std_dev_alternate)

df = pd.DataFrame({'x': np.concatenate([x, x]),
                   'y': np.concatenate([y1, y2]),
                   'Distribution': ['Null'] * len(x) + ['Alternate'] * len(x)})

fig = px.line(df, x='x', y='y', color='Distribution', title='Two Sided Distribution', labels={'x': 'x', 'y': 'Probability Density'})

crit_value = z_alpha * std_dev_null + p1
crit_value_left = p1 - z_alpha * std_dev_null 
fig.add_vline(x=crit_value, line=dict(color='red', dash='dash'))
fig.add_annotation(x=crit_value, y=-0.03, text=f'{crit_value:.2f}', showarrow=False, yanchor='top', font=dict(size=12), xshift=-5)
fig.add_vline(x=crit_value_left, line=dict(color='red', dash='dash'))
fig.add_annotation(x=crit_value_left, y=-0.03, text=f'{crit_value_left:.2f}', showarrow=False, yanchor='top', font=dict(size=12), xshift=-5)


null_dist_values = norm.pdf(x, p1, std_dev_null)
alt_dist_values = norm.pdf(x, p2, std_dev_alternate)
rejection_data = pd.DataFrame({
    'x': x[x >= crit_value],
    'y_null': null_dist_values[x >= crit_value],
    'y_alt': alt_dist_values[x >= crit_value]
})

fig.add_scatter(x=rejection_data['x'], y=rejection_data['y_null'], fill='tonexty', mode='lines',
                name='Rejection Region (alpha)', fillcolor='rgba(0, 0, 255, 0.2)', line=dict(color='blue', width=0),
                showlegend=True)

# Adding power region under H1 (1 - beta)
fig.add_scatter(x=rejection_data['x'], y=rejection_data['y_alt'], fill='tonexty', mode='lines',
                name='Power (1 - beta)', fillcolor='rgba(0, 128, 0, 0.3)', line=dict(color='green', width=0),
                showlegend=True)

# Update layout for legend
fig.update_layout(
    legend=dict(x=0.7, y=0.95), 
    template='plotly_white'
    )
st.plotly_chart(fig)