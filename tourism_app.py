import streamlit as st
import requests
import time

# --- CONFIGURATION ---
# We need a very specific User-Agent to avoid being blocked on Streamlit Cloud
# We also add a Referer to look more like a legitimate web traffic
HEADERS = {
    'User-Agent': 'MyUniqueTourismApp/1.0 (contact@example.com)',
    'Referer': 'https://tourism-agent-app.streamlit.app/' 
}

# --- 1. GEOCODING AGENT (GET BOUNDARIES) ---
def get_location_data(place_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': place_name,
        'format': 'json',
        'limit': 1
    }
    try:
        # Added timeout to prevent hanging
        response = requests.get(url, params=params, headers=HEADERS, timeout=5)
        
        # DEBUG: Check if we are being blocked
        if response.status_code != 200:
            st.error(f"⚠️ API Error: {response.status_code}")
            return None

        data = response.json()
        
        if data:
            bbox = data[0]['boundingbox'] 
            lat = data[0]['lat']
            lon = data[0]['lon']
            display_name = data[0]['display_name']
            
            return {
                'lat': float(lat), 
                'lon': float(lon), 
                'name': display_name, 
                'bbox': bbox 
            }
        return None
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
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

# --- 3. PLACES AGENT (SMART BOUNDARY SEARCH) ---
def get_places(bbox):
    url = "https://overpass-api.de/api/interpreter"
    
    south, north, west, east = bbox[0], bbox[1], bbox[2], bbox[3]
    
    query = f"""
    [out:json][timeout:25];
    nwr["tourism"~"attraction|museum|zoo|theme_park|viewpoint|aquarium|artwork|gallery"]({south},{west},{north},{east});
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

st.title("🗺️ Smart Boundary Travel AI")
st.markdown("This agent adapts its search radius to the **exact size** of the place you enter.")

city = st.text_input("Enter a State, City, or Town:", placeholder="e.g., Kerala, Vatican City, Tokyo")

if st.button("Plan My Trip", type="primary"):
    if not city:
        st.warning("Please enter a location.")
    else:
        with st.spinner(f"Mapping boundaries for {city}..."):
            
            # 1. Get Location
            # Add a small delay to be polite to the API
            time.sleep(0.5)
            loc_data = get_location_data(city)
            
            if not loc_data:
                st.error(f"🚫 I couldn't locate '{city}'. The map service might be busy.")
            else:
                st.success(f"📍 **Location Found:** {loc_data['name']}")
                
                # 2. Fetch Weather & Places
                weather = get_weather(loc_data['lat'], loc_data['lon'])
                places = get_places(loc_data['bbox'])
                
                # 3. Display Results
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("🌡️ Current Weather", weather)
                
                with col2:
                    st.subheader("📸 Top Attractions")
                    if places:
                        for place in places:
                            st.write(f"• {place}")
                    else:
                        st.info(f"No major attractions found directly inside the mapped boundaries.")