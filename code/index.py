from flask import Flask, request
import os
from http import HTTPStatus
from dashscope import Application
import dashscope
import json
from pymongo import MongoClient
import tldextract
from flask_cors import CORS

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
 
app = Flask(__name__)
CORS(app)
AI_API_KEY = os.environ.get('AI_API_KEY')
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
    print(os.environ.get("MONGODB_URI"))
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
    if event_type == "START":
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

@app.route('/metrics', methods=['POST'])
def metrics():
    return {
        "days": [
            {
            "day": "Monday",
            "total_duration_seconds": 12345,
            "items": [
                {
                "label": "stackoverflow.com",
                "duration_seconds": 3600
                },
                {
                "label": "github.com",
                "duration_seconds": 1800
                },
                {
                "label": "news.ycombinator.com",
                "duration_seconds": 900
                }
            ]
            },
            {
            "day": "Tuesday",
            "total_duration_seconds": 9876,
            "items": [
                {
                "label": "medium.com",
                "duration_seconds": 1500
                },
                {
                "label": "dev.to",
                "duration_seconds": 1200
                },
                {
                "label": "youtube.com",
                "duration_seconds": 2700
                }
            ]
            },
            {
            "day": "Wednesday",
            "total_duration_seconds": 11111,
            "items": [
                {
                "label": "reddit.com/r/programming",
                "duration_seconds": 2400
                },
                {
                "label": "news.google.com",
                "duration_seconds": 1800
                },
                {
                "label": "stackoverflow.com",
                "duration_seconds": 2700
                }
            ]
            },
            {
            "day": "Thursday", 
            "total_duration_seconds": 8642,
            "items": [
                {
                "label": "github.com",
                "duration_seconds": 3600
                },
                {
                "label": "medium.com",
                "duration_seconds": 1200
                }
            ]
            },
            {
            "day": "Friday",
            "total_duration_seconds": 13579,
            "items": [
                {
                "label": "dev.to",
                "duration_seconds": 1800
                },
                {
                "label": "news.ycombinator.com",
                "duration_seconds": 2700
                },
                {
                "label": "youtube.com",
                "duration_seconds": 3600
                }
            ]
            },
            {
            "day": "Saturday",
            "total_duration_seconds": 7200,
            "items": [
                {
                "label": "reddit.com",
                "duration_seconds": 3600
                },
                {
                "label": "stackoverflow.com",
                "duration_seconds": 1800
                }
            ]
            },
            {
            "day": "Sunday",
            "total_duration_seconds": 5400,
            "items": [
                {
                "label": "github.com",
                "duration_seconds": 1800
                },
                {
                "label": "medium.com",
                "duration_seconds": 1200
                }
            ]
            }
        ]
    }

@app.route('/metrics/topics', methods=['POST'])
def metrics_topics():
    return {
        "points": [
        {
            "label": "sports",
            "x": 1,
            "y": 1
        },
        {
            "label": "NBA",
            "x": 2,
            "y": 2
        },
        {
            "label": "basketball",
            "x": 3,
            "y": 3
        },
        ]
    }


@app.route('/')
def index():
    return 'HEALTHY'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
