import requests
import json
from dotenv import load_dotenv
import os
import ipdb
import traceback
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()

notion_token = os.environ.get("NOTION_TOKEN")
database_id = os.environ.get("NOTION_DB_ID")
headers = {
    "Authorization": "Bearer " + notion_token,
    "Content-Type": "application/json",
    "Notion-Version": "2021-05-13"
}


def get_lap_time(result, key):
    if len(result['properties'][f'{key}']['rich_text']) > 0:
        value = result['properties'][f'{key}']['rich_text'][0]['plain_text']
        return value
    else:
        return '00:00'

def convert_db_to_dict(db_json):
    results = db_json['results']
    
    db_dict = []
    for result in results:
        try:
            temp = {
                'date': result['properties']['Date']['title'][0]['plain_text'],
                'lap1': get_lap_time(result, 'Lap 1'),
                'lap2': get_lap_time(result, 'Lap 2'),
                'lap3': get_lap_time(result, 'Lap 3'),
                'sprint': get_lap_time(result, 'Sprint'),
                'set1': result['properties'].get('Set 1', {}).get('number', 0),
                'set2': result['properties'].get('Set 2', {}).get('number', 0),
                'set3': result['properties'].get('Set 3', {}).get('number', 0)
            }
            # db_dict[result['properties']['Date']['title'][0]['plain_text']] = temp
            db_dict.append(temp)
        except:
            print(traceback.print_exc())
    
    db_dict.sort(key = lambda x: datetime.strptime(x['date'], '%d-%b-%Y'))
    return db_dict


def dict_to_df(db_dict):
    df = pd.DataFrame(db_dict)
    df['total running'] = pd.to_timedelta('00:' + df['lap1']) + pd.to_timedelta('00:' + df['lap2']) + pd.to_timedelta('00:' + df['lap3']) + pd.to_timedelta('00:' + df['sprint'])
    df['total running'] = df['total running'].dt.seconds.div(60).astype(int).astype(str).str.zfill(2) + ':' + df['total running'].dt.seconds.mod(60).astype(str).str.zfill(2)
    df['total pushups'] = df['set1'] + df['set2'] + df['set3']
    return df


# https://prettystatic.com/notion-api-python/
def read_db(database_id, headers):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    
    res = requests.request("POST", url, headers=headers)
    data = res.json()
    # print(res.status_code)

    # with open('./db.json', 'w', encoding='utf8') as f:
    #     json.dump(data, f, ensure_ascii=False)
    return data


def plot_data(df):
    # Convert lap times to seconds
    df['lap1_sec'] = pd.to_timedelta('00:' + df['lap1']).dt.total_seconds()
    df['lap2_sec'] = pd.to_timedelta('00:' + df['lap2']).dt.total_seconds()
    df['lap3_sec'] = pd.to_timedelta('00:' + df['lap3']).dt.total_seconds()
    df['sprint_sec'] = pd.to_timedelta('00:' + df['sprint']).dt.total_seconds()

    # Calculate total running time and total pushups
    df['total_running_sec'] = df['lap1_sec'] + df['lap2_sec'] + df['lap3_sec'] + df['sprint_sec']
    df['total_pushups'] = df['set1'] + df['set2'] + df['set3']

    # Plot the data
    fig, ax = plt.subplots()
    df.plot(x='date', y='total_running_sec', kind='bar', ax=ax)
    df.plot(x='date', y='total_pushups', kind='line', ax=ax, secondary_y=True)
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Running Time (seconds)')
    ax.right_ax.set_ylabel('Total Pushups')
    plt.show()


data = read_db(database_id, headers)
db_dict = convert_db_to_dict(data)
db_df = dict_to_df(db_dict)
plot_data(db_df)
# print(db_df)
