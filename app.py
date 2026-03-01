import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import itertools
import time
import random
import json
from datetime import date, datetime, time, timedelta
import google.generativeai as genai
import base64
import plotly.graph_objects as go
import plotly.express as px
import numpy as np # Just ensuring you have this imported!
import math
import requests




# ==========================================
# 🔐 SECURE LOGIN GATEKEEPER
# ==========================================
def check_password():
    def password_entered():
        # Your specified password
        if st.session_state["password"] == "0010":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Full Screen Dark Theme for Login
        st.markdown("""
            <style>
                .stApp { background: #0f172a !important; }
                h1, h3 { color: white !important; -webkit-text-fill-color: white !important; }
                .stInfo { background: rgba(251, 191, 36, 0.1) !important; border: 1px solid #fbbf24 !important; color: #fbbf24 !important; }
            </style>
        """, unsafe_allow_html=True)
        
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            # LOCAL IMAGE CALL
            try:
                st.image("L&T LOGO.webp", width=180)
            except:
                st.warning("⚠️ L&T LOGO.png not found in folder.")
                
            st.title("CreaTech Optimizer")
            st.markdown("### Secure Site Access")
            st.text_input("Enter Credentials", type="password", on_change=password_entered, key="password", placeholder="Access Key")
            st.info("Authorized L&T Personnel Only")
        return False
    elif not st.session_state["password_correct"]:
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.text_input("Enter Credentials", type="password", on_change=password_entered, key="password")
            st.error("Invalid Access Key. Please try again.")
        return False
    return True

# 🟢 MAIN GATE: If password is not correct, stop everything here!
if not check_password():
    st.stop()

    

# ==========================================
# 0. APP CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(page_title="L&T Precast Optimizer", layout="wide", initial_sidebar_state="collapsed")

# GLOBAL CSS: BLUR BACKGROUND ONLY, KEEP FOREGROUND SHARP
st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none; }
        h1 a, h2 a, h3 a, h4 a, h5 a, h6 a, a.header-anchor { display: none !important; }
        
        /* BACKGROUND BLUR CONTROL - Change 10px to your preference */
        .stApp::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image: var(--bg-image);
            background-size: cover;
            background-position: center;
            filter: blur(10px); 
            -webkit-filter: blur(2px);
            transform: scale(1.1);
            z-index: -1;
        }

        .stApp { background-color: rgba(0,0,0,0.6); }

        /* FIXED GLOBAL LOGO POSITIONING WITH TEXT-FADE SAFE ZONE */
        .logo-container {
            position: fixed;
            top: 0;           /* Start from the absolute top edge */
            left: 0;
            width: 100%;      /* Stretch across the entire screen */
            height: 150px;    /* The height of the hidden protective zone */
            
            /* The magic: A smooth fade from solid dark background to transparent */
            background: linear-gradient(to bottom, rgba(15, 15, 15, 1) 55%, rgba(15, 15, 15, 0) 100%);
            
            z-index: 10000;   /* Stay above all scrolling text */
            pointer-events: none; /* Ensures the invisible gradient doesn't block mouse clicks */
            
            /* Pushes the actual logo down to the correct spot inside the gradient */
            padding-top: 65px; 
            padding-left: 30px; 
        }
        .logo-img {
            width: 200px;    /* Wider width for the horizontal logo format */
            height: auto;    /* Maintain aspect ratio */
            /* Adds a subtle shadow so the white text pops against any background */
            filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.6));
        }

        /* Keep all foreground content sharp */
        .main .block-container { 
            position: relative; 
            z-index: 1; 
            padding-top: 2rem; /* Give space for the logo */
        }
        /* 🍏 APPLE-STYLE GLASSMORPHISM CARDS */
        .mode-card {
            background: rgba(255, 255, 255, 0.05); /* Faint translucent layer */
            backdrop-filter: blur(16px);           /* Frosted glass effect */
            -webkit-backdrop-filter: blur(16px);   /* Safari support */
            border: 1px solid rgba(255, 255, 255, 0.15); /* Glossy reflective edge */
            border-radius: 24px;                   /* Heavy round curves */
            padding: 40px 20px;
            text-align: center;                    /* Centers the text */
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); /* Deep shadow for depth */
            margin-bottom: 20px;
        }
        .mode-card h3 { 
            color: white; 
            margin-bottom: 10px; 
            font-weight: 600;
        }
        .mode-card p { 
            color: #d1d1d1; 
            font-size: 1.1rem;
        }
    </style>
