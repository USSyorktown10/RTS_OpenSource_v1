import json
import os
import time
import zoneinfo
from datetime import datetime, timedelta, timezone
import math

DATA_FILE = "user_data.json"
local_tz = zoneinfo.ZoneInfo("America/New_York")

def load_data(key):
    if not os.path.exists(DATA_FILE):
        get_user_data()
    else:
        try:
            with open(DATA_FILE, "r") as file:
                data = json.load(file)
            if key in data:
                return data[key]
            else:
                raise KeyError(f"Key '{key}' not found in data.")
        except KeyError as e:
            print(f"Error loading data: {e}")
            return None
        
def load_all_data():
    if not os.path.exists(DATA_FILE):
        get_user_data()
    else:
        try:
            with open(DATA_FILE, "r") as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print("File not Found.")
            return None
        except json.JSONDecodeError:
            print("Error decoding JSON data.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

def save_data(key, value):
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as file:
            json.dump({}, file)
    try:
        with open(DATA_FILE, "r+") as file:
            data = json.load(file)
            if key in data:
                data[key] = value
            else:
                data[key] = value
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
    except FileNotFoundError:
        print("File not Found.")
        
def get_user_data():
    print("Welcome to RTS v.0.0.0-alpha.3. This is an offline version and preview of the online version.")
    time.sleep(2)
    print("Please enter your data:")
    metric_imperial = input("Enter 'metric' or 'imperial': ").strip().lower()
    if metric_imperial == "imperial":
        preference = 'imperial'
        user_age = input("Enter your age in years: ")
        user_height = input("Enter your height in inches: ")
        user_weight = input("Enter your weight in pounds: ")
        user_max_hr = input("Enter your max heart rate: ")
        user_stride_length = input("Enter your stride length in inches: ")
        user_HR_zones = {
            "zone1": 0.60,
            "zone2": 0.70,
            "zone3": 0.80,
            "zone4": 0.90,
            "zone5": 1.00
        }
        user_Erun = 1.036
        user_hosc = 0.07
        user_Afrontal = 0.5
        user_Cd = 1.0
        user_air_density = 0.0765
        user_CTLmin = 0
        user_CTLmax = 200
        user_ATLmin = 0
        user_ATLmax = 100
        user_Tfit_days = 42
        user_Tfat_days = 7
        user_g = 9.81
        user_constants = {
            "preference": preference,
            "age": int(user_age),
            "weight_kg": float(user_weight) * 0.453592,
            "height_m": float(user_height) * 0.0254,
            "max_HR": int(user_max_hr),
            "stride_length": float(user_stride_length) * 0.0254,
            "HR_zones": user_HR_zones,
            "Erun": user_Erun,
            "hosc": user_hosc,
            "Afrontal": user_Afrontal,
            "Cd": user_Cd,
            "air_density": user_air_density,
            "CTLmin": user_CTLmin,
            "CTLmax": user_CTLmax,
            "ATLmin": user_ATLmin,
            "ATLmax": user_ATLmax,
            "Tfit_days": user_Tfit_days,
            "Tfat_days": user_Tfat_days,
            "g": user_g
        }
        save_data("user_constants", user_constants)
        print("User data saved successfully.")
        if load_data("activities") is KeyError:
            activities = []
            save_data("activities", activities)
        time.sleep(2)
        return
    elif metric_imperial == "metric":
        print("Sorry for the inconvenience, but the metric system is not supported yet.")
        time.sleep(3)
        return
    

def format_total_time(total_seconds):
    """
    Formats total time from seconds into days, hours, minutes, and seconds.
    Omits days and hours if they are zero.
    """
    days, remainder = divmod(total_seconds, 86400)  # 86400 seconds in a day
    hours, remainder = divmod(remainder, 3600)     # 3600 seconds in an hour
    minutes, seconds = divmod(remainder, 60)      # 60 seconds in a minute

    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"

def input_run_data():
    """
    Allows the user to input run details and saves the data.
    """
    activities = load_data("activities") or []
    user_constants = load_data("user_constants")
    now = datetime.now(timezone.utc)

    # Input run details
    distance_miles = float(input("Enter distance (miles): "))
    total_minutes = int(input("Enter time (minutes): "))
    total_seconds = int(input("Enter seconds: "))
    total_time_sec = total_minutes * 60 + total_seconds
    avg_hr = int(input("Enter average heart rate (BPM): "))
    cadence = int(input("Enter average cadence (steps per minute): "))
    elevation_gain_ft = float(input("Enter elevation gain (feet): "))
    elevation_gain_m = elevation_gain_ft * 0.3048  # Convert to meters

    # Constants from user data
    weight_kg = user_constants["weight_kg"]
    max_hr = user_constants["max_HR"]
    Erun = user_constants["Erun"]  # Energy cost of running (J/kg/m)
    gravity = user_constants["g"]  # Gravitational acceleration (m/s^2)
    Afrontal = user_constants["Afrontal"]  # Frontal area (m^2)
    Cd = user_constants["Cd"]  # Drag coefficient
    air_density = user_constants["air_density"]  # Air density (kg/m^3)
    hosc = user_constants["hosc"]  # Vertical oscillation (m)

    # Convert distance to kilometers
    distance_km = distance_miles * 1.60934

    # Calculate power (P) in watts
    velocity_mps = distance_km * 1000 / total_time_sec  # Velocity in m/s
    power = (
        Erun * weight_kg * velocity_mps  # Energy cost of running
        + 0.5 * air_density * Afrontal * Cd * velocity_mps**3  # Air resistance
        + weight_kg * gravity * hosc * velocity_mps  # Vertical oscillation
    )

    # Calculate HRavg as a percentage of max HR
    hr_avg_percentage = avg_hr / max_hr

    # Calculate relative effort (RE)
    terrain_adjustment = 1 + (elevation_gain_m / distance_km) if distance_km > 0 else 1
    relative_effort = ((power * distance_km) / weight_kg) * (1 / total_time_sec) + (terrain_adjustment * hr_avg_percentage)

    # Save the run data
    activity = {
        "timestamp": now.strftime('%Y-%m-%d %H:%M:%S%z'),
        "distance_miles": distance_miles,
        "time_seconds": total_time_sec,
        "avg_hr": avg_hr,
        "cadence": cadence,
        "elevation_gain_m": elevation_gain_m,
        "pace": total_time_sec / distance_miles,  # Pace in seconds per mile
        "relative_effort": relative_effort
    }
    activities.append(activity)
    save_data("activities", activities)

    print("Run data saved successfully.")
    update_fitness_metrics()
    input("Press Enter to return to the main menu...")

def update_fitness_metrics():
    """
    Updates CTL, ATL, TSB, and normalized values based on the current date and activity history.
    """
    user_constants = load_data("user_constants")
    activities = load_data("activities") or []
    now = datetime.now(timezone.utc)  # Make 'now' offset-aware
    Tfit = user_constants["Tfit_days"]
    Tfat = user_constants["Tfat_days"]

    # Calculate CTL
    ctl_sum = 0
    for activity in activities:
        # Parse the timestamp and calculate delta_t in days
        activity_timestamp = datetime.strptime(activity['timestamp'], '%Y-%m-%d %H:%M:%S%z')
        delta_t = (now - activity_timestamp).total_seconds() / (60 * 60 * 24)
        exp_factor = math.exp(-delta_t / Tfit)
        ctl_sum += activity['relative_effort'] * exp_factor

    ctl = ctl_sum
    save_data("CTL", ctl)

    # Calculate ATL
    atl_sum = 0
    for activity in activities:
        # Parse the timestamp and calculate delta_t in days
        activity_timestamp = datetime.strptime(activity['timestamp'], '%Y-%m-%d %H:%M:%S%z')
        delta_t = (now - activity_timestamp).total_seconds() / (60 * 60 * 24)
        exp_factor = math.exp(-delta_t / Tfat)
        atl_sum += activity['relative_effort'] * exp_factor

    atl = atl_sum
    save_data("ATL", atl)

    # Calculate TSB
    tsb = ctl - atl
    save_data("TSB", tsb)

    # Calculate normalized CTL and ATL
    normalized_ctl = (ctl - user_constants["CTLmin"]) / (user_constants["CTLmax"] - user_constants["CTLmin"]) * 100 if ctl > 0 else 0
    normalized_atl = (atl - user_constants["ATLmin"]) / (user_constants["ATLmax"] - user_constants["ATLmin"]) * 100 if atl > 0 else 0
    save_data("normalized_CTL", normalized_ctl)
    save_data("normalized_ATL", normalized_atl)

    print(f"Fitness metrics updated:\nCTL: {ctl:.2f}, ATL: {atl:.2f}, TSB: {tsb:.2f}")
    print(f"Normalized CTL: {normalized_ctl:.2f}%, Normalized ATL: {normalized_atl:.2f}%")

def view_run_details():
    """
    Displays details of the most recent runs.
    """
    activities = load_data("activities")
    if activities:
        print("<===================== Recent Runs =====================>")
        for activity in activities[-5:]:
            timestamp = datetime.strptime(activity['timestamp'], '%Y-%m-%d %H:%M:%S%z')
            local_time = timestamp.astimezone()
            minutes, seconds = divmod(activity['pace'], 60)
            formatted_pace = f"{int(minutes)}:{int(seconds):02d} min/mile"

            print(f"Date and Time (Local): {local_time.strftime('%B %-d, %Y, %-I:%M %p %Z')}")
            print(f"Distance: {activity['distance_miles']} miles")
            print(f"Time: {format_total_time(activity['time_seconds'])}")
            print(f"Average Heart Rate: {activity['avg_hr']} BPM")
            print(f"Cadence: {activity['cadence']} spm")
            print(f"Elevation Gain: {activity['elevation_gain_m']:.2f} meters")
            print(f"Pace: {formatted_pace}")
            print("---------------------------------------------------------")
        input("Press Enter to return to the main menu...")
    else:
        print("No recent runs found.")
        time.sleep(2)
        
def view_fitness_metrics():
    """
    Displays accumulated weekly relative effort, CTL, and ATL.
    """
    ctl = load_data("CTL") or 0
    atl = load_data("ATL") or 0
    tsb = ctl - atl
    activities = load_data("activities") or []

    # Calculate weekly relative effort
    now = datetime.now(timezone.utc)
    weekly_effort = sum(
        activity["relative_effort"]
        for activity in activities
        if (now - datetime.strptime(activity["timestamp"], '%Y-%m-%d %H:%M:%S%z')).days <= 7
    )

    print("<===================== Fitness Metrics =====================>")
    print(f"Weekly Relative Effort: {weekly_effort:.2f}")
    print(f"CTL (Chronic Training Load): {ctl:.2f}")
    print(f"ATL (Acute Training Load): {atl:.2f}")
    print(f"TSB (Training Stress Balance): {tsb:.2f}")
    print("---------------------------------------------------------")
    input("Press Enter to return to the main menu...")
    
def ai_insights():
    """
    Analyzes running history and provides insights to prevent burnout or injury.
    """
    activities = load_data("activities") or []
    if not activities:
        print("No data available for AI insights.")
        time.sleep(2)
        return

    # Analyze running history
    weekly_mileage = sum(
        activity["distance_miles"]
        for activity in activities
        if (datetime.now(timezone.utc) - datetime.strptime(activity["timestamp"], '%Y-%m-%d %H:%M:%S%z')).days <= 7
    )
    previous_week_mileage = sum(
        activity["distance_miles"]
        for activity in activities
        if 7 < (datetime.now(timezone.utc) - datetime.strptime(activity["timestamp"], '%Y-%m-%d %H:%M:%S%z')).days <= 14
    )

    # Detect irregularities
    if weekly_mileage > previous_week_mileage * 1.5:
        print("Warning: Your weekly mileage has increased significantly. Consider reducing mileage to prevent burnout or injury.")
    elif weekly_mileage < previous_week_mileage * 0.5:
        print("Note: Your weekly mileage has decreased significantly. Gradually increase mileage to maintain fitness.")

    print("---------------------------------------------------------")
    input("Press Enter to return to the main menu...")



def stats_and_averages():
    """
    Displays stats and averages, including weekly mileage, time, and pace.
    """
    activities = load_data("activities") or []
    if activities:
        # Total stats
        total_distance = sum(activity['distance_miles'] for activity in activities)
        total_time = sum(activity['time_seconds'] for activity in activities)
        formatted_total_time = format_total_time(total_time)
        total_runs = len(activities)
        avg_distance = total_distance / total_runs
        avg_time = total_time / total_runs
        avg_pace = total_time / total_distance
        avg_minutes, avg_seconds = divmod(avg_pace, 60)
        formatted_avg_pace = f"{int(avg_minutes)}:{int(avg_seconds):02d} min/mile"

        # Weekly stats (starting on Monday)
        now = datetime.now(timezone.utc)
        start_of_week = now - timedelta(days=now.weekday())  # Monday of the current week
        weekly_activities = [
            activity for activity in activities
            if datetime.strptime(activity['timestamp'], '%Y-%m-%d %H:%M:%S%z') >= start_of_week
        ]
        weekly_mileage = sum(activity['distance_miles'] for activity in weekly_activities)
        weekly_time = sum(activity['time_seconds'] for activity in weekly_activities)
        formatted_weekly_time = format_total_time(weekly_time)
        weekly_pace = weekly_time / weekly_mileage if weekly_mileage > 0 else 0
        weekly_minutes, weekly_seconds = divmod(weekly_pace, 60)
        formatted_weekly_pace = f"{int(weekly_minutes)}:{int(weekly_seconds):02d} min/mile" if weekly_mileage > 0 else "N/A"

        # Print stats
        print("\n<===================== Stats and Averages =====================>")
        print(f"Total Distance: {total_distance:.2f} miles")
        print(f"Total Time: {formatted_total_time}")
        print(f"Average Distance: {avg_distance:.2f} miles")
        print(f"Average Time: {format_total_time(avg_time)}")
        print(f"Average Pace: {formatted_avg_pace}")
        print("\n<===================== Weekly Stats =====================>")
        print(f"Weekly Mileage: {weekly_mileage:.2f} miles")
        print(f"Weekly Time: {formatted_weekly_time}")
        print(f"Average Weekly Pace: {formatted_weekly_pace}")
        print("---------------------------------------------------------\n")
        input("Press Enter to return to the main menu...")
    else:
        print("No data available to calculate stats and averages.")
        time.sleep(2)
        
def daily_update():
    now = datetime.now()
    user_constants = load_data("user_constants")
    try: 
        if not user_constants.get("next_update"):
            user_constants["next_update"] = (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S%z')
            save_data("user_constants", user_constants)
            return
    except AttributeError:
        print("Error: User constants not found. Please restart program if you have already entered data.")
        return
    
data = load_all_data()
if data:
    if "activities" in data:
        None
    else:
        data["activities"] = []
        with open(DATA_FILE, "w") as file:
            json.dump(data, file, indent=4)
            print("Activities key added to user_data.json.")
    if "user_constants" in data:
        None
    else:
        get_user_data()

def homescreen():
    daily_update()
    os.system('cls' if os.name == 'nt' else 'clear')
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("<===================== RTS =====================>")
        print("1. Enter Run Data")
        print("2. View Recent Runs")
        print("3. View Stats and Averages")
        print("4. View Fitness Metrics")
        print("5. AI Insights")
        print("6. Exit")
        option = input("Select an option (1-6): ")
        if option == "1":
            input_run_data()
        elif option == "2":
            view_run_details()
        elif option == "3":
            stats_and_averages()
        elif option == "4":
            view_fitness_metrics()
        elif option == "5":
            ai_insights()
        elif option == "6":
            os.system('cls' if os.name == 'nt' else 'clear')
            print("TERMINAL CLEARED FOR SECURITY")
            print("RETURNING TO DEFAULT TERMINAL.")
            break
        else:
            print("Invalid option. Please try again.")
            
homescreen()