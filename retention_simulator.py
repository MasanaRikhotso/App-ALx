
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.title("Incentive-Based Retention Strategy Simulator")

# Sidebar - Inputs
st.sidebar.header("Simulation Parameters")
initial_learners = st.sidebar.number_input("Initial number of learners", 100, 10000, 1000)
duration = st.sidebar.slider("Program duration (months)", 1, 24, 12)
dropoff_month3 = st.sidebar.slider("Drop-off rate in month 3 (%)", 0, 100, 30)
revenue_per_learner = st.sidebar.number_input("Monthly revenue per active learner ($)", 0.0, 100.0, 5.0)
incentive_cost = st.sidebar.number_input("Incentive cost per learner ($)", 0.0, 100.0, 5.0)
incentive_month = st.sidebar.slider("Incentive offered in month", 1, duration, 3)
retention_boost = st.sidebar.slider("Retention improvement from incentive (%)", 0, 100, 20)

uploaded_file = st.sidebar.file_uploader("Upload drop-off history CSV", type=["csv"])

# Load Data
def load_data():
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        # Create synthetic drop-off data
        month = np.arange(1, duration + 1)
        dropoff = np.linspace(10, 50, duration)
        dropoff[2] = dropoff_month3  # override for month 3
        df = pd.DataFrame({"month": month, "dropoff_rate": dropoff})
    return df

data = load_data()

# Simulate Retention Scenarios
def simulate_scenario(df, improved=False):
    learners = [initial_learners]
    for i in range(1, duration):
        rate = df.loc[i, 'dropoff_rate'] if i < len(df) else df['dropoff_rate'].mean()
        if improved and (i + 1) == incentive_month:
            rate *= (1 - retention_boost / 100)
        retained = learners[-1] * (1 - rate / 100)
        learners.append(retained)
    return learners

scenarios = {
    "Baseline (no incentive)": simulate_scenario(data, improved=False),
    "Incentive, no effect": simulate_scenario(data, improved=False),
    "Incentive, improved retention": simulate_scenario(data, improved=True)
}

# Calculate Metrics
def calculate_metrics(learners):
    gross_revenue = sum([l * revenue_per_learner for l in learners])
    incentive_total = learners[incentive_month - 1] * incentive_cost if 1 <= incentive_month <= len(learners) else 0
    net_revenue = gross_revenue - incentive_total
    return gross_revenue, incentive_total, net_revenue

# Display Results
metrics = {}
for key, learners in scenarios.items():
    gross, cost, net = calculate_metrics(learners)
    metrics[key] = {
        "learners": learners,
        "gross": gross,
        "cost": cost,
        "net": net
    }

# Summary Table
summary_df = pd.DataFrame([
    {
        "Scenario": key,
        "Gross Revenue ($)": round(val['gross'], 2),
        "Incentive Cost ($)": round(val['cost'], 2),
        "Net Revenue ($)": round(val['net'], 2),
        "Final Retention (%)": round((val['learners'][-1] / initial_learners) * 100, 2)
    }
    for key, val in metrics.items()
])

st.subheader("Business Metrics Summary")
st.dataframe(summary_df, use_container_width=True)

# Visualization
st.subheader("Retention Over Time")
chart_data = pd.DataFrame({"Month": np.arange(1, duration + 1)})
for key in scenarios:
    chart_data[key] = scenarios[key]

chart_data = chart_data.melt("Month", var_name="Scenario", value_name="Learners")

line_chart = alt.Chart(chart_data).mark_line().encode(
    x="Month",
    y="Learners",
    color="Scenario"
).properties(height=400)

st.altair_chart(line_chart, use_container_width=True)

st.markdown("""
### Notes:
- Drop-off data can be customized via CSV upload (columns: `month`, `dropoff_rate`).
- Incentives are assumed to be one-time costs applied at the selected month.
- This simulation is designed to explore high-level trends and ROI of retention interventions.
""")