""", unsafe_allow_html=True)

if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'home'

GEMINI_API_KEY = "AIzaSyBFKCF-ERrrLliCr7f947JA9eA-Djcvf0Q"

# --- HELPER: CONVERT IMAGES TO BASE64 ---
def get_base64_of_bin_file(bin_file):
    """Reads a binary file and returns base64 encoded string."""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

# --- HELPER: SET BACKGROUND (SHARP FOREGROUND) ---
def set_bg_image(image_file):
    try:
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            :root {{
                --bg-image: url("data:image/jpeg;base64,{encoded_string}");
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        pass

# ==========================================
# 1. CORE ENGINE & MODELS
# ==========================================
STATE_MONTHLY_TEMPS = {
    "Delhi": {1: 14.0, 2: 18.0, 3: 24.0, 4: 30.0, 5: 34.0, 6: 34.0, 7: 31.0, 8: 30.0, 9: 29.0, 10: 26.0, 11: 20.0, 12: 15.0},
    "Maharashtra": {1: 24.0, 2: 25.0, 3: 27.0, 4: 29.0, 5: 30.0, 6: 29.0, 7: 27.0, 8: 27.0, 9: 27.0, 10: 28.0, 11: 27.0, 12: 25.0},
    "Karnataka": {1: 22.0, 2: 24.0, 3: 27.0, 4: 28.0, 5: 27.0, 6: 24.0, 7: 23.0, 8: 23.0, 9: 23.0, 10: 23.0, 11: 22.0, 12: 21.0},
    "Tamil Nadu": {1: 25.0, 2: 26.0, 3: 28.0, 4: 31.0, 5: 33.0, 6: 32.0, 7: 30.0, 8: 30.0, 9: 29.0, 10: 28.0, 11: 26.0, 12: 25.0},
    "Gujarat": {1: 20.0, 2: 23.0, 3: 28.0, 4: 32.0, 5: 34.0, 6: 33.0, 7: 30.0, 8: 29.0, 9: 29.0, 10: 28.0, 11: 25.0, 12: 21.0},
    "Rajasthan": {1: 15.0, 2: 18.0, 3: 24.0, 4: 30.0, 5: 34.0, 6: 34.0, 7: 30.0, 8: 29.0, 9: 28.0, 10: 26.0, 11: 21.0, 12: 16.0},
    "Uttar Pradesh": {1: 15.0, 2: 19.0, 3: 25.0, 4: 31.0, 5: 34.0, 6: 33.0, 7: 30.0, 8: 29.0, 9: 29.0, 10: 26.0, 11: 21.0, 12: 16.0},
    "West Bengal": {1: 20.0, 2: 23.0, 3: 28.0, 4: 30.0, 5: 31.0, 6: 30.0, 7: 29.0, 8: 29.0, 9: 29.0, 10: 28.0, 11: 24.0, 12: 20.0},
    "Kerala": {1: 27.0, 2: 28.0, 3: 29.0, 4: 29.0, 5: 28.0, 6: 27.0, 7: 26.0, 8: 26.0, 9: 27.0, 10: 27.0, 11: 27.0, 12: 27.0}
}
# --- NEW: HARDCODED HUMIDITY FALLBACKS ---
HARDCODED_HUMIDITY = {
    "Delhi": 65.0, "Maharashtra": 85.0, "Karnataka": 60.0,
    "Tamil Nadu": 75.0, "Gujarat": 55.0, "Rajasthan": 40.0,
    "Uttar Pradesh": 60.0, "West Bengal": 80.0, "Kerala": 85.0
}

def get_smart_weather(city_name, month_num):
    """
    Attempts to fetch live weather using the free Open-Meteo API. 
    Falls back to hardcoded dictionaries if API fails.
    """
    # A simple dictionary to map city names to coordinates for the free API
    city_coords = {
        "Delhi": (28.61, 77.23), "Maharashtra": (19.07, 72.87), # Mumbai coords
        "Karnataka": (12.97, 77.59), "Tamil Nadu": (13.08, 80.27),
        "Gujarat": (23.02, 72.57), "Rajasthan": (26.91, 75.78),
        "Uttar Pradesh": (26.84, 80.94), "West Bengal": (22.57, 88.36),
        "Kerala": (8.52, 76.93)
    }
    
    try:
        if city_name in city_coords:
            lat, lon = city_coords[city_name]
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
            
            # Increased timeout to 8 seconds to ensure it fetches the real data
            response = requests.get(url, timeout=8) 
            response.raise_for_status()
            data = response.json()
            
            fetched_temp = data['current']['temperature_2m']
            fetched_humidity = data['current']['relative_humidity_2m']
            return fetched_temp, fetched_humidity, "Live API 📡"
        else:
            raise ValueError(f"City {city_name} coordinates not found.")

    except Exception as e:
        print(f"API Fetch Failed: {e}") # This will show in your terminal if it fails
        # FAILSAFE TRIGGERED
        temp = STATE_MONTHLY_TEMPS.get(city_name, {}).get(month_num, 30.0)
        humidity = HARDCODED_HUMIDITY.get(city_name, 60.0)
        return temp, humidity, "Failsafe Data 🗄️"
    
CEMENT_GRADES = {"M30": 30, "M40": 40, "M50": 50}
CURING_TYPES = {"Natural": {"k_factor": 1.0, "energy_cost_per_m3": 50}, "Steam": {"k_factor": 1.5, "energy_cost_per_m3": 400}}
AUTOMATION_LEVELS = {
    "Manual": {"prep_time": 4, "reset_time": 3, "worker_wage": 500, "workers_per_10m3": 5, "equip_rate": 1000},
    "Semi-Automated": {"prep_time": 2, "reset_time": 1.5, "worker_wage": 800, "workers_per_10m3": 2, "equip_rate": 3000},
    "Fully Automated": {"prep_time": 1, "reset_time": 0.5, "worker_wage": 1200, "workers_per_10m3": 1, "equip_rate": 6000}
}
# NEW: Chemical Admixtures and Project Types
ADMIXTURES = {"None": {"cost_per_m3": 0, "speed_multiplier": 1.0}, "Accelerator": {"cost_per_m3": 250, "speed_multiplier": 1.35}}
PROJECT_TYPES = {"Building (Slab/Wall)": {"complexity_multiplier": 1.0}, "Infrastructure (Girder/Pier)": {"complexity_multiplier": 1.5}}

# UPDATED: Now receives admix_speed
def calculate_strength(t_days, S28, Temp, k_curing, admix_speed):
    a, b, k = 4.0, 0.85, 0.015
    base = S28 * ((t_days * admix_speed) / (a + b * (t_days * admix_speed)))
    correction = 1 + k * (Temp - 20) * k_curing
    return min(base * correction, S28 * 1.1)

# UPDATED: Now receives exact target_mpa from sidebar
def run_simulation(volume, temp, target_mpa_req, project_type="Building (Slab/Wall)"):
    results = []
    comp_mult = PROJECT_TYPES[project_type]["complexity_multiplier"]
    
    for cement, curing, auto, admix in itertools.product(CEMENT_GRADES.keys(), CURING_TYPES.keys(), AUTOMATION_LEVELS.keys(), ADMIXTURES.keys()):
        S28 = CEMENT_GRADES[cement]
        k_cur = CURING_TYPES[curing]["k_factor"]
        admix_speed = ADMIXTURES[admix]["speed_multiplier"]
        
        target_mpa = target_mpa_req # Uses exact MPa from sidebar!
        c_days = 28.0
        for t in np.arange(0.1, 28.0, 0.1):
            if calculate_strength(t, S28, temp, k_cur, admix_speed) >= target_mpa:
                c_days = round(t, 1)
                break
                
        # 🟢 FIX: Scale physical labor time based on concrete volume (Base = 25 m³)
        volume_multiplier = max(1.0, volume / 25.0) 
        
        scaled_prep = AUTOMATION_LEVELS[auto]["prep_time"] * volume_multiplier
        scaled_reset = AUTOMATION_LEVELS[auto]["reset_time"] * volume_multiplier
        
        # 🟢 THE FIX: Convert 'c_days' to hours for the AI Optimizer!
        hrs = scaled_prep + (c_days * 24.0) + scaled_reset
        mat_cost = volume * (4000 + (S28-30)*50 + ADMIXTURES[admix]["cost_per_m3"])
        eng_cost = volume * CURING_TYPES[curing]["energy_cost_per_m3"]
        shifts = max(1, hrs / 8)
        
        # 🟢 FIX: Applying the new Headcount Math to the Top Row Optimizer
        crew_size = max(1, math.ceil((volume / 10.0) * AUTOMATION_LEVELS[auto]["workers_per_10m3"]))
        current_labor_rate = crew_size * AUTOMATION_LEVELS[auto]["worker_wage"]
        current_equip_rate = AUTOMATION_LEVELS[auto]["equip_rate"]
        
        # 🟢 FIX: Add the Steel Rebar cost to the top row so it perfectly matches the dashboard
        steel_cost = volume * 100 * 60 
        mat_cost = mat_cost + steel_cost 
        
        cost = mat_cost + eng_cost + (shifts * (current_labor_rate + current_equip_rate))
        results.append({"Cement Grade": cement, "Curing Type": curing, "Admixture": admix, "Automation": auto, "Target Strength (MPa)": target_mpa, "Curing Time (Days)": c_days, "Cycle Time (Hours)": hrs, "Total Cost": cost})
    return pd.DataFrame(results)

# UPDATED: AI now extracts the Project Type
def extract_parameters_with_ai(prompt_text):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    current_month_num = date.today().month
    current_month_name = date.today().strftime("%B")
    
    system_instruction = f"""
    You are an AI parameter extractor for L&T. Extract variables into a strict JSON object. 
    RULES:
    1. 'location' MUST be mapped to: "Delhi", "Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Rajasthan", "Uttar Pradesh", "West Bengal", "Kerala".
    2. 'start_month' MUST be an integer. Current month is {current_month_name} ({current_month_num}).
    3. 'project_type' MUST be exactly "Building (Slab/Wall)" OR "Infrastructure (Girder/Pier)". Look for clues in the text.
    
    JSON Format:
    {{
        "length": float, "width": float, "height": float, "location": "string", 
        "start_month": int, "target_strength_perc": int, 
        "objective": "Must be exactly 'Minimize Cost', 'Minimize Time', or 'Balanced'", 
        "project_type": "string", "assumptions_made": "string"
    }}
    """
    response = model.generate_content(system_instruction + "\n\nUser Input: " + prompt_text)
    
    res_text = response.text.strip()
    if "```json" in res_text: res_text = res_text.split("```json")[1].split("```")[0].strip()
    elif "```" in res_text: res_text = res_text.split("```")[1].split("```")[0].strip()
    return json.loads(res_text)

# ==========================================
# 2. UI & ROUTING
# ==========================================
def set_mode(m): st.session_state.app_mode = m

def render_dashboard(df, temp, humidity, curing_mode, obj, target_mpa, automation_mode, actual_volume, start_date, pour_time, anomaly_delay):
    
    # 1. Map "Standard" to "Natural" so it matches the data correctly
    curing_filter = "Natural" if curing_mode == "Standard" else "Steam"
    
    # 2. FILTER THE DATAFRAME based on your sidebar rules BEFORE finding the best
    df_filtered = df[df['Curing Type'] == curing_filter]
    
    if automation_mode != "Auto-Optimize":
        df_filtered = df_filtered[df_filtered['Automation'] == automation_mode]
        
    # Fallback just in case
    if df_filtered.empty:
        df_filtered = df 
        
    # 3. NOW find the optimal strategy from the remaining options
    if obj == "Minimize Cost":
        best_idx = df_filtered['Total Cost'].idxmin()
    elif obj == "Minimize Time":
        best_idx = df_filtered['Cycle Time (Hours)'].idxmin()
    else: # Balanced Optimization
        norm_cost = df_filtered['Total Cost'] / df_filtered['Total Cost'].max()
        norm_time = df_filtered['Cycle Time (Hours)'] / df_filtered['Cycle Time (Hours)'].max()
        best_idx = (norm_cost + norm_time).idxmin()
        
    best = df_filtered.loc[best_idx]
    
    st.markdown("<div style='background-color: rgba(10,10,10,0.9); padding:30px; border-radius:15px; border: 1px solid #444;'>", unsafe_allow_html=True)
    # ... KEEP EVERYTHING ELSE THE SAME BELOW THIS ...
    st.header(f"Optimal Strategy: {obj}", anchor=False)
    
    # ROW 1: The Engineering Parameters (Expanded)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cement Grade", best["Cement Grade"])
    m2.metric("Admixture", best["Admixture"])
    m3.metric("Curing Type", best["Curing Type"])
    m4.metric("Automation", best["Automation"])
    
    st.divider()
    
    # ROW 2: The Project Outcomes
    # ==========================================
    # 🧠 CALL THE AI LOGIC ENGINE
    # ==========================================
    # ⚠️ IMPORTANT: Ensure 'temp', 'humidity', and 'curing_mode' match your actual Streamlit input variables from the sidebar!
    # ==========================================
    # 🌤️ LIVE WEATHER CONTEXT BANNER
    # ==========================================
    st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 12px 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <span style="color: rgba(255,255,255,0.7); font-size: 0.95rem;"><b>Site Conditions Detected:</b></span>
            <span style="color: #3498db; font-weight: 600; font-size: 1.1rem;">🌡️ {temp}°C</span>
            <span style="color: #3498db; font-weight: 600; font-size: 1.1rem;">💧 {humidity}% RH</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 🟢 REAL MATH: Feeding the true volume into the dashboard
    results = run_precast_simulation(temp, humidity, target_mpa, best, actual_volume)
    
   # ==========================================
    # 🟢 FORWARD-FLOW SCHEDULING LOGIC
    # ==========================================
    # 1. ANCHOR: Setup starts on the Project Start Date at 08:00 AM
    prep_start = datetime.combine(start_date, time(8, 0))
    
    # 2. Add the Anomaly Delay directly to the start (e.g., site mobilization delay)
    prep_start = prep_start + timedelta(hours=anomaly_delay)
    
    # 3. CALCULATE PROGRESSION
    # Rebar starts after 50% of the Prep time is finished
    rebar_start = prep_start + timedelta(hours=results['adj_prep'] * 0.5) 
    
    # Pour happens after Setup + Rebar are 100% complete
    actual_pour_datetime = prep_start + timedelta(hours=results['adj_prep'])
    
    # Demould happens after the chemical clock hits the target
    demould_datetime = actual_pour_datetime + timedelta(hours=results['hours_to_demould'])
    
    # Reset happens after stripping the mould
    reset_complete = demould_datetime + timedelta(hours=results['adj_reset'])
    
    # Format strings for the top metrics
    demould_str = demould_datetime.strftime("%d %b, %I:%M %p")
    
    # 🟢 NEW: Constructing the dynamic Tooltip strings
    cycle_time_help = f"""
    **⚙️ CYCLE TIME CALCULATION**
    
    **Unit Values:**
    • Curing Time (AI Physics): {results['hours_to_demould']} hrs
    • Setup & Reset (Labor): {results['taxed_manual_total']:.1f} hrs
    • Heat Fatigue Penalty: {results['fatigue_loss']} hrs
    
    **Formula:**
    Total Time = Labor Hours + Curing Hours
    
    **Procedure:**
    The AI extracts base labor times for **{best['Automation']}**, applies a 6% efficiency penalty per degree over 27°C (Heat Tax), and adds the exact hour the chemical curve hits **{target_mpa} MPa**.
    """
    
    cost_help = f"""
    **💰 TOTAL EST. COST CALCULATION**
    
    **Unit Values (Per m³):**
    • Material (Cement+Admix): ₹{results['breakdown']['mat_cost']:,.0f}
    • Energy ({best['Curing Type']}): ₹{results['breakdown']['eng_cost']:,.0f}
    • Operations: ₹{results['breakdown']['labor_rate'] + results['breakdown']['equip_rate']:,.0f} / shift
    
    **Formula:**
    Cost = Material + Energy + (Shifts × Ops Rate)
    
    **Procedure:**
    The AI aggregates raw material base costs, adds the steam boiler premium (if active), calculates the required labor shifts ({results['breakdown']['shifts']:.1f} shifts), and applies the hourly burn rate for **{best['Automation']}** systems.
    """
    
    # ==========================================
    # 🏆 ROW 1: THE RESEARCH-BACKED KPIs
    # ==========================================
    r1, r2, r3, r4 = st.columns(4)
    
   # ==========================================
    # 📋 THE DYNAMIC SHIFT SCHEDULER (FLUSH LEFT)
    # ==========================================
    delay_warning = f"<span style='color: #ff4b4b; font-weight: bold;'>⚠️ SCHEDULE ADJUSTED: +{anomaly_delay} Hr Anomaly Logged</span><br>" if anomaly_delay > 0 else ""
    
    # ⚠️ IMPORTANT: Do not indent the HTML lines below! 
    st.markdown(f"""
