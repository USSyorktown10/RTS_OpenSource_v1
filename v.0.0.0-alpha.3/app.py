import yaml
import requests
from flask import Flask, render_template, jsonify, request, url_for, redirect, request, flash, session
import sqlite3
import json 
from datetime import datetime, timedelta, timezone
import time
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from utils import cm_to_ft_in, kg_to_lbs, lbs_to_kg, ft_in_to_cm
import os
import math
from collections import defaultdict
import logging
import joblib
import numpy as np


UPLOAD_FOLDER = 'static/pfps'  # Create a 'pfps' folder inside 'static'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
banister_params = joblib.load('banister_params.pkl')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

app.secret_key = config.get('secret_key', 'dev-secret-key')  # Use a secure value in production!

redirect_uri = config['redirect']
CLIENT_ID = config['client_id']
CLIENT_SECRET = config['client_secret']
db_name = config['db']

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username, profile_pic):
        self.id = id
        self.username = username
        self.profile_pic = profile_pic or 'static/default_pfp.png'

class RowWithAttr(sqlite3.Row):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT id, username, profile_pic FROM users WHERE id=?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(row[0], row[1], row[2])
    return None

CTLmin = 0
CTLmax = 150
ATLmin = 0
ATLmax = 150
Tfit = 42
Tfat = 7
ISA_SEA_LEVEL_TEMP_C = 15.0
ISA_SEA_LEVEL_PRESSURE_PA = 101325.0
LAPSE_RATE = 0.0065
TROPOPAUSE_ALT = 11000.0
TROPOPAUSE_TEMP_C = -56.5
GAS_CONST = 287.05
GRAVITY = 9.80665
ISA_SEA_LEVEL_TEMP_K = 288.15
MOLAR_MASS_AIR = 0.0289644  # kg/mol (Molar mass of dry air)
lapse_rate = 0.0065  # K/m (approximate lapse rate in the troposphere)

# Calculate EXPONENT based on the barometric formula for the troposphere
EXPONENT = (GRAVITY * MOLAR_MASS_AIR) / (GAS_CONST * lapse_rate)

