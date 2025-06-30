from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

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
        "distance": 8045,  # meters
        "moving_time": 2400,  # seconds
        "elapsed_time": 2520,  # seconds
        "total_elevation_gain": 125,
        "type": "Run",
        "sport_type": "Run",
        "start_date": "2025-04-08T06:30:00Z",
        "start_date_local": "2025-04-08T07:30:00Z",
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
        # Time series data (30-second intervals)
        "metrics": {
            "time_points": [i * 30 for i in range(81)],
            "pace": [5.2, 5.1, 4.9, 4.8, 4.7, 4.6, 4.5, 4.4, 4.3, 4.2, *([4.1] * 71)],
            "elevation": [45, 48, 52, 55, 62, 68, 72, 75, 78, 82, *([85] * 71)],
            "heart_rate": [125, 145, 155, 162, 165, 168, 170, 172, 173, 175, *([176] * 71)],
            "cadence": [165, 172, 175, 178, 180, 182, 182, 183, 183, 184, *([185] * 71)],
            "power": [180, 195, 210, 225, 235, 240, 245, 248, 250, 252, *([255] * 71)]
        }
    },
    {
        "id": 2,
        "resource_state": 2,
        "external_id": "garmin_20250407_1",
        "upload_id": 1002,
        "athlete": {
            "id": 12345,
            "name": "Sarah Johnson",
            "profile_pic": "profile1.jpg"
        },
        "name": "Interval Training",
        "distance": 6500,
        "moving_time": 1800,
        "elapsed_time": 2100,
        "total_elevation_gain": 85,
        "type": "Run",
        "sport_type": "Run",
        "start_date": "2025-04-07T16:00:00Z",
        "start_date_local": "2025-04-07T17:00:00Z",
        "timezone": "Europe/London",
        "start_latlng": [51.5074, -0.1278],
        "end_latlng": [51.5074, -0.1278],
        "average_speed": 3.61,
        "max_speed": 4.8,
        "average_cadence": 182,
        "average_temp": 18,
        "has_heartrate": True,
        "average_heartrate": 168,
        "max_heartrate": 185,
        "elev_high": 75,
        "elev_low": 35,
        "pr_count": 3,
        "calories": 595,
        "perceived_exertion": 8,
        "metrics": {
            "time_points": [i * 30 for i in range(61)],
            "pace": [5.5, 5.2, 4.0, 3.8, 3.7, 5.2, 5.0, 3.9, 3.7, 3.6, *([3.5] * 51)],
            "elevation": [40, 45, 48, 52, 55, 58, 62, 65, 68, 70, *([72] * 51)],
            "heart_rate": [130, 150, 165, 175, 180, 182, 185, 182, 180, 178, *([176] * 51)],
            "cadence": [170, 175, 185, 188, 190, 188, 185, 182, 180, 178, *([176] * 51)],
            "power": [185, 200, 280, 295, 305, 290, 275, 285, 295, 300, *([290] * 51)]
        }
    },
    {
        "id": 3,
        "resource_state": 2,
        "external_id": "garmin_20250406_1",
        "upload_id": 1003,
        "athlete": {
            "id": 12345,
            "name": "Sarah Johnson",
            "profile_pic": "profile1.jpg"
        },
        "name": "Sunday Long Run",
        "distance": 21097,
        "moving_time": 7200,
        "elapsed_time": 7500,
        "total_elevation_gain": 245,
        "type": "Run",
        "sport_type": "Run",
        "start_date": "2025-04-06T08:00:00Z",
        "start_date_local": "2025-04-06T09:00:00Z",
        "timezone": "Europe/London",
        "start_latlng": [51.5074, -0.1278],
        "end_latlng": [51.5074, -0.1278],
        "average_speed": 2.93,
        "max_speed": 3.5,
        "average_cadence": 172,
        "average_temp": 15,
        "has_heartrate": True,
        "average_heartrate": 155,
        "max_heartrate": 168,
        "elev_high": 120,
        "elev_low": 15,
        "pr_count": 1,
        "calories": 1585,
        "perceived_exertion": 6,
        "metrics": {
            "time_points": [i * 30 for i in range(241)],
            "pace": [5.8, 5.6, 5.5, 5.4, 5.4, 5.3, 5.4, 5.5, 5.6, 5.7, *([5.6] * 231)],
            "elevation": [25, 35, 45, 55, 65, 75, 85, 95, 105, 115, *([120] * 231)],
            "heart_rate": [135, 145, 150, 155, 158, 160, 162, 160, 158, 155, *([153] * 231)],
            "cadence": [168, 170, 172, 172, 173, 173, 172, 171, 170, 169, *([168] * 231)],
            "power": [175, 185, 190, 195, 200, 205, 200, 195, 190, 185, *([180] * 231)]
        }
    }
]