<div style="background: rgba(15, 20, 30, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 20px; margin-top: 25px; margin-bottom: 25px;">
<h4 style="color: #3498db; margin-top: 0; font-size: 1.1rem; letter-spacing: 1px;">📋 LIVE SHIFT TIMETABLE</h4>
<p style="font-size: 0.9rem; color: #a0a0a0; margin-bottom: 15px;">{delay_warning}Automatically recalculated based on heat tax and chemical curing rates.</p>
<div style="border-left: 2px solid #3498db; padding-left: 15px; margin-left: 10px;">
<p style="color: #e0e0e0; margin: 8px 0;"><b>{prep_start.strftime('%d %b, %I:%M %p')}</b> &nbsp;—&nbsp; 👷‍♂️ Start Mould Setup & Oiling</p>
<p style="color: #e0e0e0; margin: 8px 0;"><b>{rebar_start.strftime('%d %b, %I:%M %p')}</b> &nbsp;—&nbsp; 🔗 Start Rebar Tying</p>
<p style="color: #2ecc71; font-weight: bold; font-size: 1.05rem; margin: 12px 0;"><b>{actual_pour_datetime.strftime('%d %b, %I:%M %p')}</b> &nbsp;—&nbsp; 🚛 CONCRETE POUR (AI Predicted)</p>
<p style="color: #e0e0e0; margin: 8px 0;"><b>{demould_datetime.strftime('%d %b, %I:%M %p')}</b> &nbsp;—&nbsp; 🏗️ Target {target_mpa} MPa Hit! Strip Mould.</p>
<p style="color: #e0e0e0; margin: 8px 0;"><b>{reset_complete.strftime('%d %b, %I:%M %p')}</b> &nbsp;—&nbsp; ✨ Mould Cleaned & Ready for Next Batch</p>
</div>
</div>
""", unsafe_allow_html=True)
    # 🟢 EXACTLY HERE! This forces it to draw the UI.
    
    # 🟢 NEW: Pass the strings into the 'help' parameter!
    r1.metric("⏱️ Cycle Time", f"{results['total_cycle_time']:.1f} hrs", help=cycle_time_help)
    r2.metric("🔄 Capacity", f"{results['pours']} pours/day")
    r3.metric("🌱 Carbon Footprint", f"{results['carbon']} kgCO₂e")
    r4.metric("💰 Total Est. Cost", f"₹ {results['cost']:,.0f}", help=cost_help)
    
    # ==========================================
    # 🍒 THE CHERRY ON TOP: IMPACT & MONSOON BANNER
    # ==========================================
    if results['time_saved'] > 0:
        roi_text = f"Accelerates standard 24h baseline by <b style='color: #2ecc71;'>{results['time_saved']} hours</b>."
        border_color = "#2ecc71" # Green
    else:
        roi_text = f"Extends baseline by <b style='color: #ff4b4b;'>{abs(results['time_saved'])} hours</b> due to environmental heat/humidity tax."
        border_color = "#ff4b4b" # Red
        
    st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border-left: 4px solid {border_color}; border-radius: 6px; padding: 16px 20px; margin-top: 15px; margin-bottom: 25px;">
            <p style="margin: 0; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: rgba(255,255,255,0.8); line-height: 1.6;">
                <b style="color: {border_color}; letter-spacing: 1px;">IMPACT ANALYSIS &nbsp;|&nbsp;</b> {roi_text}<br>
                {results['water_warning']}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # ==========================================
    # 🧠 THE AI "THOUGHT PROCESS" CONSOLE
    # ==========================================
    # Generate dynamic expert commentary based on the temperature
    if temp > 27.0:
        insight_title = "THERMODYNAMICS vs. HUMAN FATIGUE"
        
        # The AI's internal dialogue
        insight_text = f"""
        <b>The Novice Assumption:</b> At {temp}°C, concrete hydration accelerates significantly, suggesting a massive drop in overall cycle time.<br><br>
        <b>The Veteran Reality:</b> While the chemical clock is faster, human labor efficiency drops by 6% for every degree over 27°C. The AI calculated that the crew lost <b><span style='color:#ff4b4b;'>{results['fatigue_loss']} hours</span></b> strictly due to heat fatigue during Setup, Rebar, and Reset phases.<br><br>
        <b>AI Strategic Verdict:</b> The thermodynamic gains are being cannibalized by manual labor limits. 
        """
        
        # Dynamic Recommendation based on severity
        if results['fatigue_loss'] >= 2.0:
            insight_text += "🔴 <b>CRITICAL:</b> Heat tax exceeds 2 hours. The AI strongly recommends switching to <b>Semi-Automated or Fully Automated</b> systems for this batch. The machine rental premium is mathematically offset by recovering the lost fatigue hours."
            glow_color = "rgba(255, 75, 75, 0.4)" # Red glow for high alert
            border_color = "#ff4b4b"
        else:
            insight_text += "🟡 <b>WARNING:</b> Heat tax is active but manageable. Maintain manual labor, but enforce hydration breaks. Automation switch not yet cost-justified."
            glow_color = "rgba(255, 235, 59, 0.3)" # Yellow glow
            border_color = "#ffeb3b"
            
    else:
        insight_title = "OPTIMAL CLIMATE CONDITIONS"
        insight_text = f"Ambient temperature ({temp}°C) is within optimal limits (≤27°C). No human fatigue tax applied. Manual labor remains the most cost-effective strategy for Setup and Rebar operations."
        glow_color = "rgba(46, 204, 113, 0.2)"
        border_color = "#2ecc71"

    # Render the sleek console box
    st.markdown(f"""
        <div style="
            background: rgba(10, 15, 25, 0.8); 
            border: 1px solid {border_color}; 
            border-left: 6px solid {border_color};
            box-shadow: 0 0 15px {glow_color};
            border-radius: 8px; 
            padding: 20px; 
            margin-bottom: 30px;">
            <h4 style="color: {border_color}; margin-top: 0; font-size: 1.1rem; letter-spacing: 1px;">
                <span style="font-size: 1.3rem;">🧠</span> AI DECISION LOG: {insight_title}
            </h4>
            <p style="color: #e0e0e0; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0;">
                {insight_text}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # ==========================================
    # 🔬 THE CHEMICAL & DURABILITY PARADOX LOG
    # ==========================================
    durability_alerts = []

    # 1. Thermal Cracking Paradox (Triggers if very hot)
    if temp >= 35.0:
        durability_alerts.append(
            "<b>🔥 Thermal Cracking Risk:</b> Extreme heat accelerates early demoulding but causes microscopic thermal cracking, permanently reducing the ultimate 28-day lifespan.<br>"
            "👉 <span style='color:#ffeb3b;'><b>AI VERDICT:</b></span> Capped early maturity curve and recommending a 20% Fly Ash substitution to lower internal heat of hydration."
        )

    # 2. Steam Boiler Paradox (Triggers if using steam on a hot day)
    if temp >= 30.0 and curing_mode == 'Steam':
        durability_alerts.append(
            "<b>💨 Diminishing Returns Trap:</b> Ambient heat already maximizes the safe chemical clock; adding steam saves barely 1 hour while spiking carbon and energy costs by over 400%.<br>"
            "👉 <span style='color:#ffeb3b;'><b>AI VERDICT:</b></span> Recommending immediate deactivation of Steam Boilers to prevent severe ROI degradation."
        )

    # 3. Monsoon Porosity Paradox (Triggers if very humid)
    if humidity > 80.0:
        durability_alerts.append(
            "<b>💧 Monsoon Porosity Trap:</b> Saturated yard aggregates secretly hold water; standard batch water pushes the W/C ratio past 0.45, creating fatally porous and weak concrete.<br>"
            "👉 <span style='color:#ffeb3b;'><b>AI VERDICT:</b></span> Added batch water mechanically reduced by 8% to offset surface moisture and guarantee the demoulding safety threshold."
        )


    # CHARTS (Cleaned up the duplicate columns line)
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("Cost Breakdown (25 m³ Batch)", anchor=False)
        
        # 🟢 THE FIX: Pull the real dynamic values from the AI breakdown!
        b = results['breakdown']
        total_labor = b['labor_rate'] * b['shifts']
        total_equip = b['equip_rate'] * b['shifts']
        
        labels = ["Material", "Energy", "Labour", "Equip"]
        cost_values = [b['mat_cost'], b['eng_cost'], total_labor, total_equip]
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels, 
            values=cost_values, 
            hole=0.4, 
            textinfo='label+value+percent',
            texttemplate='<b>%{label}</b><br>₹%{value:,.0f}<br>(%{percent})', 
            textposition='outside',
            marker=dict(colors=['#6675ff', '#ff5c33', '#00cc96', '#b870ff'])
        )])
        
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            font_color="white"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with colB:
        st.subheader("Strength Projection", anchor=False)
        
        y_strength = results['curve']
        x_hours = np.arange(1, len(y_strength) + 1)
        
        fig_line = px.line(
            x=x_hours, 
            y=y_strength,
            labels={'x': 'Curing Time (Hours)', 'y': 'Compressive Strength (MPa)'},
            template="plotly_dark"
        )
        
        # 🟢 THE FIX: Green line now uses the target_mpa variable from the sidebar!
        fig_line.add_hline(
            y=target_mpa, 
            line_dash="dash", 
            line_color="#2ecc71", 
            annotation_text=f"Demoulding Target ({target_mpa} MPa)", 
            annotation_position="bottom right",
            annotation_font_color="#2ecc71"
        )
        
        # 🟢 THE FIX: Yellow Pointer now explicitly states the exact intersection!
        demould_hour = results['hours_to_demould']
        fig_line.add_annotation(
            x=demould_hour, 
            y=target_mpa, 
            text=f"<b>Target hit at {demould_hour} hrs!</b><br>Ready to demould.", 
            showarrow=True, 
            arrowhead=2, 
            arrowsize=1.5, 
            arrowcolor="#ffeb3b", 
            ax=-80, 
            ay=-50, 
            font=dict(color="#111", size=11), 
            bgcolor="#ffeb3b", 
            borderpad=4, 
            opacity=0.9
        )
        
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            xaxis=dict(showgrid=False), 
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
        )
        fig_line.update_traces(line_shape='spline', line=dict(color='#6675ff', width=3))
        st.plotly_chart(fig_line, use_container_width=True)
        
        # ==========================================
        # 🔬 THE CHEMICAL & DURABILITY PARADOX LOG
        # ==========================================
        durability_alerts = []
        if temp >= 35.0: durability_alerts.append("<b>🔥 Thermal Cracking Risk:</b> Extreme heat accelerates early demoulding but causes microscopic thermal cracking, permanently reducing ultimate lifespan.<br>👉 <span style='color:#ffeb3b;'><b>AI VERDICT:</b></span> Capped early maturity curve and recommending a 20% Fly Ash substitution.")
        if temp >= 30.0 and curing_mode == 'Steam': durability_alerts.append("<b>💨 Diminishing Returns Trap:</b> Ambient heat already maximizes the safe chemical clock; adding steam saves <1 hour while spiking carbon/costs >400%.<br>👉 <span style='color:#ffeb3b;'><b>AI VERDICT:</b></span> Recommending immediate deactivation of Steam Boilers.")
        if humidity > 80.0: durability_alerts.append("<b>💧 Monsoon Porosity Trap:</b> Saturated yard aggregates secretly hold water; standard batch water pushes W/C ratio past 0.45, creating fatally porous concrete.<br>👉 <span style='color:#ffeb3b;'><b>AI VERDICT:</b></span> Added batch water mechanically reduced by 8% to offset surface moisture.")
        
        if durability_alerts:
            alerts_html = "<hr style='border-color: rgba(255,255,255,0.1); margin: 10px 0;'>".join(durability_alerts)
            st.markdown(f"""
                <div style="background: rgba(25, 10, 10, 0.8); border: 1px solid #ff4b4b; border-left: 4px solid #ff4b4b; box-shadow: 0 0 15px rgba(255, 75, 75, 0.2); border-radius: 8px; padding: 15px; margin-top: 15px;">
                    <h4 style="color: #ff4b4b; margin-top: 0; font-size: 1rem; letter-spacing: 0.5px;"><span style="font-size: 1.1rem;">🔬</span> CHEMICAL ANOMALIES DETECTED</h4>
                    <p style="color: #e0e0e0; font-size: 0.85rem; line-height: 1.5; margin-bottom: 0;">{alerts_html}</p>
                </div>
            """, unsafe_allow_html=True)
            
    # EXPORT FEATURE
    st.divider()
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Full Simulation Report (CSV)", data=csv, file_name="LT_Optimization_Report.csv", mime='text/csv')
    st.markdown("</div>", unsafe_allow_html=True)
    
