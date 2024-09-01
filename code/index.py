from flask import Flask, request
import os
from http import HTTPStatus
from dashscope import Application
import dashscope
import json
from pymongo import MongoClient
import tldextract
from flask_cors import CORS
from collections import defaultdict
import requests
from sklearn.manifold import TSNE
import numpy as np

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
 
app = Flask(__name__)
CORS(app)
AI_API_KEY = os.environ.get('AI_API_KEY')
JINA_API_KEY = os.environ.get('JINA_API_KEY')
client = MongoClient(os.environ.get("MONGODB_URI"))
db = client['db']

original_categories = [
    "Books",
    "Business",
    "Developer Tools",
    "Education",
    "Entertainment",
    "Finance",
    "Food & Drink",
    "Games",
    "Graphics & Design",
    "Health & Fitness",
    "Lifestyle",
    "Kids",
    "Magazines & Newspapers",
    "Medical",
    "Music",
    "Navigation",
    "News",
    "Photo & Video",
    "Productivity",
    "Reference",
    "Shopping",
    "Social Networking",
    "Sports",
    "Travel",
    "Utilities",
    "Weather"
    ]

def extract_main_domain(url):
    ext = tldextract.extract(url)
    main_domain = f"{ext.domain}.{ext.suffix}"
    return main_domain

def get_topics_and_summary(message):
    response = Application.call(app_id='f788527999424bbf90474fdc382927c0',
                                prompt=message,
                                api_key=AI_API_KEY)

    if response.status_code != HTTPStatus.OK:
        return [], ""
    else:
        result = json.loads(response.output.text)
        return result['topics'], result['summary']

def get_categories(message):
    result = []
    response = Application.call(app_id='afe6e6c97c6b4229ae827cc53830a41b',
                                prompt=message,
                                api_key=AI_API_KEY)

    if response.status_code != HTTPStatus.OK:
        return result
    else:
        for category in original_categories:
            if category in response.output.text:
                result.append(category)
        
        return result
    
def get_minutes_saved(text_content):
    return len(text_content.split()) // 200

@app.route('/track', methods=['POST'])
def track():
    # 1. get text_content from request
    body = request.get_json()
    user_id = body['user_id']
    url = body['url']
    timestamp = body['timestamp']
    event_type = body['event_type']
    text_content = body['text_content']
    
    # 2. call qwen ai to generate categories, topics, summary, and minute saved (if event start)
    categories = []
    topics = []
    summary = ""
    minutes_saved = 0
    
    website_content = db['website_content'].find_one({'url': url})
    if website_content:
        topics, summary = website_content['topics'], website_content['summary']
        categories = website_content['categories']
    else:
        topics, summary = get_topics_and_summary(text_content)
        categories = get_categories(summary)
        
        db['website_content'].insert_one({
            'url': url,
            'categories': categories,
            'topics': topics,
            'summary': summary
        })
        
    minutes_saved = get_minutes_saved(text_content)
        
    # 3. put the data to user_activities database
    db['user_activity'].insert_one({
        'user_id': user_id,
        'url': url,
        'domain': extract_main_domain(url),
        'timestamp': timestamp,
        'event_type': event_type,
        'categories': categories,
        'topics': topics,
        'summary': summary
    })
    
    # 4. return the data
    return {
        "categories": categories,
        "topics": topics,
        "summary": summary,
        "minutes_saved": minutes_saved
    }
    
def get_domain_metrics(user_activities):
    label_type_map = defaultdict(dict)
    label_duration_map = defaultdict(int)
    for activity in user_activities:
        label = activity['domain']
        event_type = activity['event_type']
        timestamp = activity['timestamp']
        
        if "START" == event_type:
            duration = 0
            if 'END' in label_type_map[label] and 'START' in label_type_map[label]:
                duration = label_type_map[label]['END'] - label_type_map[label]['START']
                del label_type_map[label]['END'] 
            elif 'POLL' in label_type_map[label] and 'START' in label_type_map[label]:
                duration = label_type_map[label]['POLL'] - label_type_map[label]['START']
                del label_type_map[label]['POLL']
                
            label_duration_map[label] += duration
        label_type_map[label][event_type] = timestamp
    
    return {
        "total_duration_seconds": sum([value for value in label_duration_map.values() if value > 0]),
        "items": [{"label": key, "duration_seconds": value} for key, value in label_duration_map.items() if value > 0]
        }
    
