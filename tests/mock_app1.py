from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Mock activity data
MOCK_ACTIVITIES = [
    {
        "id": 1,
        "resource_state": 2,
        "external_id": "garmin_20250408_1",
        "upload_id": 1001,
        "athlete": {
            "id": 12345,
            "name": "Sarah Johnson",
            "profile_pic": "profile1.jpg"
        },
        "name": "Morning Tempo Run",
        "distance": 8045,  # in meters
        "moving_time": 2400,  # in seconds
        "elapsed_time": 2520,  # in seconds
        "total_elevation_gain": 125,
        "type": "Run",
        "sport_type": "Run",
        "start_date": "2025-04-08T06:30:00Z",
        "start_date_local": "2025-04-08T07:30:00",
        "timezone": "Europe/London",
        "start_latlng": [51.5074, -0.1278],
        "end_latlng": [51.5074, -0.1278],
        "average_speed": 3.35,  # m/s
        "max_speed": 4.2,
        "average_cadence": 178,
        "average_temp": 16,
        "has_heartrate": True,
        "average_heartrate": 162,
        "max_heartrate": 178,
        "elev_high": 98,
        "elev_low": 23,
        "pr_count": 2,
        "calories": 685,
        "perceived_exertion": 7,
        "metrics": {
            "time_points": [i * 30 for i in range(81)],
            "pace": [5.2, 5.1, 4.9, 4.8, 4.7, 4.6, 4.5, 4.4, 4.3, 4.2, *([4.1] * 71)],
            "elevation": [45, 48, 52, 55, 62, 68, 72, 75, 78, 82, *([85] * 71)],
            "heart_rate": [125, 145, 155, 162, 165, 168, 170, 172, 173, 175, *([176] * 71)],
            "cadence": [165, 172, 175, 178, 180, 182, 182, 183, 183, 184, *([185] * 71)],
            "power": [180, 195, 210, 225, 235, 240, 245, 248, 250, 252, *([255] * 71)]
        }
    },
    # Additional activities...
]

def format_datetime(value):
    date = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    return date.strftime("%I:%M %p, %B %d, %Y")

def format_pace(pace_min_per_mile):
    minutes = int(pace_min_per_mile)
    seconds = int((pace_min_per_mile - minutes) * 60)
    return f"{minutes}:{seconds:02d}/mile"

app.jinja_env.filters['format_datetime'] = format_datetime
app.jinja_env.filters['format_pace'] = format_pace

@app.route('/')
def home():
    return render_template('home.html', activities=MOCK_ACTIVITIES)

@app.route('/activity/<int:activity_id>')
def activity(activity_id):
    activity = next((act for act in MOCK_ACTIVITIES if act["id"] == activity_id), None)
    if not activity:
        return "Activity not found", 404
    return render_template('activity.html', activity=activity)

if __name__ == '__main__':
    app.run(debug=True)