# ==========================================
# 3. GLOBAL ASSETS (THE LOGO) - PLACED ON EVERY PAGE
# ==========================================
# Using a pure SVG ensures 100% transparency and infinite sharpness
# FIXED: Widened the viewBox to 450 to stop cutting off the text
logo_svg = """
<svg width="350" height="55" viewBox="0 0 450 60" xmlns="http://www.w3.org/2000/svg">
    <g fill="none" stroke="#ffffff" stroke-width="3.5">
        <circle cx="30" cy="30" r="26"/>
        <path d="M 32 14 L 14 40 L 32 40" stroke-linejoin="round" stroke-linecap="round"/>
        <path d="M 22 23 L 46 23 M 38 23 L 25 45" stroke-linejoin="round" stroke-linecap="round"/>
    </g>
    <text x="70" y="42" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-size="28" font-weight="900" font-style="italic" letter-spacing="1.5">LARSEN &amp; TOUBRO</text>
</svg>
"""

# FIXED: Put this entirely on one line so Streamlit doesn't render the </div> as a code block!
st.markdown(f"<div class='logo-container'>{logo_svg}</div>", unsafe_allow_html=True)


#Add the Arrhenius Function

def calculate_arrhenius_strength(time_hrs, ambient_temp, curing_mode, max_strength=40.0):
    """Calculates concrete strength using the Arrhenius Maturity Equation."""
    # 1. Constants from the research
    E_a = 42000.0   # Activation Energy (J/mol)
    R = 8.314       # Universal Gas Constant
    T_r = 293.15    # Reference Temp (20°C) in Kelvin
    
    # 2. Temperature Input (Tc) = Ambient + Hydration (assumed 5°C) + Steam Boost
    steam_boost = 20.0 if curing_mode == 'Steam' else 0.0
    t_c_kelvin = (ambient_temp + 5.0 + steam_boost) + 273.15
    
    # 3. Calculate the Arrhenius exponential factor
    arrhenius_factor = math.exp((-E_a / R) * ((1 / t_c_kelvin) - (1 / T_r)))
    
    # 4. Calculate Equivalent Age (t_eq)
    t_eq = time_hrs * arrhenius_factor
    
    # 5. Convert t_eq to Strength (MPa) using the Hyperbolic Model
    strength_mpa = max_strength * (t_eq / (t_eq + 15.0))
    
    return strength_mpa


