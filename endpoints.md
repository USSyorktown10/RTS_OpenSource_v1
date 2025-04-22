# Functions and Endpoints

## Functions
- ### Home
  - Shows all activities from friends, recommended challenges, targets, and weekly stats
- ### RTS AI
  - Recommended workout for the day
  - Daily Brefing: can send notification every day at certain time too
    - The weather today, what time you should run at, what to eat, route for the day, workout for the day, and feedback/input on what you want to do
    - IF YOU HAVE A TRAINING PLAN:
      - What todays run will be, what time you should do it at, what to wear (run wear)
  - Find me routes for this workout (RTS Pathfunder)
    - Maps, routes, workout so that GAP=Target pace
  - Run wear - gives you clothes to use during runs that allow mobility but keep you warm/cool
  - **Training Plans**
    - 
    - **Start**
      - 400, 800, 1600, 3k, 3200, 5k, 10k, Half-Marathon, Marathon, Custom
      - Give goal for distance
      - Give fastest mile
        - If you dont have a mile time yet, it will instruct you to go out and run one
      - Give weeks until
      - It will then calculate if you have enough time to do it.
        - CALC: D = distance(miles), G = goal time for race(minutes), T = fastest mile time(minutes per mile), W = training duration(weeks), F = improvement factor(rate of weekly progress)
        - CONVERT min/mi with this: 
          - seconds --> decimal: $\frac{seconds}{60}$ aka: (seconds/60)
          - decimal --> seconds: decimal * 60
        - **STEPS:**
          - 
          - 1. Calculate Target page (TP)
            - TP = $\frac{g}{d}$ also shown as: (G/D) goal time for race/distance
              - Results in required pace in minutes per mile
          - 2. Calculate Improvement needed (I)
            - I = T - TP 
            - This calculates the difference between fastest mile and target pace
          - 3. Estimate training duration
            - IF I > 0:
              - W = $\frac{\log\left(\frac{T}{\text{TP}}\right)}{\log(1 + F)}$
              - Finds estimated weeks with F as training factor (estimated 2% per week)
            - IF I ≤ 0:
              - W = Min. conditioning period
              - Approx. 8-12 weeks
    - **View Current Stats**
      - 
      - See what you are doing today
      - Veiw calender (if everything goes according to plan, this will work)
        - Can change calender and runs based on sleep, food, hydration, etc.
      - See how everyhting thats going on in your life affects this training plan
      - Weeks left, estimated pace (based on fitness) compared to goal pace
- **Injury Prevention and Nutrition**
  - 
  - Log for injuries
  - AI runs stretching routines that fix all problems that you say your pain is
  - Fuel for after runs
  - Daily fuel and what to eat
  - How sleep, hydration, and food you have eaten has affected your runs, what to do better