def init_db():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    # -- users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            profile_pic TEXT DEFAULT '/default_pfp.png'
        )
    ''')
    # -- tokens table (add user_id)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            expires_at INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # -- activities table (add user_id)
    c.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_id INTEGER,
            data TEXT,
            rpe REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # -- user table (user specifics)
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            height INTEGER,
            weight INTEGER,
            sex TEXT,
            age INTEGER,
            firstname TEXT,
            lastname TEXT,
            fastest_pace REAL,
            height_is_user_set BOOLEAN DEFAULT FALSE,
            weight_is_user_set BOOLEAN DEFAULT FALSE,
            sex_is_user_set BOOLEAN DEFAULT FALSE,
            age_is_user_set BOOLEAN DEFAULT FALSE,
            firstname_is_user_set BOOLEAN DEFAULT FALSE,
            lastname_is_user_set BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # -- user_hr_zones table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_hr_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            zone_number INTEGER,
            min_hr INTEGER,
            max_hr INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # -- user_stats table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            max_hr INTEGER,
            stride_length REAL,
            erun REAL,
            hosc REAL,
            afrontal REAL,
            cd REAL,
            ftp REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')    
    # -- user_fitness table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_fitness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_id INTEGER,
            day TEXT,
            watts FLOAT,
            relative_effort FLOAT,
            CTL FLOAT,
            ATL FLOAT,
            norm_CTL FLOAT,
            norm_ATL FLOAT,
            TSB FLOAT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()
    
def init_user_stats(max_hr, stride_length, hosc, afrontal, ftp):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT id FROM users')
    user_ids = [row[0] for row in c.fetchall()]
    for user_id in user_ids:
        c.execute('''
            INSERT OR IGNORE INTO user_stats (user_id, max_hr, stride_length, erun, hosc, afrontal, cd, ftp)
            VALUES (?, ?, ?, 1.036, ?, ?, 1.2, ?)
        ''', (user_id, max_hr, stride_length, hosc, afrontal, ftp))
    conn.commit()
    conn.close()

def calculate_tss(activity, user_stats, user_data, watts):
    duration_hr = activity['elapsed_time'] / 3600
    # 1. Heart Rate
    if activity.get('average_heartrate') and user_stats['max_hr'] and user_stats['resting_hr']:
        hr_avg = activity['average_heartrate']
        hr_rest = user_stats['resting_hr']
        hr_max = user_stats['max_hr']
        if hr_max <= hr_rest:
            logging.error(f"Invalid HR data: max_hr={hr_max}, resting_hr={hr_rest}")
            return duration_hr * 50  # fallback
        intensity = (hr_avg - hr_rest) / (hr_max - hr_rest)
    # 2. RPE
    elif activity.get('rpe'):
        rpe = float(activity.get('rpe', 5))
        intensity = rpe / 10  # Assuming 1–10 RPE scale
    # 3. Fastest pace
    elif user_data['fastest_pace'] and activity.get('distance') and activity.get('elapsed_time'):
        pace = activity['distance'] / activity['elapsed_time']  # m/s
        intensity = pace / user_data['fastest_pace']
    # 4. FTP
    elif user_stats['ftp'] and watts:
        intensity = watts / user_stats['ftp']
    else:
        intensity = 0.5  # fallback

    intensity = max(0, min(intensity, 1))
    tss = duration_hr * intensity * 100

    # Apply terrain gradient
    if activity.get('total_elevation_gain', 0) > 0 and activity.get('distance', 0) > 0:
        gradient = activity['total_elevation_gain'] / activity['distance']
        tss *= (1 + gradient * 0.1)  # Adjust multiplier as needed
    return tss

def calculate_training_load(activities, current_day, user_stats, user_data, watts, tfit=42, tfat=7):
    ctl = 0
    atl = 0
    daily_data = {}
    now = datetime.now(timezone.utc).date()

    for activity in activities:
        try:
            activity_timestamp = datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00'))
        except ValueError:
            logging.error(f"Invalid timestamp for activity {activity.get('id')}")
            continue
        day = activity_timestamp.date()
        if day > current_day:
            break  # Stop processing future activities
        
        delta_t = (now - day).days
        tss = calculate_tss(activity, user_stats, user_data, watts)
        if tss is None:
            continue

        # Store activity contributions
        key = (day.isoformat(), activity['id'])
        daily_data[key] = {
            'tss': tss,
            'ctl_contribution': tss * math.exp(-delta_t / tfit),
            'atl_contribution': tss * math.exp(-delta_t / tfat)
        }

        # Sum contributions for current day
        if day == current_day:
            ctl += daily_data[key]['ctl_contribution']
            atl += daily_data[key]['atl_contribution']

    return ctl, atl, daily_data

def banister_recursive(params, tss_list):
    k1, k2, PO, CTLC, ATLC = params
    fitness = np.zeros(len(tss_list))
    fatigue = np.zeros(len(tss_list))
    for i in range(1, len(tss_list)):
        fitness[i] = fitness[i-1] + (tss_list[i] - fitness[i-1]) / CTLC
        fatigue[i] = fatigue[i-1] + (tss_list[i] - fatigue[i-1]) / ATLC
    prediction = k1 * fitness + k2 * fatigue + PO
    return fitness, fatigue, prediction

def get_user_fitness(activities): 
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM user_stats WHERE user_id=?', (current_user.id,))
    user_stats = c.fetchone()
    c.execute('SELECT * FROM user_data WHERE user_id=?', (current_user.id,))
    user_data = c.fetchone()
    now = datetime.now(timezone.utc)
    
    # Group activities by day
    from collections import defaultdict
    acts_by_day = defaultdict(list)
    for activity in activities:
        day = activity['start_date_local'][:10]
        acts_by_day[day].append(activity)

    sorted_days = sorted(acts_by_day.keys())
    CTL = 0
    ATL = 0
    ctl_by_day = {}
    atl_by_day = {}
    daily_data = {}
    re_list = []

    for day in sorted_days:
        re_today = 0
        for act in acts_by_day[day]:
            if not act.get('distance') or not act.get('elapsed_time') or not act.get('average_cadence'):
                act['relative_effort'] = 0
                continue

            activity_timestamp = datetime.fromisoformat(act['start_date_local'].replace('Z', '+00:00'))
            if activity_timestamp.tzinfo is None:
                activity_timestamp = activity_timestamp.replace(tzinfo=timezone.utc)
            else:
                activity_timestamp = activity_timestamp.astimezone(timezone.utc)
            day = activity_timestamp.date().isoformat()
            delta_t = (now - activity_timestamp).total_seconds() / (60 * 60 * 24)
            exp_factor_ctl = math.exp(-delta_t / Tfit)
            exp_factor_atl = math.exp(-delta_t / Tfat)
            velocity_mps = act['distance'] / act['elapsed_time']

            '''The following is using Newtons Law of Universal Gravitation'''
            # Universal Gravitational Constant (m^3 kg^-1 s^-2)
            G = 6.67430 * (10**-11) 
            # Mass of Earth (kg)
            M = 5.9722 * (10**24)
            # Mean radius of Earth (m)
            R = 6.371 * (10**6)
            r = R + act['elev_high']  # Distance from Earth's center to the object
            gravity = (G * M) / (r**2)

            '''The following is using International Standard Atmosphere (ISA) model as a basis'''        
            try:
                # Temperature calculation
                if act.get('average_temp'):
                    if act['average_temp'] is None:
                        T = ISA_SEA_LEVEL_TEMP_C - LAPSE_RATE * act['elev_high'] if act['elev_high'] <= TROPOPAUSE_ALT else TROPOPAUSE_TEMP_C
                    else:
                        T = act['average_temp']
                    T_kelvin = T + 273.15

                    # Precompute constants
                    sea_level_temp_K = ISA_SEA_LEVEL_TEMP_C + 273.15
                    exponent = GRAVITY / (LAPSE_RATE * GAS_CONST)

                    # Pressure calculation
                    if act['elev_high'] <= TROPOPAUSE_ALT:
                        P = ISA_SEA_LEVEL_PRESSURE_PA * (T_kelvin / sea_level_temp_K) ** exponent
                    else:
                        tropopause_temp_K = TROPOPAUSE_TEMP_C + 273.15
                        P_tropopause = ISA_SEA_LEVEL_PRESSURE_PA * (tropopause_temp_K / sea_level_temp_K) ** exponent
                        P = P_tropopause * math.exp(-GRAVITY * (act['elev_high'] - TROPOPAUSE_ALT) / (GAS_CONST * T_kelvin))

                    # Air density calculation
                    air_density = P / (GAS_CONST * T_kelvin)
                else:
                    T = ISA_SEA_LEVEL_TEMP_C - LAPSE_RATE * act['elev_high'] if act['elev_high'] <= TROPOPAUSE_ALT else TROPOPAUSE_TEMP_C
                    T_kelvin = T + 273.15

                    # Precompute constants
                    sea_level_temp_K = ISA_SEA_LEVEL_TEMP_C + 273.15
                    exponent = GRAVITY / (LAPSE_RATE * GAS_CONST)

                    # Pressure calculation
                    if act['elev_high'] <= TROPOPAUSE_ALT:
                        # Assuming a standard lapse rate (temperature decrease with altitude)
                        lapse_rate = 0.0065  # K/m (approximate lapse rate in the troposphere)
                        estimated_T_kelvin = ISA_SEA_LEVEL_TEMP_K - (lapse_rate * act['elev_high'])
                        P = ISA_SEA_LEVEL_PRESSURE_PA * (estimated_T_kelvin / ISA_SEA_LEVEL_TEMP_K) ** EXPONENT
                    else:
                        # For altitudes above the tropopause, use tropopause values and an exponential decay
                        tropopause_temp_K = TROPOPAUSE_TEMP_C + 273.15
                        P_tropopause = ISA_SEA_LEVEL_PRESSURE_PA * (tropopause_temp_K / ISA_SEA_LEVEL_TEMP_K) ** EXPONENT
                        P = P_tropopause * math.exp(-GRAVITY * (act['elev_high'] - TROPOPAUSE_ALT) / (GAS_CONST * tropopause_temp_K)) # Use tropopause temp for this part of the calculation, assuming a constant temperature in the stratosphere

                    # Air density calculation
                    air_density = P / (GAS_CONST * T_kelvin)
            except Exception as e:
                print("Air density problem")
                print(e)
            
            cadence_sec = act['average_cadence'] / 60.0
            watts = (1.036 * user_data['weight'] * velocity_mps) + (user_data['weight'] * gravity * user_stats['hosc'] * cadence_sec) + (0.5 * air_density * user_stats['afrontal'] * 1.4 * velocity_mps**3) + (user_data['weight'] * gravity * velocity_mps * act['total_elevation_gain'] / act['distance'])

            act['relative_effort'] = calculate_tss(act, user_stats, user_data, watts)
            re_today += act['relative_effort'] 
            re_list.append(act['relative_effort'])
        
        CTL_arr, ATL_arr, _ = banister_recursive(banister_params, re_list)
        CTL = CTL + (re_today - CTL) / Tfit
        ATL = ATL + (re_today - ATL) / Tfat
        ctl_by_day[day] = CTL
        atl_by_day[day] = ATL
        for act in acts_by_day[day]:
            key = (day, act['id'])
            daily_data[key] = {
                'watts': watts,
                'relative_effort': act['relative_effort'],
                'ctl': CTL,
                'atl': ATL,
                'tsb': CTL - ATL
            }

    # Write to DB
    for i, ((day, activity_id), data) in enumerate(list(daily_data.items())[:len(CTL_arr)]):
        ctl = CTL_arr[i]
        atl = ATL_arr[i]
        tsb = ctl - atl
        norm_ctl = (ctl - CTLmin) / (CTLmax - CTLmin) * 100 if ctl > 0 else 0
        norm_atl = (atl - ATLmin) / (ATLmax - ATLmin) * 100 if atl > 0 else 0

        c.execute('''
            SELECT id FROM user_fitness WHERE user_id = ? AND activity_id = ? AND day = ?
        ''', (current_user.id, activity_id, day))
        row = c.fetchone()
        if row is not None and row[0] is not None:
            c.execute('''
                UPDATE user_fitness
                SET watts = ?, relative_effort = ?, CTL = ?, ATL = ?, norm_CTL = ?, norm_ATL = ?, TSB = ?
                WHERE id = ?
            ''', (data['watts'], data['relative_effort'], ctl, atl, norm_ctl, norm_atl, tsb, row[0]))
        else:
            c.execute('''
                INSERT INTO user_fitness (user_id, activity_id, day, watts, relative_effort, CTL, ATL, norm_CTL, norm_ATL, TSB)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (current_user.id, activity_id, day, data['watts'], data['relative_effort'], ctl, atl, norm_ctl, norm_atl, tsb))

    conn.commit()

    # Fetch and return all fitness data for the user
    c.execute('''
        SELECT * FROM user_fitness WHERE user_id = ? ORDER BY day, activity_id
    ''', (current_user.id,))
    results = c.fetchall()
    columns = ['id', 'user_id', 'activity_id', 'day', 'watts', 'relative_effort', 'CTL', 'ATL', 'norm_CTL', 'norm_ATL', 'TSB']
    conn.close()
    return [dict(zip(columns, row)) for row in results]