# UPDATED: Now dynamically scales based on massive concrete volumes
def calculate_heat_tax_durations(ambient_temp, automation_level, volume):
    # 🟢 THE FIX: Apply the Volume Multiplier (Base = 25 m³)
    volume_multiplier = max(1.0, volume / 25.0) 
    
    base_prep = AUTOMATION_LEVELS[automation_level]["prep_time"] * volume_multiplier
    base_reset = AUTOMATION_LEVELS[automation_level]["reset_time"] * volume_multiplier
    base_total = base_prep + base_reset
    
    heat_tax_multiplier = 1.0
    if ambient_temp > 27.0: 
        heat_tax_multiplier += (0.06 * (ambient_temp - 27.0))
        
    adj_prep = round(base_prep * heat_tax_multiplier, 2)
    adj_reset = round(base_reset * heat_tax_multiplier, 2)
    
    return adj_prep, adj_reset, base_total

#Add the Monsoon Buffer Function
def calculate_monsoon_impact(humidity):
    """
    Checks if monsoon conditions (>80% RH) are active.
    Returns a curing speed multiplier and a batch water warning string.
    """
    is_raining = humidity > 80.0
    
    # If humidity is >80%, the curing speed drops to 90% efficiency (a 10% time penalty)
    curing_speed_multiplier = 0.90 if is_raining else 1.0
    
    # The exact warning message for the engineers on the dashboard
    if is_raining:
        water_warning = "⚠️ MONSOON ALERT: Reduce Added Batch Water by 5-8% to compensate for aggregate surface moisture."
    else:
        water_warning = "✅ Standard W/C ratio maintained."
        
    return curing_speed_multiplier, water_warning

