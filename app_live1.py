import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import datetime
import plotly
import plotly.graph_objs as go
import sqlite3
import pandas as pd

DATABASE = 'envdata.sqlite3'

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

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    html.Div([
        html.H4('TERRA Satellite Live Feed'),
        html.Div(id='live-update-text'),
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=3*1000, # in milliseconds
            n_intervals=0
        )
    ])
)


@app.callback(Output('live-update-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_text(n):
    style = {'padding': '5px', 'fontSize': '16px'}
    return html.Span(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


# Multiple components can update everytime interval gets fired.
@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    data = {
        'read_at': df['read_at'],
        'pressure': df['pressure'],
        'temperature': df['temperature'],
        'humidity': df['humidity']
    }

    # Create the graph with subplots
    # fig = plotly.tools.make_subplots(rows=1, cols=1)
    fig = go.Figure()
    # fig['layout']['margin'] = {
    #     'l': 30, 'r': 10, 'b': 30, 't': 10
    # }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
    fig['layout']['title'] = '環境センサー計測値'
    fig['layout']['xaxis'] = {'title': '測定日時'}
    fig['layout']['yaxis'] = {'title': '気圧'}
    fig['layout']['yaxis2'] = {'title': '気温・湿度', 'overlaying': 'y', 'side': 'right'}

    trace0 = go.Scatter(x=data['read_at'], y=data['pressure'], name='気圧')
    trace1 = go.Scatter(x=data['read_at'], y=data['temperature'], name='気温', yaxis='y2')
    trace2 = go.Scatter(x=data['read_at'], y=data['humidity'], name='湿度', yaxis='y2')
    fig['data'] = [trace0, trace1, trace2]

    return fig

@server.route('/api')
def api():
    return "API test"

if __name__ == '__main__':
    app.run_server(debug=True)
