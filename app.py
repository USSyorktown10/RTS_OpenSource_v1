from flask import Flask, render_template, jsonify, request
from garminconnect import Garmin
from datetime import datetime, timedelta
import json
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

class GarminAPI:
    def __init__(self):
        self.client = None
        
    def connect(self, email, password):
        try:
            self.client = Garmin(email, password)
            self.client.login()
            return True
        except Exception as e:
            print(f"Error connecting to Garmin: {e}")
            return False
    
    def get_activity_details(self, activity_id):
        try:
            return self.client.get_activity_details(activity_id)
        except Exception as e:
            print(f"Error fetching activity details: {e}")
            return None

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

@app.route('/connect-garmin', methods=['POST'])
def connect_garmin():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    garmin_api = GarminAPI()
    if garmin_api.connect(email, password):
        return jsonify({"message": "Connected to Garmin successfully"}), 200
    return jsonify({"error": "Failed to connect to Garmin"}), 401

@app.route('/fetch-activity/<int:activity_id>', methods=['GET'])
def fetch_activity(activity_id):
    garmin_api = GarminAPI()
    activity_data = garmin_api.get_activity_details(activity_id)
    
    if activity_data:
        db = Database('rts_main.db')
        db.save_activity(activity_data)
        return jsonify(activity_data), 200
    return jsonify({"error": "Failed to fetch activity"}), 404

@app.route('/activities', methods=['GET'])
def get_activities():
    db = Database('rts_main.db')
    activities = db.get_activities()
    return jsonify(activities), 200

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
