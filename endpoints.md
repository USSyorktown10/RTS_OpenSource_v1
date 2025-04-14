### Functions and Endpoints

## Functions
- Home
  - Shows all activities from friends, recommended challenges, targets, and weekly stats
- RTS AI
  - Recommended workout for the day
  - Daily Brefing: can send notification every day at certain time too
    - The weather today, what time you should run at, what to eat, route for the day, workout for the day, and feedback/input on what you want to do
    - IF YOU HAVE A TRAINING PLAN:
      - What todays run will be, what time you should do it at, what to wear (run wear)
  - Find me routes for this workout (RTS Pathfunder)
    - Maps, routes, workout so that GAP=Target pace
  - Run wear - gives you clothes to use during runs that allow mobility but keep you warm/cool
  - Training Plans
    - Start
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
        - STEPS:
          - 1. Calculate Target page (TP)
            - TP = $\frac{g}{d}$ also shown as: (G/D) goal time for race/distance
              - Results in required pace in minutes per mile
          - 2. Calculate Improvement needed (I)
            - I = T - TP 
            - This calculates the difference between fastest mile and target pace
    - View Current
- Injury Prevention and Nutrition
  - Log for injuries
  - AI runs stretching routines that fix all problems that you say your pain is
  - Fuel for after runs
  - Daily fuel and what to eat
  - How sleep, hydration, and food you have eaten has affected your runs, what to do better
- 

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

route('/)