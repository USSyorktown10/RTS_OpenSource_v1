import json
import math
from datetime import datetime
import os
import time
import zoneinfo

DATA_FILE = "runner_data.json"
tz = zoneinfo.ZoneInfo("America/New_York")

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

def save_data(key, value):
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
    metric_imperial = input("Enter 'metric' or 'imperial': ").strip().lower()
    if metric_imperial == "imperial":
        preference = 'imperial'
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
        time.sleep(2)
        return
    elif metric_imperial == "metric":
        print("Sorry for the inconvenience, but the metric system is not supported yet.")
        time.sleep(3)
        return
    
from datetime import datetime, timedelta
import math

def update_fitness_metrics():
    """
    Updates CTL, ATL, TSB, and normalized values based on the current date and activity history.
    """
    user_constants = load_data("user_constants")
    activities = load_data("activities") or []
    now = datetime.now()
    Tfit = user_constants["Tfit_days"]
    Tfat = user_constants["Tfat_days"]

    # Calculate CTL
    ctl_sum = 0
    for activity in activities:
        # Parse the timestamp and calculate delta_t in days
        activity_timestamp = datetime.strptime(activity['timestamp'], '%Y-%m-%d %H:%M:%S')
        delta_t = (now - activity_timestamp).total_seconds() / (60 * 60 * 24)
        exp_factor = math.exp(-delta_t / Tfit)
        ctl_sum += activity['RE'] * exp_factor

    ctl = ctl_sum
    save_data("CTL", ctl)

    # Calculate ATL
    atl_sum = 0
    for activity in activities:
        # Parse the timestamp and calculate delta_t in days
        activity_timestamp = datetime.strptime(activity['timestamp'], '%Y-%m-%d %H:%M:%S')
        delta_t = (now - activity_timestamp).total_seconds() / (60 * 60 * 24)
        exp_factor = math.exp(-delta_t / Tfat)
        atl_sum += activity['RE'] * exp_factor

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