def get_activity_fitness_changes(activity_id, db_name='strava_tokens.db'):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Fetch the activity's fitness data
    c.execute('SELECT day, watts, relative_effort, CTL, ATL, TSB FROM user_fitness WHERE user_id = ? AND activity_id = ?', (current_user.id, activity_id))
    activity_data = c.fetchone()
    if not activity_data:
        conn.close()
        return None

    activity_day, watts, relative_effort, ctl, atl, tsb = activity_data
    # Find the previous day's fitness data
    activity_date = datetime.strptime(activity_day, '%Y-%m-%d').date()
    previous_date = activity_date.fromordinal(activity_date.toordinal() - 1)
    previous_day_str = previous_date.isoformat()

    c.execute('SELECT AVG(CTL), AVG(ATL), AVG(TSB) FROM user_fitness WHERE user_id = ? AND day = ?', (current_user.id, previous_day_str))
    previous_data = c.fetchone()
    prev_ctl, prev_atl, prev_tsb = (previous_data if previous_data and all(v is not None for v in previous_data) else (0, 0, 0))

    conn.close()
    return {
        'relative_effort': relative_effort,
        'ctl_change': ctl - prev_ctl,
        'atl_change': atl - prev_atl,
        'watts': watts,
        'tsb_change': tsb - prev_tsb
    }

