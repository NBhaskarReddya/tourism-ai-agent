import streamlit as st
import requests

# --- CONFIGURATION ---
HEADERS = {
    'User-Agent': 'StudentAIProject/1.0 (contact@example.com)'
}

# --- 1. GEOCODING AGENT ---
def get_location_data(place_name):
    # Open-Meteo Geocoding (No API Key, Cloud-Safe)
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        'name': place_name,
        'count': 10,
        'language': 'en',
        'format': 'json'
    }
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=5)
        data = response.json()
        
        if 'results' in data and data['results']:
            # Auto-fix for India locations (Prioritize India over Finland/USA)
            for result in data['results']:
                if result.get('country') == 'India':
                    return {
                        'lat': float(result['latitude']), 
                        'lon': float(result['longitude']), 
                        'name': f"{result['name']}, {result.get('country')}"
                    }
            
            # Default to first result
            result = data['results'][0]
            return {
                'lat': float(result['latitude']), 
                'lon': float(result['longitude']), 
                'name': f"{result['name']}, {result.get('country')}"
            }
        return None
    except:
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

# --- 3. PLACES AGENT (STRICT FILTERS) ---
def get_places(lat, lon):
    url = "https://overpass-api.de/api/interpreter"
    
    # IMPROVEMENT: 
    # 1. Search Radius increased to 30km (30000m) to find big landmarks.
    # 2. We search for specific "Major" tags: Museums, Zoos, Castles, Forts.
    # 3. We explicitly require the ["name"] tag to avoid unnamed spots.
    
    query = f"""
    [out:json][timeout:25];
    (
      nwr["tourism"~"museum|zoo|theme_park|aquarium|gallery"](around:30000, {lat}, {lon});
      nwr["historic"~"castle|monument|ruins|fort|memorial"](around:30000, {lat}, {lon});
      nwr["natural"="beach"](around:30000, {lat}, {lon});
    );
    out center 20;
    """
    try:
        response = requests.get(url, params={'data': query}, headers=HEADERS, timeout=15)
        data = response.json()
        places = []
        if 'elements' in data:
            for item in data['elements']:
                tags = item.get('tags', {})
                name = tags.get('name')
                
                # Filter out common noise
                if name and "hotel" not in name.lower() and "guest" not in name.lower():
                    places.append(name)
        
        # Return top 5 unique places
        return list(set(places))[:5]
    except:
        return []

# --- USER INTERFACE ---
st.set_page_config(page_title="Travel AI", page_icon="✈️")

st.title("✈️ AI Tourism Planner")
st.markdown("Enter a city below to find the weather and **major** attractions.")

city = st.text_input("Enter a City:", placeholder="e.g. Munnar, Kochi, Delhi")

if st.button("Plan My Trip", type="primary"):
    if not city:
        st.warning("Please enter a location.")
    else:
        with st.spinner(f"Flying to {city}..."):
            
            loc_data = get_location_data(city)
            
            if not loc_data:
                st.error(f"🚫 I couldn't locate '{city}'.")
            else:
                st.success(f"📍 **Found:** {loc_data['name']}")
                
                weather = get_weather(loc_data['lat'], loc_data['lon'])
                places = get_places(loc_data['lat'], loc_data['lon'])
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("🌡️ Current Weather", weather)
                
                with col2:
                    st.subheader("🏛️ Major Attractions")
                    if places:
                        for place in places:
                            st.write(f"• {place}")
                    else:
                        st.info("No major museums, forts, or famous spots found in this 30km radius.")