# UPDATED: Calculates True Total Cost and cleanly extracts rates for the tooltip
def calculate_dynamic_cost_and_carbon(cycle_hrs, cement_grade, admixture, curing_type, automation_level, volume):
    S28 = CEMENT_GRADES[cement_grade]
    
   # 🟢 FIX: ADDING STRUCTURAL STEEL (REBAR)
    # Standard precast requires ~100kg of steel per cubic meter. Steel costs ~₹60/kg.
    steel_cost = volume * 100 * 60 
    
    # 1. Material Cost (Concrete + Chemical + Steel)
    concrete_cost = volume * (4000 + (S28-30)*50 + ADMIXTURES[admixture]["cost_per_m3"])
    mat_cost = concrete_cost + steel_cost
    
    # 2. Energy Cost (Steam vs Natural)
    eng_cost = volume * CURING_TYPES[curing_type]["energy_cost_per_m3"]
    
    # 🟢 FIX: THE HEADCOUNT MULTIPLIER
    # Calculate how many workers are needed based on the physical volume of the pour
    crew_size = max(1, math.ceil((volume / 10.0) * AUTOMATION_LEVELS[automation_level]["workers_per_10m3"]))
    
    # Total labor rate is now the wage multiplied by the massive crew size
    current_labor_rate = crew_size * AUTOMATION_LEVELS[automation_level]["worker_wage"]
    current_equip_rate = AUTOMATION_LEVELS[automation_level]["equip_rate"]
    
    # 3. Labor & Equipment Cost (Based on Shifts calculated from AI cycle time)
    shifts = max(1, cycle_hrs / 8)
    labor_equip_cost = shifts * (current_labor_rate + current_equip_rate)
    
    total_cost = mat_cost + eng_cost + labor_equip_cost
    
    # Dynamic Carbon (Higher cement grade = more carbon. Steam = massive carbon penalty)
    base_carbon = 300 + ((S28-30) * 2)
    if curing_type == "Steam": base_carbon += 50
    total_carbon = round(volume * base_carbon, 2)
    
    time_saved = round(24.0 - cycle_hrs, 2)
    pours = round(24.0 / cycle_hrs, 2) if cycle_hrs > 0 else 0.0
    
    # 🟢 FIX: Safely pass those extracted rates into the UI breakdown
    breakdown = {
        "mat_cost": mat_cost,
        "eng_cost": eng_cost,
        "labor_rate": current_labor_rate,
        "equip_rate": current_equip_rate,
        "shifts": shifts
    }
    
    return time_saved, pours, total_carbon, total_cost, breakdown

# UPDATED: Now accepts cement, admixture, and automation from the dashboard
def run_precast_simulation(ambient_temp, humidity, target_strength, best_strategy_dict, volume):
    curing_mode = best_strategy_dict["Curing Type"]
    automation_level = best_strategy_dict["Automation"]
    cement_grade = best_strategy_dict["Cement Grade"]
    admixture = best_strategy_dict["Admixture"]
    
    curing_speed_multiplier, water_warning = calculate_monsoon_impact(humidity)
    
   # Use real automation times
    # 🟢 THE FIX: Pass the physical volume to the Heat Tax engine so it can scale!
    adj_prep, adj_reset, base_manual_total = calculate_heat_tax_durations(ambient_temp, automation_level, volume)
    taxed_manual_total = adj_prep + adj_reset
    fatigue_hours_lost = round(taxed_manual_total - base_manual_total, 2)
    
    hours_to_demould = 0
    strength_curve = []
    
    # 🟢 NEW: Admixtures and Cement Grades now physically alter the Arrhenius graph!
    admix_speed = ADMIXTURES[admixture]["speed_multiplier"]
    max_strength_potential = float(CEMENT_GRADES[cement_grade]) * 1.1 
    
    for hour in range(1, 73):
        raw_strength = calculate_arrhenius_strength(hour, ambient_temp, curing_mode, max_strength=max_strength_potential)
        actual_strength = raw_strength * curing_speed_multiplier * admix_speed 
        strength_curve.append(actual_strength)
        
        if actual_strength >= target_strength and hours_to_demould == 0:
            hours_to_demould = hour
            
    if hours_to_demould == 0: hours_to_demould = 72
    total_cycle_time_hrs = taxed_manual_total + hours_to_demould
    
    # 🟢 REAL MATH: Passing the exact geometric volume to the cost engine
    time_saved, pours, carbon, cost, breakdown = calculate_dynamic_cost_and_carbon(total_cycle_time_hrs, cement_grade, admixture, curing_mode, automation_level, volume)
    
    # 🟢 NEW: Pass 'taxed_manual_total' and 'breakdown' to the frontend!
    return {
        "total_cycle_time": total_cycle_time_hrs, 
        "hours_to_demould": hours_to_demould, 
        "curve": strength_curve, 
        "water_warning": water_warning, 
        "time_saved": time_saved, 
        "pours": pours, 
        "carbon": carbon, 
        "cost": cost, 
        "fatigue_loss": fatigue_hours_lost,
        "taxed_manual_total": taxed_manual_total, 
        "adj_prep": adj_prep,   # 🟢 NEW: Sent to the Scheduler
        "adj_reset": adj_reset, # 🟢 NEW: Sent to the Scheduler
        "breakdown": breakdown 
    }


