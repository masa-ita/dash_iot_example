import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import sqlite3
import flask
from flask import g

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

data = query_db('SELECT * FROM envdata ORDER BY read_at')
df = pd.DataFrame(data, columns=['read_at', 'pressure', 'temperature', 'humidity'])
timestamp = pd.to_datetime(df.iloc[:,0])
df['read_at'] = timestamp

app.layout = html.Div([
    dcc.Graph(
        id='example-graph-2',
        figure={
            'data': [
                {'x': df['read_at'], 'y': df['pressure'], 'type': 'line', 'name': '気圧'},
                {'x': df['read_at'], 'y': df['temperature'], 'type': 'line', 'name': '気温', 'yaxis': 'y2'},
                {'x': df['read_at'], 'y': df['humidity'], 'type': 'line', 'name': '湿度', 'yaxis': 'y2'},
            ],
            'layout': {
                'title': '環境センサー計測値',
                'xaxis': {'title': '測定日時'},
                'yaxis': {'title': '気圧'},
                'yaxis2': {'title': '気温・湿度', 'overlaying': 'y', 'side': 'right'}
            },
            'config': {'editable': False, 'modeBarButtonsToRemove': ['sendDataToCloud']}
        }
    )
])

if __name__ == '__main__':
    app.run_server()
    db.close()