def calculate():
    user_constants = load_data("user_constants")
    Erun = user_constants["Erun"]              # J/kg/m
    mass = user_constants["weight_kg"]         # kg
    gravity = user_constants["g"]              # 9.81 m/s^2
    hosc = user_constants["hosc"]              # meters
    Afrontal = user_constants["Afrontal"]      # m^2
    Cd = user_constants["Cd"]                  # unitless
    air_density = user_constants["air_density"]# kg/m^3
    stride_length = user_constants["stride_length"]  # meters

    # Input data for the run
    total_minutes = int(input("Enter time (minutes): "))
    total_seconds = int(input("Enter seconds: "))
    total_time_sec = total_minutes * 60 + total_seconds  # total time in seconds

    distance = float(input("Enter distance (miles): "))
    distance_m = distance * 1609.34   # convert miles to meters

    speed = distance_m / total_time_sec  # m/s

    elev1 = float(input("Enter starting elevation (ft): ")) * 0.3048
    elev2 = float(input("Enter ending elevation (ft): ")) * 0.3048

    elev_gain = elev2 - elev1  # meters
    gradient = elev_gain / distance_m  # unitless (rise/run)

    cadence = (speed * 2) / stride_length  # steps per second

    power_horizontal = Erun * mass * speed
    vertical_power = mass * gravity * hosc * cadence
    air_resistance = 0.5 * air_density * Afrontal * Cd * (speed ** 3)
    incline_power = mass * gravity * speed * gradient

    wattage = power_horizontal + vertical_power + air_resistance + incline_power

    hr_avg = input("Enter average heart rate (BPM): ")
    if hr_avg:
        max_hr = user_constants["max_HR"]
        HR_avg_frac = float(hr_avg) / max_hr
    else:
        HR_avg_frac = 0.75  # Default value
        
    term1 = (wattage * distance) / mass * (1 / total_time_sec)
    term2 = (elev_gain / distance_m) * 1000
    relative_effort = term1 + term2 * HR_avg_frac
    
    # Load existing activities
    activities = load_data("activities") or []
    now = datetime.now()
    Tfit = user_constants["Tfit_days"]
    Tfat = user_constants["Tfat_days"]
    
    # Calculate CTL
    ctl_sum = 0
    for activity in activities:
        delta_t = (now - datetime.strptime(activity['timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() / (60 * 60 * 24)
        exp_factor = math.exp(-delta_t / Tfit)
        ctl_sum += activity['RE'] * exp_factor
        
    ctl = ctl_sum
    save_data("CTL", ctl)
    
    # Calculate ATL
    atl_sum = 0
    for activity in activities:
        delta_t = (now - datetime.strptime(activity['timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() / (60 * 60 * 24)
        exp_factor = math.exp(-delta_t / Tfat)
        atl_sum += activity['RE'] * exp_factor
    
    atl = atl_sum
    save_data("ATL", atl)
    
    # Calculate TSB
    tsb = ctl - atl
    normalized_ctl = (ctl - user_constants["CTLmin"]) / (user_constants["CTLmax"] - user_constants["CTLmin"]) * 100
    normalized_atl = (atl - user_constants["ATLmin"]) / (user_constants["ATLmax"] - user_constants["ATLmin"]) * 100
    save_data("TSB", tsb)
    save_data("normalized_CTL", normalized_ctl)
    save_data("normalized_ATL", normalized_atl)
    
    # Save the current run data
    activity = {
        "timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
        "time_seconds": total_time_sec,
        "distance_miles": distance,
        "pace": total_time_sec / distance,  # seconds per mile
        "wattage": wattage,
        "RE": relative_effort,
        "CTL": ctl,
        "ATL": atl,
        "TSB": tsb,
        "normalized_CTL": normalized_ctl,
        "normalized_ATL": normalized_atl
    }
    activities.append(activity)
    save_data("activities", activities)
    
    print("Run data saved successfully.")
    
    update_fitness_metrics()
    return activity

def show_recent_runs():
    activities = load_data("activities")
    if activities:
        print("<===================== Recent Runs =====================>")
        for activity in activities[-5:]:
            # Convert the timestamp string back to a datetime object
            timestamp = datetime.strptime(activity['timestamp'], '%Y-%m-%d %H:%M:%S')
            
            # Convert pace from seconds to minutes:seconds format
            minutes, seconds = divmod(activity['pace'], 60)
            formatted_pace = f"{int(minutes)}:{int(seconds):02d} min/mile"
            
            print(f"Date and Time: {timestamp.strftime('%B %-d, %Y, %-I:%M %p %Z')}\n"
                  f"Distance: {activity['distance_miles']} miles\n"
                  f"Pace: {formatted_pace}\n"
                  f"Wattage: {activity['wattage']:.2f} W\n"
                  f"Relative Effort: {activity['RE']:.2f}\n"
                  f"TSB: {activity['TSB']:.0f}\n"
                  f"Normalized CTL: {activity['normalized_CTL']:.0f}\n"
                  f"Normalized ATL: {activity['normalized_ATL']:.0f}\n")
            print("---------------------------------------------------------")
        input("Press Enter to return to the main menu...")
    else:
        print("No recent runs found.")
        time.sleep(2)

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

def stats_and_averages():
    activities = load_data("activities")
    if activities:
        total_distance = sum(activity['distance_miles'] for activity in activities)
        total_time = sum(activity['time_seconds'] for activity in activities)
        # Convert total_time from seconds to minutes:seconds format
        formatted_total_time = format_total_time(total_time)
        
        total_runs = len(activities)
        
        avg_distance = total_distance / total_runs
        avg_time = total_time / total_runs
        avg_pace = avg_time / avg_distance
        
        avg_minutes, avg_seconds = divmod(avg_time, 60)
        formatted_avg_time = f"{int(avg_minutes)}:{int(avg_seconds):02d}"
        
        minutes, seconds = divmod(avg_pace, 60)
        formatted_avg_pace = f"{int(minutes)}:{int(seconds):02d} min/mile"
        
        print("\n<===================== Stats and Averages =====================>")
        print(f"Total Distance: {total_distance:.2f} miles")
        print(f"Total Time: {formatted_total_time}")
        print(f"Average Distance: {avg_distance:.2f} miles")
        print(f"Average Time: {formatted_avg_time}")
        print(f"Average Pace: {formatted_avg_pace}")
        print("---------------------------------------------------------\n")
        input("Press Enter to return to the main menu...")
    else:
        print("No data available to calculate stats and averages.")
        time.sleep(2)

def homescreen():
    daily_update()
    os.system('cls' if os.name == 'nt' else 'clear')
    if os.path.exists(DATA_FILE):
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("<===================== RTS v. 0.0.0-alpha.2 =====================>")
            print("                 |--| Terminal Basic Version |--|")
            print("1. Enter Run Data")
            print("2. View Recent Runs")
            print("3. View Stats and Averages")
            option = input("Select an option (1-3): ")
            if option == "1":
                calculate()
                time.sleep(2)
            elif option == "2":
                show_recent_runs()
            elif option == "3":
                stats_and_averages()
            else:
                print("Invalid option. Please try again.")
                time.sleep(2)
    else:
        get_user_data()

def daily_update():
    now = datetime.now()
    user_constants = load_data("user_constants")
    if not user_constants.get("next_update"):
        user_constants["next_update"] = (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        save_data("user_constants", user_constants)
        return
    
    next_update = datetime.strptime(user_constants["next_update"], '%Y-%m-%d %H:%M:%S')
    if now < next_update:
        return
    else:
        # Update the last update time
        user_constants["next_update"] = (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        save_data("user_constants", user_constants)

        # Perform daily update
        update_fitness_metrics()


homescreen()