class GarminAPI:
    def connect(self, email, password):
        # Mock successful connection
        return True

    def get_activity_details(self, activity_id):
        # Return mock activity data
        return MOCK_ACTIVITIES[0]

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.create_tables()

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id BIGINT PRIMARY KEY,
                resource_state INTEGER,
                external_id TEXT,
                upload_id BIGINT,
                athlete_id BIGINT,
                name TEXT,
                distance FLOAT,
                moving_time INTEGER,
                elapsed_time INTEGER,
                total_elevation_gain FLOAT,
                activity_type TEXT,
                sport_type TEXT,
                start_date DATETIME,
                start_date_local DATETIME,
                timezone TEXT,
                utc_offset INTEGER,
                start_lat FLOAT,
                start_lng FLOAT,
                end_lat FLOAT,
                end_lng FLOAT,
                achievement_count INTEGER,
                athlete_count INTEGER,
                map_id TEXT,
                map_polyline TEXT,
                map_summary_polyline TEXT,
                trainer BOOLEAN,
                manual BOOLEAN,
                private BOOLEAN,
                gear_id TEXT,
                average_speed FLOAT,
                max_speed FLOAT,
                average_cadence FLOAT,
                average_temp FLOAT,
                average_watts FLOAT,
                weighted_average_watts FLOAT,
                kilojoules FLOAT,
                device_watts BOOLEAN,
                has_heartrate BOOLEAN,
                max_watts INTEGER,
                elev_high FLOAT,
                elev_low FLOAT,
                pr_count INTEGER,
                workout_type INTEGER,
                calories FLOAT,
                device_name TEXT,
                embed_token TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def save_activity(self, activity_data):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO activities (
                id, resource_state, external_id, upload_id, athlete_id, name,
                distance, moving_time, elapsed_time, total_elevation_gain,
                activity_type, sport_type, start_date, start_date_local,
                timezone, utc_offset, start_lat, start_lng, end_lat, end_lng,
                achievement_count, athlete_count, map_id, map_polyline,
                map_summary_polyline, trainer, manual, private, gear_id,
                average_speed, max_speed, average_cadence, average_temp,
                average_watts, weighted_average_watts, kilojoules, device_watts,
                has_heartrate, max_watts, elev_high, elev_low, pr_count,
                workout_type, calories, device_name, embed_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?)
        ''', (
            activity_data['id'],
            activity_data['resource_state'],
            activity_data.get('external_id'),
            activity_data.get('upload_id'),
            activity_data['athlete']['id'],
            activity_data['name'],
            activity_data['distance'],
            activity_data['moving_time'],
            activity_data['elapsed_time'],
            activity_data['total_elevation_gain'],
            activity_data['type'],
            activity_data['sport_type'],
            activity_data['start_date'],
            activity_data['start_date_local'],
            activity_data['timezone'],
            activity_data['utc_offset'],
            activity_data['start_latlng'][0] if activity_data.get('start_latlng') else None,
            activity_data['start_latlng'][1] if activity_data.get('start_latlng') else None,
            activity_data['end_latlng'][0] if activity_data.get('end_latlng') else None,
            activity_data['end_latlng'][1] if activity_data.get('end_latlng') else None,
            activity_data['achievement_count'],
            activity_data['athlete_count'],
            activity_data['map']['id'],
            activity_data['map']['polyline'],
            activity_data['map']['summary_polyline'],
            activity_data['trainer'],
            activity_data['manual'],
            activity_data['private'],
            activity_data.get('gear_id'),
            activity_data['average_speed'],
            activity_data['max_speed'],
            activity_data.get('average_cadence'),
            activity_data.get('average_temp'),
            activity_data.get('average_watts'),
            activity_data.get('weighted_average_watts'),
            activity_data.get('kilojoules'),
            activity_data.get('device_watts'),
            activity_data['has_heartrate'],
            activity_data.get('max_watts'),
            activity_data['elev_high'],
            activity_data['elev_low'],
            activity_data['pr_count'],
            activity_data.get('workout_type'),
            activity_data.get('calories'),
            activity_data.get('device_name'),
            activity_data.get('embed_token')
        ))
        conn.commit()
        conn.close()

    def get_activities(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM activities ORDER BY start_date DESC')
        activities = cursor.fetchall()
        conn.close()
        return [dict(activity) for activity in activities]

    def get_user_profile(self):
        # Implement user profile retrieval
        return {}

@app.route('/')
def index():
    return render_template('index.html')

# Modified routes to use mock data
@app.route('/connect-garmin', methods=['POST'])
def connect_garmin():
    data = request.get_json()
    garmin_api = GarminAPI()
    return jsonify({"message": "Connected to Garmin successfully"}), 200

@app.route('/fetch-activity/<int:activity_id>', methods=['GET'])
def fetch_activity(activity_id):
    # Return mock activity data
    return jsonify(MOCK_ACTIVITIES[0]), 200

@app.route('/activities', methods=['GET'])
def get_activities():
    # Return list of mock activities
    return jsonify(MOCK_ACTIVITIES), 200

@app.route('/process-activity', methods=['POST'])
def process_activity():
    activity_data = request.get_json()
    db = Database('rts_main.db')
    db.save_activity(activity_data)
    return jsonify({"message": "Activity processed and saved successfully"}), 201

@app.route('/injury_tracking', methods=['GET', 'POST'])
def injury_tracking():
    if request.method == 'POST':
        pain_data = request.form['pain_data']
        return jsonify({"message": "Injury tracking data processed"}), 200
    return render_template('injury_tracking.html')

@app.route('/profile', methods=['GET'])
def profile():
    db = Database('rts_main.db')
    user_data = db.get_user_profile()
    return render_template('profile.html', user_data=user_data)

if __name__ == '__main__':
    app.run(debug=True)