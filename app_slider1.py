import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import datetime
import plotly
import plotly.graph_objs as go
import sqlite3
import pandas as pd
from flask import request, json
import pickle
from sklearn.preprocessing import StandardScaler
from tensorflow import keras
import numpy as np

DATABASE = 'envdata.sqlite3'
T = 1440
L = 144
INTERVAL = 5


def query_db(query, args=(), one=False):
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close
    db.close()
    return (rv[0] if rv else None) if one else rv


envdata = query_db("SELECT * FROM envdata")

df = pd.read_sql("SELECT * FROM envdata", sqlite3.connect(DATABASE))

timestamp = pd.to_datetime(df.iloc[:,0])
env_ts = df.iloc[:,1:4]
env_ts.index = timestamp
print(env_ts)

trace=go.Scatter(x=env_ts.index, y=env_ts.pressure)
data = [trace]
layout = dict(
    title='環境データ測定値',
    autosize=True,
    height=800,
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label='1ヶ月',
                     step='month',
                     stepmode='backward'),
                dict(count=7,
                     label='1週間',
                     step='day',
                     stepmode='backward'),
                dict(count=24,
                     label='最近24時間',
                     step='hour',
                     stepmode='todate'),
                dict(count=1,
                     label='1日',
                     step='day',
                     stepmode='backward'),
                dict(step='all')
            ])
        ),
        rangeslider=dict(),
        type='date'
    )
)
fig = plotly.tools.make_subplots(rows=3, cols=1, vertical_spacing=0.2, shared_xaxes=True)
trace1 = go.Scatter(x=env_ts.index, y=env_ts.pressure, yaxis='y1')
trace2 = go.Scatter(x=env_ts.index, y=env_ts.temperature, yaxis='y3')
trace3 = go.Scatter(x=env_ts.index, y=env_ts.humidity, yaxis='y3')
data = [trace1, trace2, trace3]
fig = dict(data=data, layout=layout)


app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    html.Div([
        html.H2('環境センサー　測定値'),
        dcc.Graph(id='graph',
                  config={
                      'modeBarButtonsToRemove': [
                      'sendDataToCloud',
                      'pan2d',
                      'zoomIn2d',
                      'zoomOut2d',
                      'autoScale2d',
                      'resetScale2d',
                      'hoverCompareCartesian',
                      'hoverClosestCartesian',
                      'toggleSpikelines'
                      ],
                      'displayModeBar': True,
                      'displaylogo': False
                  },
                  figure = fig,
                  ),
    ])
)


if __name__ == '__main__':
    app.run_server(debug=True)
