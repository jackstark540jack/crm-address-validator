import re
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components
import requests
import streamlit as st
API_KEY = st.secrets["GOOGLE_API_KEY"]

  # Replace with your actual API key

# -------------------- Helpers --------------------
def extract_info(raw_string):
    match = re.search(r"Selected address: (.*), latitude: ([\d.]+), longitude: ([\d.]+)", raw_string)
    if match:
        address = match.group(1).strip()
        latitude = float(match.group(2))
        longitude = float(match.group(3))
        return address, latitude, longitude
    return None, None, None

def geocode_address(address):
    # Check if API key is properly configured
    if API_KEY == "YOUR_GOOGLE_MAPS_API_KEY" or not API_KEY:
        st.error("🔑 Google Maps API key not configured!")
        st.info("Please replace 'YOUR_GOOGLE_MAPS_API_KEY' with your actual Google Maps API key.")
        st.info("Get your API key from: https://developers.google.com/maps/documentation/geocoding/get-api-key")
        return None, None, None
    
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        if data["status"] == "OK":
            result = data["results"][0]
            formatted_address = result["formatted_address"]
            lat = result["geometry"]["location"]["lat"]
            lng = result["geometry"]["location"]["lng"]
            return formatted_address, lat, lng
        elif data["status"] == "REQUEST_DENIED":
            st.error("🚫 API request denied. Check your API key and billing settings.")
            return None, None, None
        elif data["status"] == "OVER_QUERY_LIMIT":
            st.error("📊 API quota exceeded. Try again later.")
            return None, None, None
        elif data["status"] == "ZERO_RESULTS":
            st.warning("🔍 No results found for this address.")
            return None, None, None
        else:
            st.error(f"❌ Geocoding failed: {data.get('status', 'Unknown error')}")
            return None, None, None
            
    except requests.exceptions.RequestException as e:
        st.error(f"🌐 Network error: {str(e)}")
        return None, None, None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None, None, None

def fallback_geocode(address):
    """Fallback method that doesn't require API key - just formats the address for map display"""
    # Clean and format the address for better display
    cleaned_address = address.strip()
    if cleaned_address:
        return cleaned_address, None, None
    return None, None, None

def embed_map_from_coords(lat, lng):
    return f"https://maps.google.com/maps?q={lat},{lng}&z=15&output=embed"

def embed_map_from_address(address):
    return f"https://maps.google.com/maps?q={urllib.parse.quote(address)}&z=15&output=embed"

def public_link_address(address):
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="CRM Address Validator", page_icon="📍", layout="wide")

st.title("📍 CRM Address Validator with Editable Geocode Lookup")
st.markdown("---")

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'show_edited_map' not in st.session_state:
    st.session_state.show_edited_map = False

# Step 1: Input Section
st.header("🔍 Step 1: Input CRM Address Data")
input_str = st.text_area(
    "Paste your CRM Address Input:",
    placeholder="Example: Selected address: 123 Main St, New York, NY, latitude: 40.7128, longitude: -74.0060",
    height=100
)

# Process Button
if st.button("✅ Extract & Process Address", type="primary"):
    original_address, lat, lng = extract_info(input_str)
    
    if original_address:
        # Store processed data in session state
        st.session_state.processed_data = {
            'original_address': original_address,
            'lat': lat,
            'lng': lng
        }
        st.session_state.show_edited_map = False  # Reset edited map state
        st.success("✅ Address parsed successfully!")
    else:
        st.error("❌ Invalid input format. Please ensure it follows the correct structure.")
        st.info("Expected format: 'Selected address: [address], latitude: [lat], longitude: [lng]'")

# Step 2: Display Results if data is processed
if st.session_state.processed_data:
    data = st.session_state.processed_data
    
    st.markdown("---")
    st.header("📊 Step 2: Extracted Information")
    
    # Display extracted info in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Original Address:** {data['original_address']}")
        st.info(f"**Coordinates:** {data['lat']}, {data['lng']}")
    
    with col2:
        st.info(f"**Latitude:** {data['lat']}")
        st.info(f"**Longitude:** {data['lng']}")
    
    # Show map from original coordinates
    st.subheader("🗺️ Map from Input Coordinates")
    components.iframe(embed_map_from_coords(data['lat'], data['lng']), height=400)
    
    # Step 3: Google Geocoding
    st.markdown("---")
    st.header("🌐 Step 3: Google Maps Geocoding")
    
    # Try geocoding with API first
    formatted_address, geo_lat, geo_lng = geocode_address(data['original_address'])
    
    # If API geocoding fails, offer fallback option
    if not formatted_address:
        st.warning("⚠️ Google Maps API geocoding unavailable.")
        
        # Offer manual address editing as fallback
        use_fallback = st.checkbox("📝 Use manual address editing (no API required)")
        
        if use_fallback:
            fallback_address, _, _ = fallback_geocode(data['original_address'])
            if fallback_address:
                formatted_address = fallback_address
                geo_lat, geo_lng = None, None  # No coordinates from fallback
                st.info("✅ Using fallback mode - you can edit the address manually below.")
    
    if formatted_address:
        if geo_lat and geo_lng:
            st.success("✅ Google Maps successfully geocoded the address!")
        else:
            st.info("📍 Using manual address mode.")
        
        # Create columns for better layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Use the original CRM address instead of Google's formatted address
            edited_address = st.text_input(
                "✏️ Original CRM Address (editable):",
                value=data['original_address'],  # Use original address from CRM
                key="edited_address_input",
                help="This is your original CRM address. Edit it if needed and click 'Update Map' to see the new location"
            )
        
        with col2:
            st.write("")  # Empty space for alignment
            st.write("")  # Empty space for alignment
            if st.button("🔄 Update Map", type="secondary"):
                st.session_state.show_edited_map = True
        
        # Always show the map with current address (either original or edited)
        current_address = st.session_state.get('edited_address_input', data['original_address']) or data['original_address']
        
        st.subheader("🗺️ Google Maps View")
        components.iframe(embed_map_from_address(current_address), height=400)
        
        # Additional info and link
        col1, col2 = st.columns(2)
        with col1:
            if geo_lat and geo_lng:
                st.info(f"**Google Geocoded Coordinates:** {geo_lat}, {geo_lng}")
                st.info(f"**Google Formatted Address:** {formatted_address}")
            else:
                st.info("**Mode:** Manual address editing")
        with col2:
            st.markdown(
                f"🔗 [Open in Google Maps →]({public_link_address(current_address)})",
                unsafe_allow_html=True
            )
        
        # Add API setup instructions if needed
        if not geo_lat:
            with st.expander("🔧 Want precise geocoding? Set up Google Maps API"):
                st.markdown("""
                **To enable precise geocoding:**
                1. Go to [Google Cloud Console](https://console.cloud.google.com/)
                2. Create a new project or select existing one
                3. Enable the Geocoding API
                4. Create credentials (API key)
                5. Replace `YOUR_GOOGLE_MAPS_API_KEY` in the code with your actual API key
                
                **Benefits of using the API:**
                - Get precise latitude/longitude coordinates
                - Validate and format addresses automatically
                - Better address suggestions and corrections
                """)
    else:
        st.warning("⚠️ Could not process the address. Please check the format.")
        st.info("💡 Try using the manual address editing option above.")

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** You can edit the Google Maps address and click 'Update Map' to see the new location without re-processing the original input.")