def update_user_stats(user_id, max_hr, stride_length, hosc, afrontal, ftp):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
        UPDATE user_stats
        SET max_hr = ?, stride_length = ?, hosc = ?, afrontal = ?, ftp = ?
        WHERE user_id = ?
    ''', (max_hr, stride_length, hosc, afrontal, ftp, user_id))
    conn.commit()
    conn.close()
    

def save_tokens(user_id, access_token, refresh_token, expires_at):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('DELETE FROM tokens WHERE user_id=?', (user_id,))
    c.execute('INSERT INTO tokens (user_id, access_token, refresh_token, expires_at) VALUES (?, ?, ?, ?)',
              (user_id, access_token, refresh_token, expires_at))
    conn.commit()
    conn.close()

def get_tokens():
    if not current_user.is_authenticated:
        return None
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT access_token, refresh_token, expires_at FROM tokens WHERE user_id=? LIMIT 1', (current_user.id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'access_token': row[0], 'refresh_token': row[1], 'expires_at': row[2]}
    return None

def refresh_access_token(refresh_token, user_id):
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
    save_tokens(user_id, tokens['access_token'], tokens['refresh_token'], tokens['expires_at'])
    
    return tokens

def get_valid_access_token():
    tokens = get_tokens()
    if not tokens:
        return None
    now = int(time.time())
    if now >= tokens['expires_at']:
        try:
            new_tokens = refresh_access_token(tokens['refresh_token'], current_user.id)
            return new_tokens['access_token']
        except Exception:
            return None
    else:
        return tokens['access_token']


def fetch_and_save_activities(access_token, limit=100):
    activities = []
    page = 1
    per_page = 100 if limit else 200
    user_id = current_user.id
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    fetched = 0
    while True:
        url = f"https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"page": page, "per_page": per_page}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        new_or_updated = []
        if not data:
            break
        for act in data:
            # Check if activity is new or updated
            c.execute('SELECT data FROM activities WHERE user_id=? AND activity_id=?', (user_id, act['id']))
            row = c.fetchone()
            if row is None or json.loads(row[0]) != act:
                new_or_updated.append(act)

            # Insert or update activity
            c.execute('''
                INSERT OR IGNORE INTO activities (user_id, activity_id, data)
                VALUES (?, ?, ?)
            ''', (user_id, act['id'], json.dumps(act)))
            c.execute('''
                UPDATE activities SET data=? WHERE user_id=? AND activity_id=?
            ''', (json.dumps(act), user_id, act['id']))

            # Fetch RPE if set
            c.execute('SELECT rpe FROM activities WHERE user_id=? AND activity_id=?', (user_id, act['id']))
            rpe_row = c.fetchone()
            if rpe_row and rpe_row[0] is not None:
                act['rpe'] = rpe_row[0]

            activities.append(act)
            fetched += 1

            if limit and fetched >= limit:
                conn.commit()
                conn.close()
                return activities, new_or_updated
        if limit and fetched >= limit:
            break
        page += 1
    conn.commit()
    conn.close()
    
    return activities, new_or_updated

@app.template_filter('localtime')
def localtime_filter(s):
    # s is expected to be an ISO string
    dt = datetime.fromisoformat(s.replace('Z', '+00:00'))  # handle Zulu time
    return dt.strftime('%I:%M %p, %-m/%-d/%Y')

auth_url = (
    f"https://www.strava.com/oauth/authorize"
    f"?client_id={CLIENT_ID}"
    f"&response_type=code"
    f"&redirect_uri={redirect_uri}"
    f"&approval_prompt=force"
    f"&scope=read,activity:read,activity:read_all"
)


@app.route('/')
def index():
    strava_connected = get_tokens() is not None
    
    return render_template('index2.html', strava_connected=strava_connected)

@app.route('/link_to_strava')
@login_required
def link_to_strava():
    return redirect(f'https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost:8000/authorized&approval_prompt=force&scope=read,activity:read,activity:read_all,profile:read_all')

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
        save_tokens(current_user.id, strava_tokens['access_token'], strava_tokens['refresh_token'], strava_tokens['expires_at'])
        return redirect(url_for('post_authorization'))

    except requests.exceptions.RequestException as e:
        return render_template('authorized.html', strava_connected=False) # Handle request errors

@app.route('/post_authorization', methods=['GET', 'POST'])
@login_required
def post_authorization():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    
    # Check if the user has already inputted any stat manually
    c.execute('''
        SELECT * FROM user_data
        WHERE user_id = ?
        AND (
            height_is_user_set = 1 OR
            weight_is_user_set = 1 OR
            sex_is_user_set = 1 OR
            age_is_user_set = 1 OR
            firstname_is_user_set = 1 OR
            lastname_is_user_set = 1
        )
    ''', (current_user.id,))
    
    user_has_set_data = c.fetchone()
    conn.close()
    
    if user_has_set_data:
        return redirect(url_for('index'))  # or wherever you want them to go
    if get_valid_access_token() is None:
        return jsonify({'error': 'No valid token. Please authorize.'}), 400
    if request.method == 'POST':
        height_ft = float(request.form['height_feet'])
        height_in = float(request.form['height_inches'])
        age = float(request.form['age'])
        max_hr = request.form['max_hr']
        stride_length = float(request.form['stride_length'])
        stride_length_metric = stride_length * 2.54
        hosc = request.form['hosc']
        afrontal = request.form['afrontal']
        fastest_pace_min = request.form['fastest_pace_min']
        fastest_pace_sec = request.form['fastest_pace_sec']
        fastest_pace = (float(fastest_pace_min) * 60) + float(fastest_pace_sec)
        fastest_pace = 1609.34 / fastest_pace
        ftp = request.form.get('ftp', None)
        init_user_stats(max_hr, stride_length_metric, hosc, afrontal, ftp)
        height = (height_ft * 30.48) + (height_in * 2.54)
        height = int(height)
        
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        c.execute('''
            UPDATE user_data
            SET height = ?, height_is_user_set = 1,
                age = ?, age_is_user_set = 1,
                fastest_pace = ?
            WHERE user_id = ?
        ''', (
            height,
            age,
            fastest_pace,
            current_user.id
        ))

        conn.commit()
        conn.close()
        return render_template('index.html')
    return render_template('authorized.html', strava_connected=True)

@app.route('/get_valid_token')
def get_valid_token():
    tokens = get_tokens()
    if not tokens:
        return jsonify({'error': 'No tokens found. Please authorize first.'}), 400
    now = int(time.time())
    if now >= tokens['expires_at']:
        # Token expired, refresh it
        try:
            new_tokens = refresh_access_token(tokens['refresh_token'], current_user.id)
            return jsonify({'access_token': new_tokens['access_token'], 'expires_at': new_tokens['expires_at']})
        except Exception as e:
            return jsonify({'error': f'Failed to refresh token: {e}'}), 400
    else:
        # Token still valid
        return jsonify({'access_token': tokens['access_token'], 'expires_at': tokens['expires_at']})

def get_weekly_mileage(activities):
    now = datetime.now(timezone.utc)
    # Start of the week (Monday, 00:00 UTC)
    start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
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
    now = datetime.now(timezone.utc)
    # List of week start dates (Monday, 00:00 UTC)
    week_starts = [
        (now - timedelta(days=now.weekday() + 7 * i)).replace(hour=0, minute=0, second=0, microsecond=0)
        for i in reversed(range(weeks))
    ]
    week_totals = [0 for _ in range(weeks)]

    for act in activities:
        act_date = datetime.fromisoformat(act['start_date_local'].replace('Z', '+00:00'))
        if act_date.tzinfo is None:
            act_date = act_date.replace(tzinfo=timezone.utc)
        else:
            act_date = act_date.astimezone(timezone.utc)
        if act['type'] == 'Run':
            for i in range(weeks):
                week_start = week_starts[i]
                week_end = week_starts[i+1] if i+1 < len(week_starts) else now + timedelta(days=1)
                if week_start <= act_date < week_end:
                    week_totals[i] += act['distance'] / 1609.34
                    break

    week_labels = [ws.strftime('%-m/%-d') for ws in week_starts]
    week_totals = [round(m, 2) for m in week_totals]
    return week_labels, week_totals

@app.route('/charts')
@login_required
def charts():
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT day, MAX(CTL) as CTL, MAX(ATL) as ATL, MAX(TSB) as TSB
        FROM user_fitness
        WHERE user_id = ?
        GROUP BY day
        ORDER BY day ASC
    ''', (current_user.id,))
    data = [dict(row) for row in c.fetchall()]
    conn.close()
    chart_data = [
        {
            'day': row['day'],
            'CTL': row['CTL'],
            'ATL': row['ATL'],
            'TSB': row['TSB'],
        }
        for row in data
    ]
    return render_template('charts.html', data=chart_data)