- **Charts and analytics**
  - 
  - Fitness, fatigue, training readiness, and acute training load.
  - Calculation Steps: Power &rarr; HR Zone &rarr; Relative Effort &rarr; Fitness for Today &rarr; Acute Training Load &rarr; Training Readiness
  - Power (Watts)
  - Wattage Output (inputs include: elevation gradient, pace, cadence, stride length):
    - $P_\text{Total} = (E_\text{run} \cdot M \cdot V) + (M \cdot G \cdot H_\text{osc} \cdot F) + (\frac{1}{2} \cdot P \cdot A_{frontal} \cdot C_\text{d} \cdot v^3) + (M \cdot G \cdot v \cdot \sin(\theta))$
    - **BREAKDOWN:**
      - 
      - $\text{Horizontal power}$ $(E_\text{run} \cdot M \cdot V)$
        - $E_\text{run}$ is the energy cost per unit distance per mass $\text{J/kg/m}$
        - Typical value is $\text{1.036J/kg/m}$ (equivalent to $\text{~1 kcal/kg/m}$)
        - $M$ is runner mass (in $kg$)
        - $V$ is velocity $(m/s)$
          - $V$ is the time of one mile in seconds
          - $V$ = $1609/360 = 4.47 \text{ m/s (6 minute mile)}$
            - $360$ seconds is a $\text{6 minute mile}$
      - $\text{Vertical Power Component}$ $(M \cdot G \cdot H_\text{osc} \cdot F)$
        - $M$ is the runner mass in $kg$
        - $G$ is the acceleration due to gravity $(9.81 \text{ }m/s^2)$
        - $H_\text{osc}$ is vertical oscillation per stride $(meters)$
          - Typically $0.05-0.12$ $m$
          - Measured using wearables like GPS watches
        - $F$ is cadence (or steps per second)
          - $\text{F} = \frac{v \cdot k}{\text{stride length}}$
          - Where $k=2$ (account for both legs)
          - Stride length can be estimated as height $(meters) \cdot 1.14$
          - Example for a runner who is $1.75$ meters tall, running at $4.47$ $m/s$: (and stride length is $1.995$)
          - $F = \frac{4.47 \cdot 2}{1.995} = 4.48 \text{ steps/sec (~268 steps/min)}$
        - Air resistance power component $(\frac{1}{2} \cdot P \cdot A_\text{frontal} \cdot C_d \cdot v^3)$
          - $P$ is air density ($1.225\text{ }kg/m^3$ at sea level)
        - $A_\text{frontal}$ is the $frontal$ area of the runner (in square meters)
          - Typical value is $~0.5m^2$
        - $C_d$ is coefficient drag (unitless)
          - ~1.0 typical for runners wearing tight clothing
        - $V^3$ is the velocity term raised to the third power ($m/s^3$)
          - Already calculated in the horizontal power component
        - Incline/Decline power component $(M \cdot G \cdot V \cdot \sin(\theta))$
          - $M$ is the runner mass in kg
          - $G$ is the acceleration due to gravity
          - $V$ is the runner's velocity in meters per second
          - $\sin(\theta)$ is the sine of the inclination angle $\theta$.
            - For a given gradient $(\text{\% slope})$: $\sin(\theta)$ $=$ $gradient$ $\frac{\%}{100}$
            - $5\%$ incline would be $\sin(\theta)$ = $\frac{5}{100}$ $=$ $0.05$

  - **Relative Effort**
    - 
    - $\text{RE} = {\frac{\text{P} \cdot \text{D}}{W} \cdot \frac{1}{t} + \left(1 + \frac{\text{Elevation gain}}{D}\right) \cdot \text{HR Average}}$
      - P = Power in watts (see above)
      - W = weight in kg
      - D = Distance in km
      - T = time (seconds)
      - $\text{1}+\frac{\text{elevation gain}}{D}$ = adjustment for terrain gradients
      - HRavg = Average HR (% of maximum)

  - **Fitness**
    - 
    - **$ATL$ MEANS FATIGUE, $CTL$ MEANS FITNESS**
      - $ATL$: Acute Training Load (Fatigue, Training Load)
      - $CTL$: Chronic Training Load (Fitness)
    - Long term fitness
    - Calculated on a scale from 1-200
    - RUN THROUGH EVERY RUN WHEN NEW IS ADDED (42 DAYS)
    - $\text{CTL} = \sum_{i=1}^{N}{\left(\text{RE Activity}_{i} \cdot e^{-\frac{\Delta t_i}{T_{fit}}} \right)}$
      - $CTL$ = fitness
      - $\text{RE Activity}_\text{i}$ is the relative effort (RE Activity) of the  day $i$ workout.
      - $\Delta t_i$ is the number of days since the $i$-th workout was performed. (Example: If it was 2 days ago, it would be $-\frac{2}{42}$)
      - $T_{fit}$ is the time constant for fitness (e.g., 42 days).
      - $\sum_{i=1}^{N}$ Where $N$ = Number of days that activities that have been completed (e.g., if you have done runs for 5 days N = 5) and where $i$ is the indexing day (e.g., $i$ is 1, so RE Activty of day 1, changes to 2 next itteration, so $i$ of RE Activity of day 2 and so on)
  - **Exponential Weighting for recent fatigue**
    - 
    - RUN THROUGH EVERY RUN WHEN NEW IS ADDED (7 DAYS)
    - $\text{ATL} = \frac{{\sum_{i=1}^{N}\left(\text{RE Activity}_{i} \cdot e^ {-\frac{\Delta t_i}{T_{fat}}} \right)}}{\text{Time Period}}$
      - $\text{ATL}$ = fatigue
      - ${T_{fat}}$ = Time constant for fatigue (7 days)
      - Works the same as $CTL$ (Look above)
      - $\text{Time Period}$ = Whatever is specified. 7 days for week, 1 day for recent activities, and 14-30 days for 2 weeks, month, etc
  - **Fitness relative to Fatigue**
    - 
    - CALCULATE WHEN CTL AND ATL ARE UPDATED
    - $\text{Form (TSB)} = CTL - ATL$
      - Positive TSB means well rested and ready to preform
      - Negative TSB means fatigue is grater than fitness and could mean injury or strain (need rest to prevent injury)
  - **Min and Max formulas**
    - 
    - **CTL**
      - $\frac{\text{CTL} - CTL_\text{min}}{ CTL_\text{max} - CTL_\text{min}} \cdot 100$
      - $CTL_\text{min}$ = 0
      - $CTL_\text{max}$ = 200
      - $CTL$ = Current
    - **ATL**
      - $\frac{\text{ATL} - ATL_\text{min}}{ ATL_\text{max} - ATL_\text{min} } \cdot 100$
      - $ATL_\text{min}$ = 0
      - $ATL_\text{max}$ = 100
      - $ATL$ = Current


## Endpoints

route('/')
- render index.html

route('/connect-garmin' [POST, GET])
- Connect to garmin connect API through API login
- Receive regreshing data from their garmin account

route('/fetch-activities' [GET])
- Load all activities onto index.html

