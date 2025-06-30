import requests
from flask import Flask, render_template, jsonify, request, url_for, redirect, request
import sqlite3
import json 
from datetime import datetime, timedelta, timezone
import time

app = Flask(__name__)

redirect_uri = 'http://localhost:8000/authorized'  # Must match your Strava app settings
CLIENT_ID = "CLIENT_ID" 
CLIENT_SECRET = "CLIENT_SECRET"
db_name = 'DB_NAME.db'

def init_db():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY,
            access_token TEXT,
            refresh_token TEXT,
            expires_at INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_tokens(access_token, refresh_token, expires_at):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('DELETE FROM tokens')  # Only store one set of tokens
    c.execute('INSERT INTO tokens (access_token, refresh_token, expires_at) VALUES (?, ?, ?)',
              (access_token, refresh_token, expires_at))
    conn.commit()
    conn.close()

def get_tokens():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT access_token, refresh_token, expires_at FROM tokens LIMIT 1')
    row = c.fetchone()
    conn.close()
    if row:
        return {'access_token': row[0], 'refresh_token': row[1], 'expires_at': row[2]}
    return None

def refresh_access_token(refresh_token):
    url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    tokens = response.json()
    save_tokens(tokens['access_token'], tokens['refresh_token'], tokens['expires_at'])
    return tokens

def get_valid_access_token():
    tokens = get_tokens()
    if not tokens:
        return None
    now = int(time.time())
    if now >= tokens['expires_at']:
        try:
            new_tokens = refresh_access_token(tokens['refresh_token'])
            return new_tokens['access_token']
        except Exception:
            return None
    else:
        return tokens['access_token']

def fetch_and_save_activities(access_token):
    activities = []
    page = 1
    per_page = 200  # Strava's max per page
    while True:
        url = f"https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"page": page, "per_page": per_page}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if not data:
            break
        activities.extend(data)
        page += 1
    # Save to file
    with open("strava_activities.json", "w") as f:
        json.dump(activities, f, indent=4)
    return activities

@app.template_filter('localtime')
def localtime_filter(s):
    # s is expected to be an ISO string
    dt = datetime.fromisoformat(s.replace('Z', '+00:00'))  # handle Zulu time
    return dt.strftime('%I:%M %p, %-m/%-d/%Y')

auth_url = (
    f"https://www.strava.com/oauth/authorize"
    f"?client_id={CLIENT_ID}"
    f"&response_type=code"
    f"&redirect_uri=http://localhost:8000/authorized"
    f"&approval_prompt=force"
    f"&scope=read,activity:read,activity:read_all"
)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/link_to_strava')
def link_to_strava():
    return redirect(f'https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost:8000/authorized&approval_prompt=force&scope=read,activity:read,activity:read_all')

@app.route('/authorized')
def authorized():
    AUTHORIZATION_CODE = request.args.get('code')

    # Strava OAuth token endpoint URL
    url = "https://www.strava.com/oauth/token"

    # Data to be sent in the POST request (using form-data)
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': AUTHORIZATION_CODE,
        'grant_type': 'authorization_code'
    }

    try:
        # Make the POST request
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        strava_tokens = response.json()
        save_tokens(strava_tokens['access_token'], strava_tokens['refresh_token'], strava_tokens['expires_at'])
        activities = fetch_and_save_activities(strava_tokens['access_token'])
        return json.dumps({
            "tokens": strava_tokens,
            "activities_count": len(activities)
        }, indent=4)
    
    except requests.exceptions.RequestException as e:
        return(f"Oops! Something went wrong: {e}") # Handle request errors

@app.route('/get_valid_token')
def get_valid_token():
    tokens = get_tokens()
    if not tokens:
        return jsonify({'error': 'No tokens found. Please authorize first.'}), 400
    now = int(time.time())
    if now >= tokens['expires_at']:
        # Token expired, refresh it
        try:
            new_tokens = refresh_access_token(tokens['refresh_token'])
            return jsonify({'access_token': new_tokens['access_token'], 'expires_at': new_tokens['expires_at']})
        except Exception as e:
            return jsonify({'error': f'Failed to refresh token: {e}'}), 400
    else:
        # Token still valid
        return jsonify({'access_token': tokens['access_token'], 'expires_at': tokens['expires_at']})

def get_weekly_mileage(activities):
    now = datetime.now(timezone.utc)
    start_of_week = now - timedelta(days=now.weekday())
    mileage = 0
    for act in activities:
        act_date = datetime.fromisoformat(act['start_date_local'].replace('Z', '+00:00'))
        if act_date.tzinfo is None:
            act_date = act_date.replace(tzinfo=timezone.utc)
        else:
            act_date = act_date.astimezone(timezone.utc)
        if act['type'] == 'Run' and act_date >= start_of_week:
            mileage += act['distance'] / 1609.34
    return round(mileage, 2)

def get_weekly_mileage_history(activities, weeks=7):
    # Build a list of week start dates (Monday) for the last `weeks` weeks
    now = datetime.now(timezone.utc)
    week_starts = [(now - timedelta(days=now.weekday() + 7 * i)).replace(hour=0, minute=0, second=0, microsecond=0)
                   for i in reversed(range(weeks))]
    week_totals = [0 for _ in range(weeks)]

    for act in activities:
        act_date = datetime.fromisoformat(act['start_date_local'].replace('Z', '+00:00'))
        if act_date.tzinfo is None:
            act_date = act_date.replace(tzinfo=timezone.utc)
        else:
            act_date = act_date.astimezone(timezone.utc)
        if act['type'] == 'Run':
            for i in range(weeks):
                # If activity falls within this week
                week_start = week_starts[i]
                week_end = week_starts[i+1] if i+1 < len(week_starts) else now + timedelta(days=1)
                if week_start <= act_date < week_end:
                    week_totals[i] += act['distance'] / 1609.34
                    break

    # Format week labels as "M/D"
    week_labels = [ws.strftime('%-m/%-d') for ws in week_starts]
    week_totals = [round(m, 2) for m in week_totals]
    return week_labels, week_totals

@app.route('/activities')
def activities():
    access_token = get_valid_access_token()
    if not access_token:
        return jsonify({'error': 'No valid token. Please authorize.'}), 400
    try:
        url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"per_page": 30}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        activities = response.json()
        weekly_mileage = get_weekly_mileage(activities)
        week_labels, week_totals = get_weekly_mileage_history(activities)
        return render_template('activities.html', activities=activities, weekly_mileage=weekly_mileage, week_labels=week_labels, week_totals=week_totals)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    init_db()  # Initialize the database
    print(get_tokens())
    app.run(host='localhost', port=8000, debug=True)