@app.route('/activities')
@login_required
def activities():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    fields = ['height', 'weight', 'age', 'fastest_pace']
    missing_fields = []

    for field in fields:
        c.execute(f'SELECT {field} FROM user_data WHERE user_id=?', (current_user.id,))
        result = c.fetchone()
        value = result[0] if result is not None else None
        if value is None:
            missing_fields.append(field)
            
    c.execute('SELECT ftp FROM user_stats WHERE user_id=?', (current_user.id,))
    result = c.fetchone()
    ftp = result[0] if result is not None else None
    if ftp is None:
        missing_fields.append('FTP')

    if missing_fields:
        missing = ', '.join(missing_fields).replace('_', ' ')
    else:
        missing = "None"

    access_token = get_valid_access_token()
    console_log = access_token 
    activities = []
    try:
        if access_token:
            activities, new_or_updated = fetch_and_save_activities(access_token, limit=100)
            if new_or_updated:
                get_user_fitness(activities)
        else:
            print("No valid access token")
            raise Exception("No valid access token found.")
    except Exception as e:
        print("/activities loading exception")
        print(e)
        conn.close()
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        activities = c.execute('SELECT data FROM activities WHERE user_id=? ORDER BY activity_id DESC LIMIT 100', (current_user.id,))
        conn.close()
    weekly_mileage = get_weekly_mileage(activities)
    week_labels, week_totals = get_weekly_mileage_history(activities)

    return render_template('activities.html', activities=activities, weekly_mileage=weekly_mileage, week_labels=week_labels, week_totals=week_totals, console_log=console_log, missing=missing)