route('/fetch-activities/<int:activity_id>' [GET])
- Open an activity and get all stats 
- redirect to activity.html

route('/fetch-activities/<int:activity_id>/map' [GET])
- Render whole map
- activity_map.html

route('/fetch-activities/<int:activity_id>/rtsai/<int:ai_query>' [POST, GET])
- redirect to activity_ai.html
- ai query:
    - 001: Overall such as irregulatrities, changes, progressions, elevation, and anything else (based on water intake, sleep, all that affected w/o)
    - 002: Pace overlook such as pace changes, random sprints, irregulatrities, elevation to pace changes
    - 003: Heart rate overlook such as high spurts, hill to heart rate, zone time, kind of work based on hr zones
    - 004: Cadence overlook on how hills and downhills affected and how steps correlate to pace, heartrate, and more, random spurts too
    - 005: Power in wattage outputs such as how your power changed based on hr, pace, and elevation, irregulatrities
    - 006: elevation changes on everything, how it compares to avereges, what to do better next time
    - 107: injury prevention, how what you did could have stressed current injuries and how it could have led to more
    - 108: What to roll and what to stretch if something hurts after workout
    - 209: How to fuel after workout to intake good ammounts
    - 210: Meal planning for post workout and rest of day 
    - 311: Based on todays work load, what tomorrow will be

route('/fetch-activities/<int:activity_id>/edit' [PUT, GET])
- Redirect to activity_edit.html
- Edit the following:
    - Title
    - Description
    - Map visibiity
    - Map Type
    - Pace Vis
    - HR Vis
    - Power vis
    - Elevation vis
    - Nutrition vis
    - AI vis
    - How did it feel (scale 1/10) intesnity
    - How did you feel? (1/5 bad to good)
    - Sores, aches, and pains
    - Allow AI to read data from this activity
    - Vis to world
      - Followers
      - Everyone
      - Private
    - Allow comments?
- IF GPS ERROR DETECTED or IF BYPASSED QUESTION: Are you sure you want to edit the {watch brand} stats of this activity? This can seriously affect your RTSAI personilization, especially if you have done something you actually did not. This can lead to catosrophic results. Only do this if YOU ARE ABSOLUTELY SURE something is wrong with distance, time, pace, cadence, heart rate, elevation, and/or power. [COMMIT, BACK TO SAFTEY]
  - Edit Distance
  - Time
  - Pace
  - Cadence
  - HR
  - Elevation
  - Power

route('/fetch-activities/<int:activity_id>/map/<int:route_id>' [GET, POST])
- redirect to: activity_map.html
- POST method:
  - If saving route
  - Downloading route
- GET method:
  - Veiwing route
  - Leaderboards
  - Segments

route('/social/<int:activity_id>/view' [POST])
- NO RENDER
- Adds a view onto an activity if someone enganges (sits on it) for longer than 5 seconds OR opens activity

route('/social/<int:activity_id>/like' [POST])
- NO RENDER
- Adds a like to the post (shows that you liked it)
  - eg. You and 5 others liked "Long Run"
    - Shows users that did it
    - And their pfp

route('/social/<int:activity_id>/remove_like' [DELETE])
- RELOAD RENDER
- Removes like from activity_id

route('/fetch-activities/<int:activity_id>/comment' [GET])
- Render template: activity_comments.html
- Opens comment section and displays all comments
- has text box too

route('/social/<int:activity_id>/post_comment' [POST])
- RELOAD PAGE
- Posts comment as your name, timestamp, details, and likeable

route('/social/<int:activity_id>/<int:comment_id>/like_comment' [POST])
- NO RENDER
- Adds a like (from you) onto comment posted by someone on an activity
- eg you and 5 others liked "comment"

route('/social/<int:activity_id>/<int:comment_id>/remove_like_comment' [DELETE])
- NO RENDER
- Removes the like you posted on a comment

route('/social/<int:activity_id>/<int:comment_id>/<int:my_post?>/edit_comment' [PUT, DELETE])
- Reload: activity_comments.html
- PUT:
  - Edits the comment and you can change info you want, then resubmit followed by reload
- DELETE:
  - Deletes the comment, followed by a reload to display changes

route('/rtsai/<int:user_id>' [GET])
- RENDER: rts_ai.html
  - FETCH daily breifing
  - FETCH recommended workout for the day
  - FETCH Runwear 
  - Show options to enter daily brefing, recomended workouts, runwear, pathfinder. Show previews of everything, EX:
    - Daily Brefing: You had good sleep tonight, so you can do ____. (Learn More)
    - Recommended Workouts: Based on your good sleep last night, your ready for a tempo. (Open Workout)
    - Run Wear: Today will be hot near the afternoon and cold in the mornings. (What to Wear based on Times)
    - Pathfinder: {Display 2 maps, one visible one in a carusel slider. 1st one is planned map for todays workout, and 2nd is recently created route.}(Plan your route)