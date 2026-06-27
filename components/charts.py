import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# ---------- Global Theme ----------
def apply_dark_theme(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", family="Inter"),
        margin=dict(l=20, r=20, t=40, b=20),
        title_font_size=22,
        title_font_color="white",
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            color="#cbd5e1"
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
            color="#cbd5e1"
        ),
    )

    return fig


# ---------- Performance Line Chart ----------
def performance_chart(df):

    if len(df) == 0:
        return go.Figure()

    fig = px.line(
        df,
        x="Date",
        y="Score",
        markers=True
    )

    fig.update_traces(
        line=dict(
            color="#8b5cf6",
            width=4
        ),
        marker=dict(
            size=10,
            color="#06b6d4",
            line=dict(
                width=2,
                color="white"
            )
        )
    )

    fig.update_layout(
        title="📈 Interview Performance",
        height=380
    )

    return apply_dark_theme(fig)


# ---------- Skill Donut Chart ----------
def skill_chart():

    labels = [
        "Technical",
        "Communication",
        "Confidence",
        "Problem Solving",
        "Behavioral"
    ]

    values = [35, 20, 18, 15, 12]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=.72,
                marker=dict(
                    colors=[
                        "#8b5cf6",
                        "#06b6d4",
                        "#22c55e",
                        "#f59e0b",
                        "#ec4899"
                    ]
                )
            )
        ]
    )

    fig.update_layout(
        title="🎯 Skill Breakdown",
        height=380
    )

    return apply_dark_theme(fig)


# ---------- Weekly Activity ----------
def weekly_activity():

    days = [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun"
    ]

    interviews = [1, 2, 1, 3, 2, 4, 3]

    fig = px.bar(
        x=days,
        y=interviews
    )

    fig.update_traces(
        marker_color="#8b5cf6"
    )

    fig.update_layout(
        title="🔥 Weekly Activity",
        height=350
    )

    return apply_dark_theme(fig)


# ---------- Progress Gauge ----------
def progress_gauge(score=86):

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={
                "text": "Overall Readiness"
            },
            gauge={
                "axis": {
                    "range": [0, 100]
                },
                "bar": {
                    "color": "#8b5cf6"
                },
                "steps": [
                    {
                        "range": [0, 50],
                        "color": "#ef4444"
                    },
                    {
                        "range": [50, 75],
                        "color": "#f59e0b"
                    },
                    {
                        "range": [75, 100],
                        "color": "#22c55e"
                    }
                ]
            }
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=330,
        font=dict(
            color="white"
        )
    )

    return fig