import math
from datetime import date, timedelta

# Define constants
Tfit = 42  # Time constant for fitness (days)
Tfat = 7   # Time constant for fatigue (days)
time_normalization = 1  # Normalization factor for simplicity

# Example list of past workouts with date and RE Activity
today = date(2025, 4, 10)
workouts = [
    {"date": date(2025, 3, 31), "re_activity": 100},  # 10 days ago
    {"date": date(2025, 4, 5), "re_activity": 150},   # 5 days ago
    {"date": date(2025, 4, 9), "re_activity": 200},   # 1 day ago
]

def calculate_training_load(workouts, today, T):
    total_load = 0
    for workout in workouts:
        delta_t = (today - workout["date"]).days  # Calculate the time difference in days
        decay_factor = math.exp(-delta_t / T)  # Calculate the decay factor
        contribution = workout["re_activity"] * decay_factor  # Contribution from this workout
        total_load += contribution  # Add to the sum
    training_load = total_load / time_normalization  # Normalize by 'time' if needed
    return training_load

def calculate_tsb(ctl, atl):
    return ctl - atl

# Calculate CTL
current_ctl = calculate_training_load(workouts, today, Tfit)
print("Current CTL:", current_ctl)

# Calculate ATL
current_atl = calculate_training_load(workouts, today, Tfat)
print("Current ATL:", current_atl)

# Calculate TSB (Form)
current_tsb = calculate_tsb(current_ctl, current_atl)
print("Current TSB:", current_tsb)
