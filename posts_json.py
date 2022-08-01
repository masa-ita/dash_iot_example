import urllib.request
import json
import pandas as pd
import sqlite3
from time import sleep

clear_db = False

url = 'http://localhost:8000/api/v1.0/iot_data'
method = 'POST'
headers = { 'Content-Type': 'application/json'}

DATABASE = 'envdata.sqlite3'
if clear_db:
    db = sqlite3.connect(DATABASE)
    db.execute('DELETE FROM envdata')
    db.commit()
    db.close()
else:
    db = sqlite3.connect(DATABASE)
    cur = db.execute('SELECT max(read_at) as max_read_at FROM envdata')
    last_read_at = cur.fetchone()[0]
    db.close()


env_df = pd.read_csv("envdata.csv", names = ('read_at', 'pressure', 'temperature', 'humidity'))

for key, row in env_df.iterrows():
    if row['read_at'] > last_read_at:
        json_data = row.to_json().encode('utf-8')
        print(json_data)

        request = urllib.request.Request(url, data=json_data, method=method, headers=headers)

        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            print(response_body)

        sleep(3)
