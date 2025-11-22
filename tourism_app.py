import streamlit as st
import requests
import time

# --- CONFIGURATION ---
HEADERS = {
    'User-Agent': 'StudentAIProject/1.0 (contact@example.com)'
}

# --- 1. GEOCODING AGENT (NEW: Uses Open-Meteo) ---
def get_location_data(place_name):
    # We switched to Open-Meteo Geocoding because it doesn't block Streamlit Cloud
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        'name': place_name,
        'count': 1,
        'language': 'en',
        'format': 'json'
    }
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=5)
        data = response.json()
        
        if 'results' in data and data['results']:
            result = data['results'][0]
            lat = result['latitude']
            lon = result['longitude']
            name = result['name']
            country = result.get('country', '')
            
            return {
                'lat': float(lat), 
                'lon': float(lon), 
                'name': f"{name}, {country}"
            }
        return None
    except Exception as e:
        st.error(f"⚠️ Geocoding Error: {e}")
        return None

# --- 2. WEATHER AGENT ---
def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {'latitude': lat, 'longitude': lon, 'current_weather': 'true'}
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if 'current_weather' in data:
            return f"{data['current_weather']['temperature']}°C"
        return "N/A"
    except:
        return "Unavailable"

# --- 3. PLACES AGENT (RADIUS SEARCH) ---
def get_places(lat, lon):
    url = "https://overpass-api.de/api/interpreter"
    
    # Since we don't have a bounding box anymore, we search in a 10km radius (10000m)
    # We explicitly search for tourism types to filter out noise
    query = f"""
    [out:json][timeout:25];
    nwr["tourism"~"attraction|museum|zoo|theme_park|viewpoint|aquarium|artwork|gallery"](around:10000, {lat}, {lon});
    out center 5;
    """
    
    try:
        response = requests.get(url, params={'data': query}, headers=HEADERS, timeout=15)
        data = response.json()
        
        places = []
        if 'elements' in data:
            for item in data['elements']:
                tags = item.get('tags', {})
                name = tags.get('name')
                if name:
                    places.append(name)
        
        return list(set(places))[:5]
    except Exception as e:
        return []

# --- USER INTERFACE ---
st.set_page_config(page_title="Smart Travel AI", page_icon="🗺️")

st.title("🗺️ Reliable Travel AI")
st.markdown("Enter a city below to find the weather and top 5 attractions.")

city = st.text_input("Enter a City:", placeholder="e.g., Kerala, Delhi, Tokyo")

if st.button("Plan My Trip", type="primary"):
    if not city:
        st.warning("Please enter a location.")
    else:
        with st.spinner(f"Flying to {city}..."):
            
            # 1. Get Location (New API)
            loc_data = get_location_data(city)
            
            if not loc_data:
                st.error(f"🚫 I couldn't locate '{city}'. Please check spelling.")
            else:
                st.success(f"📍 **Found:** {loc_data['name']}")
                
                # 2. Fetch Weather & Places
                weather = get_weather(loc_data['lat'], loc_data['lon'])
                places = get_places(loc_data['lat'], loc_data['lon'])
                
                # 3. Display Results
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("🌡️ Current Weather", weather)
                
                with col2:
                    st.subheader("📸 Top Attractions (10km Radius)")
                    if places:
                        for place in places:
                            st.write(f"• {place}")
                    else:
                        st.info(f"No major attractions found within 10km.")