# The following may become something later, just not sure yet.
'''
@app.route('/calculations/<int:calc_type>')
@login_required
def calculations(calc_type):
    if get_valid_access_token() is None:
        return jsonify({'error': 'No valid token. Please authorize.'}), 400
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Enable attribute access
    c = conn.cursor()
    c.execute('SELECT * FROM user_data WHERE user_id=?', (current_user.id,))
    user_data = c.fetchone()
    c.execute('SELECT * FROM user_stats WHERE user_id=?', (current_user.id,))
    user_stats = c.fetchone()
    conn.close()
    if not user_data or not user_stats:
        return jsonify({'error': 'User data or stats not found.'}), 404
    
    if calc_type == 1: # Wattage
        if user_data and user_stats:
            distance = request.form.get('distance', type=float)
            slope = request.form.get('slope', type=float, default=0)  # Slope in percentage
            total_time_sec = request.form.get('total_time_sec', type=float)
            cadence = request.form.get('cadence', type=float)
            air_density = request.form.get('air_density', type=float, default=1.225)  # kg/m^3 at sea level
            velocity_mps = distance * 1000 / total_time_sec
            weight_kg = user_data.weight
            Erun = user_stats.erun
            g = 9.81  # Acceleration due to gravity in m/s^2
            hosc = user_stats.hosc
            afrontal = user_stats.afrontal
            cd = user_stats.cd
            
            # Perform wattage calculation
            power = (
                (Erun * weight_kg * velocity_mps) + (weight_kg * g * hosc * cadence) + (0.5 * air_density * afrontal * cd  * velocity_mps**3) + (weight_kg * g * velocity_mps * math.sine(slope / 100))
            )
            return jsonify({'wattage': power}), 200
    elif calc_type == 2:
        # Perform calculation type 2
        pass
    else:
        return jsonify({'error': 'Invalid calculation type.'}), 400
'''

