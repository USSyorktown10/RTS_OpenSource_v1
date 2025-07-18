# RTS v0.0.0-alpha.3

**Release Date:** July 15, 2025
**Commit:** [`918993f`](https://github.com/USSyorktown10/RTS_OpenSource_v1/commit/918993f7c8ed8ef0a7fa9233b18960ee16a0c810)

---

### New Features

* **User Authentication System**

  * Full implementation of **Signup** and **Login** functionality.
  * Basic account management pipeline in place.

* **Persistent Account Storage**

  * User stats and activities are now saved independently of Strava, ensuring data resilience even during API outages.

* **New Advanced Metrics**
  The platform now provides detailed training insights:

  * **Wattage Output**
  * **Relative Effort**
  * **CTL (Chronic Training Load)**
  * **ATL (Acute Training Load)**
  * **TSB (Training Stress Balance/Fatigue)**
 
  Note: Calculations are still dull and not very accurate currently. We hope to achive more accuracy in v.0.0.0-alpha.4

---

### UI & UX Enhancements

* A new **CSS stylesheet** has been applied to the front-end.

  * Major visual improvements to escape the "gov-site" look.
  * Cleaner profile and activity views.
* Templates updated or added:

  * `login.html`, `signup.html`, `profile.html`, `edit_profile.html`, `activity_details.html`
  * Redesigned `index.html`, `link_to_strava.html`, and `activities.html`

---

### Other Additions

* **Profile Pictures Support**

  * Default and fun preset profile pictures included (`default_pfp.png`, `pfps/*.jpg`)

* **Activity Visuals**

  * New assets like `RTS.png` and `weight_training.png` added for richer context.

* **Utility Modules Added**

  * `utils.py` introduced to support backend logic.
  * `config.yaml` added for configuration management. Enhances privacy and allows users to enter their own Strava API Credentials in.

---

### Test & Docs Updates

* Test file `offline_v2.py` is now unusable because of vars being changed to fit `app.py` under `v.0.0.0-alpha.3`.
* `README.md`, `endpoints.md`, and `version_planning.md` updated to reflect new features.

---

### Developer Notes

If you find a bug, think of a cool stat, or just want to make RTS even better — open an issue and contribute!