# --- HOME ---
if st.session_state.app_mode == 'home':
    set_bg_image('image_1.jpeg')
    
    # 🍏 MAXIMUM OVERRIDE CSS FOR GLASS CARDS
    st.markdown("""
        <style>
        /* 1. Target the button's core attribute to bypass Streamlit's solid grey theme */
        div[data-testid="stButton"] button,
        button[kind="secondary"] {
            background: rgba(255, 255, 255, 0.05) !important; 
            backdrop-filter: blur(16px) !important;           
            -webkit-backdrop-filter: blur(16px) !important;   
            border: 1px solid rgba(255, 255, 255, 0.15) !important; 
            border-radius: 24px !important;                   
            height: 220px !important; 
            width: 100% !important;   
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4) !important; 
            transition: all 0.3s ease !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
        }
        
        /* 2. Transparent Fade on Hover */
        div[data-testid="stButton"] button:hover,
        button[kind="secondary"]:hover {
            opacity: 0.6 !important;
            transform: none !important; 
            border-color: rgba(255, 255, 255, 0.05) !important; 
            background: rgba(255, 255, 255, 0.02) !important;
            color: white !important;
        }
        
        /* 3. The Text inside the button */
        div[data-testid="stButton"] button p,
        button[kind="secondary"] p {
            white-space: pre-line !important; 
            text-align: center !important;
            font-size: 1.1rem !important;     
            font-weight: 400 !important;
            color: rgba(255, 255, 255, 0.7) !important; 
            line-height: 2.0 !important;
            margin: 0 !important; /* Strips any hidden margins Streamlit adds */
        }
        
        /* 4. MAGIC HACK: Turn the first line into the Title */
        div[data-testid="stButton"] button p::first-line,
        button[kind="secondary"] p::first-line {
            font-size: 2.2rem !important; 
            font-weight: 700 !important;
            color: #ffffff !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Large Catchy Heading
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 5.5rem; color: white; text-shadow: 4px 4px 10px #000;'>Precast Optimizer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.8rem; color: #f0f0f0; text-shadow: 2px 2px 5px #000;'>Building India with AI-Driven Precision</p>", unsafe_allow_html=True)
    
    st.write("<br><br>", unsafe_allow_html=True)
    
    # Layout Columns
    c1, c2, c3, c4 = st.columns([1, 4, 4, 1])
    
    # The pure, native buttons
    with c2:
        st.button("Manual Parameters\n\nFull engineering control.", on_click=set_mode, args=('manual',), use_container_width=True)
    with c3:
        st.button("AI Assistant\n\nNatural language processing.", on_click=set_mode, args=('ai',), use_container_width=True)

# # --- MANUAL ---
elif st.session_state.app_mode == 'manual':
    set_bg_image('image_2.jpeg')
    
    # BULLETPROOF FLOATING CSS (BOTTOM LEFT + GLASSMORPHISM)
    st.markdown("""
        <style>
        /* Positions the button container at the bottom left */
        div.element-container:has(#back-btn-anchor) + div.element-container {
            position: fixed;
            bottom: 30px; /* Shifted to the bottom */
            left: 5px;   /* Anchored to the left */
            z-index: 99999;
            width: auto;
        }
        /* Applies the Apple Glassmorphism effect to the button (SMALLER SIZE) */
        div.element-container:has(#back-btn-anchor) + div.element-container button {
            background: rgba(255, 255, 255, 0.05) !important; 
            backdrop-filter: blur(16px) !important;           
            -webkit-backdrop-filter: blur(16px) !important;   
            border: 1px solid rgba(255, 255, 255, 0.15) !important; 
            box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.3) !important; /* Softer shadow */
            border-radius: 10px !important; /* Tighter curves for a smaller button */
            color: white !important;
            font-size: 0.85rem !important;  /* Smaller, sleeker text */
            font-weight: 500 !important;
            padding: 6px 16px !important;   /* Tighter padding reduces overall bulk */
            min-height: 0 !important;       /* Overrides Streamlit's default bulky height */
            height: auto !important;
            transition: all 0.3s ease !important;
        }
        /* Hover effect - Fades into transparency without lifting */
        div.element-container:has(#back-btn-anchor) + div.element-container button:hover {
            opacity: 0.5 !important;         /* Makes the entire button 50% transparent */
            transform: none !important;      /* Forces the button to stay perfectly still */
            border-color: rgba(255, 255, 255, 0.1) !important; /* Softens the border instead of turning it red */
            background: rgba(255, 255, 255, 0.02) !important;  /* Drops the background frost effect slightly */
        }
        </style>
    """, unsafe_allow_html=True)
    
 # The invisible anchor
    st.markdown('<div id="back-btn-anchor"></div>', unsafe_allow_html=True)
    # The button that will float
    st.button("Back", on_click=set_mode, args=('home',))
    
    st.markdown("<br><h1 style='text-shadow: 2px 2px 4px #000;'>Manual Entry</h1>", unsafe_allow_html=True)
    
    # START OF THE INPUT BOX CONTAINER
    with st.container():
        st.markdown("<div style='background-color:rgba(20,20,20,0.85); padding:30px; border-radius:15px;'>", unsafe_allow_html=True)
        
        # 1. DEFINE THE COLUMNS
        c1, c2, c3 = st.columns(3)
        
        # 2. REAL DIMENSION INPUTS
        with c1:
            loc = st.selectbox("Location", list(STATE_MONTHLY_TEMPS.keys()))
            start_date = st.date_input("Project Start Date", date.today())
        with c2:
            proj_type = st.selectbox("Project Type", list(PROJECT_TYPES.keys()))
            batch_qty = st.number_input("Elements per Batch", min_value=1, value=10, step=1)
        with c3:
            l = st.number_input("Length (m)", 5.0)
            w = st.number_input("Width (m)", 1.2)
            h = st.number_input("Height/Thickness (m)", 0.2)
            
        # 🟢 CALCULATE EXACT GEOMETRIC VOLUME
        actual_volume = l * w * h * batch_qty
            
        # 4. GOAL SELECTOR (Spans neatly below the columns)
        st.write("<br>", unsafe_allow_html=True)
        obj = st.radio("Optimization Goal", ["Minimize Cost", "Minimize Time", "Balanced"], horizontal=True)
            
        # 5. THE SIMULATE BUTTON
        st.write("<br>", unsafe_allow_html=True) 
        # 5. THE SIMULATE BUTTON & SESSION MEMORY
        st.write("<br>", unsafe_allow_html=True) 
        if st.button("Simulate", type="primary", use_container_width=True):
            st.session_state.manual_sim_active = True
            
        if st.session_state.get('manual_sim_active', False):
            month_num = start_date.month
            
            # Fetch intelligent weather
            actual_temp, actual_humidity, source = get_smart_weather(loc, month_num)
            
            # Live Sidebar Controls
            st.sidebar.markdown("### Live Environment Controls")
            st.sidebar.caption(f"Weather Data: **{source}**")
            
            # 🟢 NEW: The Anomaly Feeder!
            start_date = date.today()
            pour_time = st.sidebar.time_input("Scheduled Pour Time", time(16, 0))
            anomaly_delay = st.sidebar.number_input("🚧 Log Delay/Anomaly (Hrs)", min_value=0.0, max_value=24.0, value=0.0, step=0.5, help="E.g., RMC Truck is late by 2 hours.")
            
            target_mpa = st.sidebar.number_input("Target Demoulding Strength (MPa)", min_value=5.0, max_value=40.0, value=15.0, step=1.0)
            # ... (keep the rest of your sidebar code) ...
            curing_mode = st.sidebar.selectbox("Curing Strategy", ["Standard", "Steam"])
            automation_mode = st.sidebar.selectbox("Automation Level", ["Auto-Optimize", "Manual", "Semi-Automated", "Fully Automated"])
            
            # 🟢 CALCULATE EXACT GEOMETRIC VOLUME
            actual_volume = l * w * h * batch_qty
            
            # 🟢 EXACT PLACEMENT: The updated simulation and dashboard calls go right here at the end!
            df = run_simulation(actual_volume, actual_temp, target_mpa, proj_type)
            # 🟢 THE FIX: Passing all 11 arguments down the chain!
            render_dashboard(df, actual_temp, actual_humidity, curing_mode, obj, target_mpa, automation_mode, actual_volume, start_date, pour_time, anomaly_delay)
            
        # CLOSE THE INPUT BOX CONTAINER
        st.markdown("</div>", unsafe_allow_html=True)
# --- AI ---
elif st.session_state.app_mode == 'ai':
    set_bg_image('image_3.jpeg')
    
    # BULLETPROOF FLOATING CSS (BOTTOM LEFT + GLASSMORPHISM)
    st.markdown("""
        <style>
        /* Positions the button container at the bottom left */
        div.element-container:has(#back-btn-anchor) + div.element-container {
            position: fixed;
            bottom: 30px; /* Shifted to the bottom */
            left: 5px;   /* Anchored to the left */
            z-index: 99999;
            width: auto;
        }
        /* Applies the Apple Glassmorphism effect to the button (SMALLER SIZE) */
        div.element-container:has(#back-btn-anchor) + div.element-container button {
            background: rgba(255, 255, 255, 0.05) !important; 
            backdrop-filter: blur(16px) !important;           
            -webkit-backdrop-filter: blur(16px) !important;   
            border: 1px solid rgba(255, 255, 255, 0.15) !important; 
            box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.3) !important; /* Softer shadow */
            border-radius: 10px !important; /* Tighter curves for a smaller button */
            color: white !important;
            font-size: 0.85rem !important;  /* Smaller, sleeker text */
            font-weight: 500 !important;
            padding: 6px 16px !important;   /* Tighter padding reduces overall bulk */
            min-height: 0 !important;       /* Overrides Streamlit's default bulky height */
            height: auto !important;
            transition: all 0.3s ease !important;
        }
        /* Hover effect - Fades into transparency without lifting */
        div.element-container:has(#back-btn-anchor) + div.element-container button:hover {
            opacity: 0.5 !important;         /* Makes the entire button 50% transparent */
            transform: none !important;      /* Forces the button to stay perfectly still */
            border-color: rgba(255, 255, 255, 0.1) !important; /* Softens the border instead of turning it red */
            background: rgba(255, 255, 255, 0.02) !important;  /* Drops the background frost effect slightly */
        }
        </style>
    """, unsafe_allow_html=True)
    
    # The invisible anchor
    st.markdown('<div id="back-btn-anchor"></div>', unsafe_allow_html=True)
    # The button that will float
    st.button("Back", on_click=set_mode, args=('home',))
    
    st.markdown("<br><h1 style='color: white; text-shadow: 2px 2px 4px #000;'>AI✨ Project Assistant</h1>", unsafe_allow_html=True)
    
    # WRAPPER FOR READABILITY
    st.markdown("<div style='background-color: rgba(25, 25, 25, 0.9); padding: 40px; border-radius: 20px; border: 1px solid #444;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: white; margin-top: 0;'>Describe your project site:</h3>", unsafe_allow_html=True)
    
    prompt = st.text_area("", height=200, placeholder="E.g. Cast a 10m beam near Badarpur border next month...", label_visibility="collapsed")
    
    if st.button("Simulate via AI✨", type="primary", use_container_width=True):
        if prompt:
            with st.spinner("AI analyzing project matrix..."):
                st.session_state.ai_sim_active = True
                st.session_state.ai_data = extract_parameters_with_ai(prompt)
                
        if st.session_state.get('ai_sim_active', False):
            data = st.session_state.ai_data
            extracted_type = data.get("project_type", "Building (Slab/Wall)")
            
            # Fetch intelligent weather using AI's extracted location
            actual_temp, actual_humidity, source = get_smart_weather(data["location"], data["start_month"])
            
            # Live Sidebar Controls
            st.sidebar.markdown("### Live Environment Controls")
            st.sidebar.caption(f"Weather Data: **{source}**")
            
            # 🟢 NEW: The Anomaly Feeder!
            start_date = date.today()
            pour_time = st.sidebar.time_input("Scheduled Pour Time", time(16, 0))
            anomaly_delay = st.sidebar.number_input("🚧 Log Delay/Anomaly (Hrs)", min_value=0.0, max_value=24.0, value=0.0, step=0.5, help="E.g., RMC Truck is late by 2 hours.")
            
            target_mpa = st.sidebar.number_input("Target Demoulding Strength (MPa)", min_value=5.0, max_value=40.0, value=15.0, step=1.0)
            # ... (keep the rest of your sidebar code) ...
            # 🟢 THE FIX: Safely extract the AI's target, default to 15.0 if missing, and cap it at 40 max
            ai_target = float(data.get("target_strength_perc", 15.0))
            ai_target = max(5.0, min(40.0, ai_target)) # Prevents crashes if AI hallucinates 1000 MPa
            
            # Now the sidebar uses the AI's target as its default value!
            target_mpa = st.sidebar.number_input("Target Demoulding Strength (MPa)", min_value=5.0, max_value=40.0, value=ai_target, step=1.0)
            
            curing_mode = st.sidebar.selectbox("Curing Strategy", ["Standard", "Steam"])
            automation_mode = st.sidebar.selectbox("Automation Level", ["Auto-Optimize", "Manual", "Semi-Automated", "Fully Automated"])
            
            # 🟢 NEW: Ask the user how many elements they are casting based on the AI's dimensions!
            batch_qty = st.sidebar.number_input("Batch Quantity (Units)", min_value=1, value=10, step=1)
            
            # 🟢 CALCULATE EXACT GEOMETRIC VOLUME
            actual_volume = data["length"] * data["width"] * data["height"] * batch_qty
            
            df = run_simulation(actual_volume, actual_temp, target_mpa, extracted_type)
            
            # 🟢 EXACT PLACEMENT: Passing actual_volume as the 8th argument!
            # 🟢 THE FIX: Passing all 11 arguments for the AI mode too!
            render_dashboard(df, actual_temp, actual_humidity, curing_mode, data["objective"], target_mpa, automation_mode, actual_volume, start_date, pour_time, anomaly_delay)
            
        st.markdown("</div>", unsafe_allow_html=True)
