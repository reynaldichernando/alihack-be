from flask import Flask

app = Flask(__name__)

@app.route('/track')
def test():
    return {
        "categories": [
            "News",
            "Sports",
            "Entertainment"
        ],
        "topics": [
            "NBA playoffs",
            "NFL draft",
            "MLB trade rumors"
        ],
        "summary": "The latest news and updates on the NBA playoffs, including game recaps, player performances, and predictions for upcoming matchups. Coverage of the NFL draft, with analysis of top prospects and potential landing spots for each team. Rumors and speculation surrounding potential trades in MLB as the deadline approaches.",
        "minute_saved": 42
    }

@app.route('/metrics')
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

@app.route('/metrics/topics')
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
