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

standard_scaler = pickle.load(open('standard_scaler.pkl', 'rb'))

def query_db(query, args=(), one=False):
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close
    db.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    with open('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()

def add_db_entry(env_data):
    db = sqlite3.connect(DATABASE)
    db.execute('INSERT INTO envdata (read_at, pressure, temperature, humidity, p_ab, t_ab, h_ab)'\
               ' VALUES (?, ?, ?, ?, ?, ?, ?)', (env_data['read_at'],
                                        env_data['pressure'],
                                        env_data['temperature'],
                                        env_data['humidity'],
                                        env_data['p_ab'],
                                        env_data['t_ab'],
                                        env_data['h_ab']))
    db.commit()
    db.close()


def embed_ts(ts, size):
    length_of_ts = len(ts)
    ts_dim = ts.shape[1]

    data = []
    target = []

    for i in range(0, length_of_ts - size):
        data.append(ts[i: i + size])
        target.append(ts[i + size])

    X = np.array(data).reshape(len(data), size, ts_dim)
    Y = np.array(target).reshape(len(target), ts_dim)

    return X, Y

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    html.Div([
        html.H2('環境センサー　測定値'),
        html.Div(id='live-update-text'),
        dcc.RadioItems(
            id='live-switch',
            options=[
                {'label': 'Live', 'value': 'live'},
                {'label': 'Static', 'value': 'static'},
            ],
            value='live',
            labelStyle={'display': 'inline-block'}
        ),
        html.Button('Resume Updating', id='resume-update-button'),
        dcc.Graph(id='live-update-graph',
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
                  }
                  ),
        dcc.Interval(
            id='interval-component',
            interval=5*1000, # in milliseconds
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
    data = query_db('SELECT * FROM envdata ORDER BY read_at DESC LIMIT ?', (T,))
    df = pd.DataFrame(data, columns=['read_at', 'pressure', 'temperature', 'humidity', 'p_ab', 't_ab', 'h_ab'])
    timestamp = pd.to_datetime(df.iloc[:, 0])
    df['read_at'] = timestamp

    # Create the graph with subplots
    fig = plotly.tools.make_subplots(rows=3, cols=1, vertical_spacing=0.1, shared_xaxes=True)
    # fig['layout']['margin'] = {
    #     'l': 30, 'r': 10, 'b': 30, 't': 10
    # }
    # fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
    # fig['layout']['title'] = '環境センサー計測値'
    # fig['layout']['xaxis'] = {'title': '測定日時'}
    # fig['layout']['yaxis'] = {'title': '気圧'}
    # fig['layout']['yaxis2'] = {'title': '気温・湿度', 'overlaying': 'y', 'side': 'right'}

    trace1 = go.Scatter(x=df['read_at'], y=df['pressure'], name='気圧', xaxis='x1', yaxis='y1')
    trace2 = go.Scatter(x=df['read_at'], y=df['temperature'], name='気温', xaxis='x2', yaxis='y2')
    trace3 = go.Scatter(x=df['read_at'], y=df['humidity'], name='湿度', xaxis='x2', yaxis='y2')

    trace4 = go.Scatter(x=df['read_at'], y=df['p_ab'], name='気圧異常度', xaxis='x3', yaxis='y3')
    trace5 = go.Scatter(x=df['read_at'], y=df['t_ab'], name='気温異常度', xaxis='x3', yaxis='y3')
    trace6 = go.Scatter(x=df['read_at'], y=df['h_ab'], name='湿度異常度', xaxis='x3', yaxis='y3')

    fig['data'] = [trace1, trace2, trace3, trace4, trace5, trace6]

    return fig

@app.callback(Output('interval-component', 'interval'),
              [Input('live-switch', 'value'),
               Input('resume-update-button', 'n_clicks')])
def update_live_or_static(live_switch, n_clicks):
    if n_clicks and n_clicks > 0 or live_switch == 'live':
        return 5*1000
    else:
        return 0


@server.route('/api/v1.0/iot_data', methods=['POST'])
def api_iot_data_add():
    model = keras.models.model_from_json(open('env_cnn_model.json').read())
    model._make_predict_function()
    model.load_weights('env_cnn_weights.h5')
    env_data = request.json
    data = query_db('SELECT read_at, pressure, temperature, humidity FROM envdata ORDER BY read_at DESC LIMIT ?', (L,))
    last_df = pd.DataFrame(data, columns=['read_at', 'pressure', 'temperature', 'humidity'])
    last_df = last_df.append(env_data, ignore_index=True)
    last_ts = np.array(last_df.sort_values(by='read_at')[['pressure', 'temperature', 'humidity']])
    if last_ts.shape[0] == L + 1:
        last_ts = standard_scaler.transform(last_ts)
        X, Y = embed_ts(last_ts, L)
        Y_pred = model.predict(X)
        ab = sum((Y_pred - Y) ** 2)
        env_data['p_ab'] = ab[0]
        env_data['t_ab'] = ab[1]
        env_data['h_ab'] = ab[2]
    else:
        env_data['p_ab'] = None
        env_data['t_ab'] = None
        env_data['h_ab'] = None

    add_db_entry(env_data)
    return json.dumps({ 'status': 'OK'})

if __name__ == '__main__':
    app.run_server(debug=True)
