import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly
import plotly.graph_objs as go
from plotly import tools
import pandas as pd
import sqlite3
# import flask
# from flask import g
from datetime import datetime

DATABASE = 'envdata.sqlite3'

app = dash.Dash()

db = sqlite3.connect(DATABASE)
db.row_factory = sqlite3.Row

def query_db(query, args=(), one=False):
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close
    return (rv[0] if rv else None) if one else rv

def init_db():
    with open('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

data = query_db('SELECT * FROM envdata ORDER BY read_at LIMIT 1440')
df = pd.DataFrame(data, columns=['read_at', 'pressure', 'temperature', 'humidity'])
timestamp = pd.to_datetime(df.iloc[:,0])
df['read_at'] = timestamp

app.layout = html.Div([
    html.Div(id='live-update-text'),
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=5 * 1000,  # in milliseconds
        n_intervals=0
    )
])

@app.callback(Output('live-update-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_text(n):
    style = {'padding': '5px', 'fontSize': '16px'}
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")


@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    layout = go.Layout(
        title='multiple y-axes example',
        width=800,
        xaxis=dict(
            domain=[0.2, 0.8]
        ),
        yaxis=dict(
            title='yaxis title',
            titlefont=dict(
                color='#1f77b4'
            ),
            tickfont=dict(
                color='#1f77b4'
            )
        ),
        yaxis2=dict(
            title='yaxis2 title',
            titlefont=dict(
                color='#ff7f0e'
            ),
            tickfont=dict(
                color='#ff7f0e'
            ),
            anchor='x',
            overlaying='y',
            side='right',
            # position=0.15
        ),
        yaxis3=dict(
            title='yaxis4 title',
            titlefont=dict(
                color='#d62728'
            ),
            tickfont=dict(
                color='#d62728'
            ),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        yaxis4=dict(
            title='yaxis5 title',
            titlefont=dict(
                color='#9467bd'
            ),
            tickfont=dict(
                color='#9467bd'
            ),
            anchor='free',
            overlaying='y',
            side='right',
            position=0.95
        )
    )

    trace1 = go.Scatter(
        x=df['read_at'],
        y=df['pressure'],
        # xaxis='x1',
        # yaxis='y1',
    )
    trace2 = go.Scatter(
        x=df['read_at'],
        y=df['temperature'],
        # xaxis='x2',
        # yaxis='y2',
    )
    trace3 = go.Scatter(
        x=df['read_at'],
        y=df['humidity'],
        # xaxis='x2',
        # yaxis='y3',
    )
    trace4 = go.Scatter(
        x=df['read_at'],
        y=df['humidity'],
        # xaxis='x2',
        # yaxis='y4',
    )

    fig = tools.make_subplots(rows=2, cols=1, shared_xaxes=True, horizontal_spacing=0.1, vertical_spacing=0.1)

    fig.append_trace(trace1, 1, 1)
    fig.append_trace(trace2, 2, 1)
    fig.append_trace(trace3, 2, 1)
    fig.append_trace(trace4, 1, 1)

    fig['layout'] = layout

    return fig


if __name__ == '__main__':
    app.run_server()
    db.close()