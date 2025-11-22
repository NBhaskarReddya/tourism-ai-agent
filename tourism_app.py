import streamlit as st
import requests

# --- CONFIGURATION ---
HEADERS = {
    'User-Agent': 'StudentAIProject/1.0 (contact@example.com)' 
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
        response = requests.get(url, params=params, headers=HEADERS)
        data = response.json()
        
        if data:
            # Nominatim returns a 'boundingbox' list: [minLat, maxLat, minLon, maxLon]
            # This represents the exact square area of the city/state on the map.
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
        print(e)
        return None

# --- 2. WEATHER AGENT ---
def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {'latitude': lat, 'longitude': lon, 'current_weather': 'true'}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if 'current_weather' in data:
            return f"{data['current_weather']['temperature']}°C"
        return "N/A"
    except:
        return "Unavailable"

# --- 3. PLACES AGENT (SMART BOUNDARY SEARCH) ---
def get_places(bbox):
    url = "https://overpass-api.de/api/interpreter"
    
    # Extract boundaries from Nominatim format
    # Nominatim gives: [minLat (South), maxLat (North), minLon (West), maxLon (East)]
    south = bbox[0]
    north = bbox[1]
    west = bbox[2]
    east = bbox[3]
    
    # OVERPASS QUERY EXPLAINED:
    # 1. [timeout:25] -> Don't wait too long.
    # 2. nwr[...] -> Search Nodes, Ways (Buildings), and Relations (Parks).
    # 3. RegEx Filter (~"...") -> Search for 'attraction', 'museum', 'zoo', 'viewpoint', etc.
    # 4. (south, west, north, east) -> Search strictly INSIDE the official boundaries.
    # 5. out center 5 -> Return the center point of the top 5 results.
    
    query = f"""
    [out:json][timeout:25];
    nwr["tourism"~"attraction|museum|zoo|theme_park|viewpoint|aquarium|artwork|gallery"]({south},{west},{north},{east});
    out center 5;
    """
    
    try:
        response = requests.get(url, params={'data': query})
        data = response.json()
        
        places = []
        if 'elements' in data:
            for item in data['elements']:
                # Some items (like parks) have tags inside the main object, others in 'tags'
                tags = item.get('tags', {})
                name = tags.get('name')
                
                if name:
                    places.append(name)
        
        # Return unique top 5
        return list(set(places))[:5]
    except Exception as e:
        print(e)
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
            
            # 1. Get Location & Boundaries
            loc_data = get_location_data(city)
            
            if not loc_data:
                st.error(f"🚫 I couldn't locate '{city}'.")
            else:
                st.success(f"📍 **Location Found:** {loc_data['name']}")
                
                # 2. Fetch Weather & Places
                # Notice we pass 'bbox' (Boundaries) to get_places, not just a point!
                weather = get_weather(loc_data['lat'], loc_data['lon'])
                places = get_places(loc_data['bbox'])
                
                # 3. Display Results
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("🌡️ Current Weather", weather)
                    # Show the raw coordinates just for info
                    st.caption(f"Lat: {loc_data['lat']}, Lon: {loc_data['lon']}")
                
                with col2:
                    st.subheader("📸 Top Attractions")
                    if places:
                        for place in places:
                            st.write(f"• {place}")
                    else:
                        st.info(f"No major attractions found directly inside the mapped boundaries of {city}.")