def get_user_stats():
    access_token = get_valid_access_token()
    if not access_token:
        return jsonify({'error': 'No valid token. Please authorize.'}), 400
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = RowWithAttr
        c = conn.cursor()
        c.execute('SELECT * FROM user_data WHERE user_id=?', (current_user.id,))
        existing_data = c.fetchone()
        conn.close()
        return existing_data
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def get_user_data():
    access_token = get_valid_access_token()
    if not access_token:
        return jsonify({'error': 'No valid token. Please authorize.'}), 400

    try:
        url = "https://www.strava.com/api/v3/athlete"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        athlete = response.json()

        conn = sqlite3.connect(db_name)
        conn.row_factory = RowWithAttr  # Enable attribute access
        c = conn.cursor()

        # Fetch existing user data
        c.execute('SELECT * FROM user_data WHERE user_id=?', (current_user.id,))
        existing_data = c.fetchone()

        if existing_data:
            update_query = 'UPDATE user_data SET '
            update_values = []

            if not existing_data.weight_is_user_set:
                update_query += 'weight=?, weight_is_user_set=?, '
                update_values.extend([athlete.get('weight'), False])

            if not existing_data.sex_is_user_set:
                update_query += 'sex=?, sex_is_user_set=?, '
                update_values.extend([athlete.get('sex'), False])

            if not existing_data.age_is_user_set:
                update_query += 'age=?, age_is_user_set=?, '
                update_values.extend([athlete.get('age'), False])

            if not existing_data.firstname_is_user_set:
                update_query += 'firstname=?, firstname_is_user_set=?, '
                update_values.extend([athlete.get('firstname'), False])

            if not existing_data.lastname_is_user_set:
                update_query += 'lastname=?, lastname_is_user_set=?, '
                update_values.extend([athlete.get('lastname'), False])

            update_query = update_query.rstrip(', ') + ' WHERE user_id=?'
            update_values.append(current_user.id)

            c.execute(update_query, tuple(update_values))
        else:
            c.execute('''
                INSERT INTO user_data (
                    user_id, weight, sex, age, firstname, lastname,
                    height_is_user_set, weight_is_user_set, sex_is_user_set,
                    age_is_user_set, firstname_is_user_set, lastname_is_user_set
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_user.id, athlete.get('weight'), athlete.get('sex'),
                athlete.get('age'), athlete.get('firstname'), athlete.get('lastname'),
                False, False, False, False, False, False
            ))

        conn.commit()
        conn.close()

        
        conn = sqlite3.connect(db_name)
        conn.row_factory = RowWithAttr  # Enable attribute access
        c = conn.cursor()
        # Fetch updated data
        c.execute('SELECT * FROM user_data WHERE user_id=?', (current_user.id,))
        user_data = c.fetchone()
        conn.close()

        # Add computed fields
        if user_data:
            user_data.weight_imperial = kg_to_lbs(user_data.weight) if user_data.weight is not None else None
            height_ft_in = cm_to_ft_in(user_data.height) if getattr(user_data, 'height', None) is not None else {'feet': None, 'inches': None}
            user_data.height_feet = height_ft_in['feet']
            user_data.height_inches = height_ft_in['inches']

        return user_data  # or jsonify(...) depending on how it's used

    except Exception as e:
        print(f"Error in get_user_data: {e}")
        return None

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    user_data = get_user_data()
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM user_stats WHERE user_id=?', (current_user.id,))
    user_stats = c.fetchone()
    conn.close()
    if request.method == 'POST':
        # Read and update values
        weight_lbs = float(request.form.get('weight'))
        height_feet = int(request.form.get('height_feet'))
        height_inches = float(request.form.get('height_inches'))
        age = int(request.form.get('age'))
        sex = request.form.get('sex')
        pace_minutes = request.form.get('pace_minutes')
        pace_seconds = request.form.get('pace_seconds')
        if pace_minutes and pace_seconds:
            pace_seconds = float(pace_seconds)
            pace_minutes = float(pace_minutes)
            fastest_pace = (pace_minutes * 60) + pace_seconds
            fastest_pace = 1609.34 / fastest_pace
        
        # Convert lbs to kg
        weight_kg = weight_lbs / 2.20462
        height_cm = (height_feet * 30.48) + (height_inches * 2.54)
        int(height_cm)
        int(age)
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        c.execute('''
            UPDATE user_data
            SET weight = ?, weight_is_user_set = 1,
                height = ?, height_is_user_set = 1,
                age = ?, age_is_user_set = 1,
                sex = ?, sex_is_user_set = 1,
                fastest_pace = ?
            WHERE user_id = ?
        ''', (
            weight_kg,
            height_cm,
            age,
            sex,
            fastest_pace,
            current_user.id
        ))

        conn.commit()
        conn.close()
        
        max_hr = int(request.form.get('max_hr'))
        stride_length = float(request.form.get('stride_length'))
        stride_length_metric = stride_length * 2.54
        hosc = float(request.form.get('hosc'))
        afrontal = float(request.form.get('afrontal'))
        ftp = request.form.get('ftp')
        update_user_stats(current_user.id, max_hr, stride_length_metric, hosc, afrontal, ftp)
        
        return redirect(url_for('profile'))  # back to view
    return render_template('edit_profile.html', user_data=user_data, user_stats=user_stats)

@app.route('/upload_pfp', methods=['POST'])
@login_required
def upload_pfp():
    if 'profile_picture' not in request.files:
        print('No file part in the request.')
        return redirect(url_for('profile'))

    file = request.files['profile_picture']

    if file.filename == '':
        print('No selected file.')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Check if a profile picture already exists and delete it
        if current_user.profile_pic != '/default_pfp.png' or current_user.profile_pic != '/static/default_pfp.png':
            old_pfp_path = (f"static/{current_user.profile_pic.lstrip('/')}")
            print(old_pfp_path)
            if os.path.exists(old_pfp_path) and old_pfp_path != 'static/default_pfp.png':
                os.remove(old_pfp_path)

        file.save(filepath)

        # Update the database with the new profile picture path
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute('UPDATE users SET profile_pic=? WHERE id=?', (f'pfps/{filename}', current_user.id))
        conn.commit()
        conn.close()

        # Update the current_user object with the new profile picture path
        current_user.profile_pic = f'static/pfps/{filename}'

        print('Profile picture updated successfully.')
        return redirect(url_for('profile'))
    else:
        print('Allowed image types are png, jpg, jpeg, gif.')
        return redirect(url_for('profile'))

@app.route('/unlink_strava', methods=['POST'])
@login_required
def unlink_strava():
    url = "https://www.strava.com/oauth/deauthorize"
    access_token = get_valid_access_token()
    if not access_token:
        # No token, but treat as success for UI consistency
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"message": "Strava account already disconnected."}), 200
        return redirect(url_for('index', unlinked=1))
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, headers=headers)
    # Always delete tokens locally, regardless of Strava response
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('DELETE FROM tokens WHERE user_id=?', (current_user.id,))
    conn.commit()
    conn.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"message": "Strava account has been disconnected from Strava."}), 200
    return redirect(url_for('index', unlinked=1))

def load_activities_with_rpe(user_id):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT activity_id, data, rpe FROM activities WHERE user_id=?', (user_id,))
    activities = []
    for row in c.fetchall():
        act = json.loads(row[1])
        if row[2] is not None:
            act['rpe'] = row[2]
        activities.append(act)
    conn.close()
    return activities

@app.route('/set_rpe/<int:activity_id>', methods=['POST'])
@login_required
def set_rpe(activity_id):
    rpe = request.form.get('rpe')
    if rpe is not None:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        # Update rpe column
        c.execute('UPDATE activities SET rpe=? WHERE user_id=? AND activity_id=?', (rpe, current_user.id, activity_id))
        # Also update the JSON data
        c.execute('SELECT data FROM activities WHERE user_id=? AND activity_id=?', (current_user.id, activity_id))
        row = c.fetchone()
        if row is not None and row[0] is not None:
            act_data = json.loads(row[0])
            act_data['rpe'] = float(rpe)
            c.execute('UPDATE activities SET data=? WHERE user_id=? AND activity_id=?', (json.dumps(act_data), current_user.id, activity_id))
        conn.commit()
        conn.close()
    # After updating RPE in DB
    activities = load_activities_with_rpe(current_user.id)
    get_user_fitness(activities)
    return redirect(url_for('activity_details', activity_id=activity_id))

@app.route('/activity/<int:activity_id>')
def activity_details(activity_id):
    access_token = get_valid_access_token()
    if not access_token:
        return jsonify({'error': 'No valid token. Please authorize.'}), 400
    try:
        url = f"https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=true"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        activity = response.json()
        laps = activity.get("laps", [])
        # Get streams
        streams_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
        params = {"keys": "altitude,distance,time", "key_by_type": "true"}
        streams_resp = requests.get(streams_url, headers=headers, params=params)
        streams_resp.raise_for_status()
        streams = streams_resp.json()
        get_user_data()
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute('SELECT rpe FROM activities WHERE user_id=? AND activity_id=?', (current_user.id, activity_id))
        row = c.fetchone()
        conn.close()
        rpe = row[0] if row is not None and row[0] is not None else None
        activity['rpe'] = rpe
        user_id = current_user.id  # or however you get the logged-in user's id
        fitness_changes = get_activity_fitness_changes(activity_id)
        return render_template('activity_details.html', activity=activity, laps=laps, streams=streams, fitness_changes=fitness_changes)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute('SELECT id, username, password_hash, profile_pic FROM users WHERE username=?', (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[2], password):
            user = User(row[0], row[1], row[3])
            login_user(user)
            next_page = request.args.get('next') or url_for('index')
            return redirect(next_page)
        else:
            print('Invalid username or password.')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username=?', (username,))
        if c.fetchone():
            conn.close()
            print('Username already exists.')
            return render_template('signup.html')
        password_hash = generate_password_hash(password)
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        c.execute('SELECT id, username, profile_pic FROM users WHERE username=?', (username,))
        row = c.fetchone()
        conn.commit()
        c.execute('SELECT id, username, profile_pic FROM users WHERE username=?', (username,))
        row = c.fetchone()
        conn.close()
        user = User(row[0], row[1], row[2])
        login_user(user)
        next_page = request.args.get('next') or url_for('index')
        if next_page != url_for('index'):
            return redirect(next_page)
        return redirect(url_for('profile_not_found'))
    return render_template('signup.html')

@app.route('/profile_not_found')
def profile_not_found():
    return render_template('after_signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def get_hr_zones():
    access_token = get_valid_access_token()
    if not access_token:
        return jsonify({'error': 'No valid token. Please authorize.'}), 400
    try:
        url = "https://www.strava.com/api/v3/athlete/zones"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        hr_zones = response.json()
        conn = sqlite3.connect(db_name)
        conn.row_factory = RowWithAttr
        c = conn.cursor()
        c.execute('DELETE FROM user_hr_zones WHERE user_id=?', (current_user.id,))
        for zone_number, zone in enumerate(hr_zones['heart_rate']['zones'], 1):
            c.execute('''
                INSERT INTO user_hr_zones (user_id, zone_number, min_hr, max_hr)
                VALUES (?, ?, ?, ?)
            ''', (current_user.id, zone_number, zone['min'], zone['max']))
        conn.commit()
        conn.close()
        return jsonify(hr_zones)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/profile')
@login_required
def profile():
    get_hr_zones()
    get_user_data()
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM user_data WHERE user_id=?', (current_user.id,))
    user_data = c.fetchone()
    c.execute('SELECT * FROM user_hr_zones WHERE user_id=?', (current_user.id,))
    hr_zones = c.fetchall()
    c.execute('SELECT * FROM user_stats WHERE user_id=?', (current_user.id,))
    user_stats = c.fetchone()
    conn.close()
    if user_data:
        return render_template('profile.html', user_data=user_data, hr_zones=hr_zones, user_stats=user_stats)
    else:
        print('No profile data found. Please update your profile.')
        return redirect(url_for('profile_not_found'))


if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(host='localhost', port=8000, debug=True)