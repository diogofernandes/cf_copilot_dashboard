"""
charts/plotly_charts.py — Plotly figure builders for the dashboard.
"""

import plotly.graph_objects as go

from dashboard.constants import RISK_COLORS


def build_cashflow_chart(df):
    """Bar + line combo chart for weekly cashflow forecast."""
    df = df.copy().sort_values("week_bucket")
    df["label"] = df["week_bucket"].apply(lambda x: f"Week {x}")
    df["cum"] = df["forecast_cash"].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["label"],
        y=df["forecast_cash"] / 1e6,
        name="Weekly ($M)",
        marker_color="rgba(0,212,170,0.6)",
        marker_line_color="rgba(0,212,170,1)",
        marker_line_width=1,
    ))
    fig.add_trace(go.Scatter(
        x=df["label"],
        y=df["cum"] / 1e6,
        name="Cumulative ($M)",
        line=dict(color="#4d9fff", width=2),
        mode="lines+markers",
        marker=dict(size=6),
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#6b7fa3", family="Inter"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#6b7fa3"),
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color="#6b7fa3"),
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color="#6b7fa3"),
            title="Amount ($M)",
            title_font=dict(color="#6b7fa3"),
        ),
        margin=dict(l=0, r=0, t=40, b=60),
        height=340,
        modebar=dict(
            orientation="h",
            bgcolor="rgba(0,0,0,0)",
            color="#3d5278",
            activecolor="#00d4aa",
        ),
    )
    return fig


def build_risk_gauge(probability: float):
    value = max(0, min(1, probability)) * 100
    color = "#00d4aa" if probability < .2 else "#ffa94d" if probability < .5 else "#ff4d6d"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, number={"suffix": "%", "font": {"color": color, "size": 28}},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={"axis": {"range": [0, 100], "tickfont": {"color": "#6b7fa3", "size": 10}},
               "bar": {"color": color}, "bgcolor": "rgba(255,255,255,0.03)",
               "bordercolor": "rgba(255,255,255,0.1)",
               "steps": [{"range": [0, 20], "color": "rgba(0,212,170,0.1)"},
                         {"range": [20, 50], "color": "rgba(255,169,77,0.1)"},
                         {"range": [50, 100], "color": "rgba(255,77,109,0.1)"}]}))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={"family": "Inter"},
                      margin={"l": 10, "r": 10, "t": 10, "b": 10}, height=160)
    return fig