def get_category_metrics(user_activities):
    label_type_map = defaultdict(dict)
    label_duration_map = defaultdict(int)
    for activity in user_activities:
        label = activity['categories'][0] if len(activity['categories']) > 0 else 'Other'
        event_type = activity['event_type']
        timestamp = activity['timestamp']
        
        if "START" == event_type:
            duration = 0
            if 'END' in label_type_map[label] and 'START' in label_type_map[label]:
                duration = label_type_map[label]['END'] - label_type_map[label]['START']
                del label_type_map[label]['END'] 
            elif 'POLL' in label_type_map[label] and 'START' in label_type_map[label]:
                duration = label_type_map[label]['POLL'] - label_type_map[label]['START']
                del label_type_map[label]['POLL']
                
            label_duration_map[label] += duration
        label_type_map[label][event_type] = timestamp
    
    return {
        "total_duration_seconds": sum([value for value in label_duration_map.values() if value > 0]),
        "items": [{"label": key, "duration_seconds": value} for key, value in label_duration_map.items() if value > 0]
        }
    

@app.route('/metrics', methods=['POST'])
def metrics():
    body = request.get_json()
    user_id = body['user_id']
    start_time = body['start_time']
    end_time = body['end_time']
    type = body['type']
    
    user_activities = list(db['user_activity'].find({
        "user_id": user_id,
        "timestamp": {"$gte": start_time, "$lt": end_time}
    }).sort('timestamp', 1))
    
    days = []
    seconds_per_day = 24 * 60 * 60
    left = start_time
    for right in range(start_time+seconds_per_day, end_time+1, seconds_per_day):
        metrics = {}
        if "CATEGORY" == type:
            metrics = get_category_metrics([activity for activity in user_activities if left <= activity['timestamp'] <= right])
        else:
            metrics = get_domain_metrics([activity for activity in user_activities if left <= activity['timestamp'] <= right])
        days.append(metrics)
        left = right
            
    return {
        "days": days
    }

def generate_embeddings(texts):
    url = 'https://api.jina.ai/v1/embeddings'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + JINA_API_KEY
    }
    payload = {
        "model": "jina-embeddings-v2-base-en",
        "normalized": True,
        "embedding_type": "float",
        "input": texts
    }

    response = requests.post(url, headers=headers, json=payload)
    
    return np.array([item['embedding'] for item in response.json()['data']])
    

@app.route('/metrics/topics', methods=['POST'])
def metrics_topics():
    body = request.get_json()
    user_id = body['user_id']
    start_time = body['start_time']
    end_time = body['end_time']
    
    user_activities = db['user_activity'].find({
        "user_id": user_id,
        "timestamp": {"$gte": start_time, "$lt": end_time},
        "event_type": "START"
    })
    
    text_set = set()
    
    for activity in user_activities:
        if 'topics' in activity:
            for topic in activity['topics']:
                text_set.add(topic)
                
    texts = list(text_set)
    
    embeddings = generate_embeddings(texts)
    
    perplexity = len(texts) / 100
    tsne = TSNE(n_components=3, random_state=42, perplexity=perplexity)
    embeddings_3d = tsne.fit_transform(embeddings).tolist()
    
    return {
        "points": [{"label": texts[i], "x": embeddings_3d[i][0], "y": embeddings_3d[i][1], "z": embeddings_3d[i][2], "size": 1} for i in range(len(texts))]
    }

@app.route('/')
def index():
    return 'HEALTHY'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
