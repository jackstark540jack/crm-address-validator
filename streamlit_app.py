import re
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components
import requests
import math
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

API_KEY = st.secrets["GOOGLE_API_KEY"]

# -------------------- Helpers --------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points using the Haversine formula"""
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    return c * r

def format_distance(distance_km):
    """Format distance in a human-readable way"""
    if distance_km < 0.001:
        return f"{distance_km * 1000000:.1f} mm"
    elif distance_km < 1:
        return f"{distance_km * 1000:.1f} m"
    else:
        return f"{distance_km:.2f} km"

def get_accuracy_status(distance_km):
    """Get accuracy status based on distance"""
    if distance_km < 0.01:  # Less than 10 meters
        return "🎯 Excellent", "success"
    elif distance_km < 0.1:  # Less than 100 meters
        return "✅ Good", "success"
    elif distance_km < 1:  # Less than 1 km
        return "⚠️ Fair", "warning"
    else:
        return "❌ Poor", "error"

def extract_info(raw_string):
    # Updated regex to capture the full address including commas until latitude
    match = re.search(r"Selected address: (.*?), latitude: ([\d.-]+), longitude: ([\d.-]+)", raw_string)
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

def embed_map_from_coords(lat, lng):
    return f"https://maps.google.com/maps?q={lat},{lng}&z=15&output=embed"

def embed_map_from_address(address):
    # Clean and properly encode the address for Google Maps
    cleaned_address = address.strip().replace('\n', ' ').replace('\r', ' ')
    # Use more comprehensive URL encoding
    encoded_address = urllib.parse.quote_plus(cleaned_address)
    return f"https://maps.google.com/maps?q={encoded_address}&z=15&output=embed"

def public_link_address(address):
    # Clean and properly encode the address for Google Maps
    cleaned_address = address.strip().replace('\n', ' ').replace('\r', ' ')
    encoded_address = urllib.parse.quote_plus(cleaned_address)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_address}"

# -------------------- Streamlit UI --------------------
st.set_page_config(
    page_title="CRM Address Validator", 
    page_icon="📍", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI with dark theme support
st.markdown("""
<!-- Removing JavaScript that overrides Streamlit's theming -->
<style>
    /* Main header - works in both themes */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Info cards - using default Streamlit theming */
    .info-card {
        border-radius: 10px;
        padding: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Comparison section - adaptive */
    .comparison-section {
        background: var(--background-color, #ffffff);
        border: 1px solid var(--border-color, #e9ecef);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        color: var(--text-color, #333);
    }
    
    .comparison-section h3, .comparison-section h4 {
        color: var(--text-color, #333) !important;
    }
    
    .comparison-section p, .comparison-section li {
        color: var(--text-color, #555) !important;
    }
    
    /* Dark theme support for comparison section */
    [data-theme="dark"] .comparison-section,
    .stApp[data-theme="dark"] .comparison-section {
        background: #262730;
        border: 1px solid #404040;
        color: #fafafa !important;
        box-shadow: 0 2px 8px rgba(255,255,255,0.05);
    }
    
    [data-theme="dark"] .comparison-section h3,
    [data-theme="dark"] .comparison-section h4,
    .stApp[data-theme="dark"] .comparison-section h3,
    .stApp[data-theme="dark"] .comparison-section h4 {
        color: #fafafa !important;
    }
    
    [data-theme="dark"] .comparison-section p,
    [data-theme="dark"] .comparison-section li,
    .stApp[data-theme="dark"] .comparison-section p,
    .stApp[data-theme="dark"] .comparison-section li {
        color: #ccc !important;
    }
    
    /* Footer styling - adaptive */
    .footer-section {
        text-align: center;
        padding: 2rem;
        background: var(--background-color, #f8f9fa);
        border-radius: 10px;
        margin-top: 2rem;
        border: 1px solid var(--border-color, #e9ecef);
        color: var(--text-color, #333);
    }
    
    .footer-section h4 {
        color: var(--text-color, #333) !important;
        margin-bottom: 1rem;
    }
    
    .footer-section p {
        color: var(--text-color, #555) !important;
        margin: 0.5rem 0;
    }
    
    /* Dark theme support for footer */
    [data-theme="dark"] .footer-section,
    .stApp[data-theme="dark"] .footer-section {
        background: #262730;
        border: 1px solid #404040;
        color: #fafafa !important;
    }
    
    [data-theme="dark"] .footer-section h4,
    .stApp[data-theme="dark"] .footer-section h4 {
        color: #fafafa !important;
    }
    
    [data-theme="dark"] .footer-section p,
    .stApp[data-theme="dark"] .footer-section p {
        color: #ccc !important;
    }
    
    /* Enhanced headers for better visibility */
    .section-header {
        color: var(--text-color, #333);
        font-weight: 600;
        margin: 1rem 0;
        padding: 0.5rem 0;
        border-bottom: 2px solid #667eea;
    }
    
    /* Dark theme header support */
    [data-theme="dark"] .section-header,
    .stApp[data-theme="dark"] .section-header {
        color: #fafafa;
        border-bottom: 2px solid #667eea;
    }
    
    /* Map container styling */
    .map-container {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        margin: 0.5rem 0;
    }
    
    /* Enhanced captions */
    .map-caption {
        font-size: 0.9em;
        color: var(--secondary-text-color, #666);
        margin: 0.25rem 0;
        padding: 0.25rem 0.5rem;
        background: var(--caption-bg, rgba(0,0,0,0.05));
        border-radius: 4px;
    }
    
    /* Dark theme caption support */
    [data-theme="dark"] .map-caption,
    .stApp[data-theme="dark"] .map-caption {
        color: #ccc;
        background: rgba(255,255,255,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📍 CRM Address Validator</h1>
    <p>Validate and compare your CRM addresses with Google Maps</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for information and controls
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    **CRM Address Validator** helps you:
    
    ✅ Extract address data from CRM inputs  
    🗺️ Geocode addresses to get Google's coordinates  
    📏 Calculate distance differences  
    📊 Compare input coordinates vs geocoded coordinates  
    """)
    
    st.markdown("---")
    st.markdown("**📊 Session Stats**")
    if 'validation_count' not in st.session_state:
        st.session_state.validation_count = 0
    st.metric("Validations", st.session_state.validation_count)

st.title("📍 CRM Address Validator")
st.markdown("---")

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'show_edited_map' not in st.session_state:
    st.session_state.show_edited_map = False
if 'geocoded_data' not in st.session_state:
    st.session_state.geocoded_data = None
if 'validation_count' not in st.session_state:
    st.session_state.validation_count = 0

# Step 1: Input Section
st.markdown("""
<div class="info-card">
    <h3 class="section-header">🔍 Input CRM Address Data</h3>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    input_str = st.text_area(
        "Paste your CRM Address Input:",
        placeholder="Example: Selected address: 123 Main St, New York, NY, latitude: 40.7128, longitude: -74.0060",
        height=120,
        help="Paste the address data from your CRM system here"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    process_btn = st.button("✅ Extract & Validate", type="primary", use_container_width=True)
    
    if st.button("🧹 Clear All", use_container_width=True):
        for key in ['processed_data', 'geocoded_data', 'show_edited_map']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Process Button Logic
if process_btn and input_str.strip():
    with st.spinner("🔄 Processing address data..."):
        original_address, lat, lng = extract_info(input_str)
        
        if original_address:
            # Store processed data in session state
            st.session_state.processed_data = {
                'original_address': original_address,
                'lat': lat,
                'lng': lng,
                'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.validation_count += 1
            
            # Auto-geocode
            with st.spinner("🌐 Geocoding with Google Maps..."):
                formatted_address, geo_lat, geo_lng = geocode_address(original_address)
                if formatted_address and geo_lat and geo_lng:
                    st.session_state.geocoded_data = {
                        'formatted_address': formatted_address,
                        'lat': geo_lat,
                        'lng': geo_lng
                    }
            
            st.session_state.show_edited_map = False  # Reset edited map state
            st.success("✅ Address parsed successfully!")
        else:
            st.error("❌ Invalid input format. Please ensure it follows the correct structure.")
            st.info("Expected format: 'Selected address: [address], latitude: [lat], longitude: [lng]'")

elif process_btn:
    st.warning("⚠️ Please enter some address data to process.")

# Display Results if data is processed
if st.session_state.processed_data:
    data = st.session_state.processed_data
    
    st.markdown("---")
    st.markdown("""
    <div class="info-card">
        <h3 class="section-header">📊 Extracted Information</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Display extracted info and geocoded comparison at the top
    if st.session_state.geocoded_data:
        geo_data = st.session_state.geocoded_data
        distance = calculate_distance(
            data['lat'], data['lng'],
            geo_data['lat'], geo_data['lng']
        )
        accuracy_status, status_type = get_accuracy_status(distance)
        
        # Show comparison info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔴 Original Coordinates from Input**")
            st.write(f"**Address:** {data['original_address']}")
            st.write(f"**Input Coordinates:** {data['lat']:.6f}, {data['lng']:.6f}")
        
        with col2:
            st.markdown("**🔵 Geocoded Coordinates from Address**")
            st.write(f"**Same Address:** {data['original_address']}")
            st.write(f"**Geocoded Coordinates:** {geo_data['lat']:.6f}, {geo_data['lng']:.6f}")
        
        # Distance info
        st.markdown(f"**Distance Difference:** {format_distance(distance)} | **Accuracy:** {accuracy_status}")
        
        # Manual address editing section
        st.markdown("---")
        st.markdown("""
        <div class="info-card">
            <h3 class="section-header">✏️ Manual Address Editing</h3>
        </div>
        """, unsafe_allow_html=True)
        
        edited_address = st.text_input(
            "Edit the address for Map2 (Address Text Map):",
            value=data['original_address'],
            key="edited_address_input",
            help="Edit the address to update Map2 and see different location"
        )
        
        # Use edited address if available, otherwise use original
        map2_address = edited_address if edited_address.strip() else data['original_address']
        
        # Show two maps side by side
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔴 Map1: Input Coordinates")
            st.markdown(f'<div class="map-caption">Coordinates: {data["lat"]:.6f}, {data["lng"]:.6f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="map-caption">(Shows location from CRM input coordinates)</div>', unsafe_allow_html=True)
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            components.iframe(embed_map_from_coords(data['lat'], data['lng']), height=400)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(
                f"🔗 [Open Input Coordinates in Google Maps](https://www.google.com/maps?q={data['lat']},{data['lng']})"
            )
        
        with col2:
            st.subheader("🔵 Map2: Address Text")
            st.markdown(f'<div class="map-caption">Google\'s coordinates: {geo_data["lat"]:.6f}, {geo_data["lng"]:.6f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="map-caption">Using address: {map2_address}</div>', unsafe_allow_html=True)
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            components.iframe(embed_map_from_address(map2_address), height=400)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(
                f"🔗 [Open Full Address in Google Maps]({public_link_address(map2_address)})"
            )
    
    else:
        # Show original info and single map
        st.write(f"**Address from Input:** {data['original_address']}")
        st.write(f"**Coordinates from Input:** {data['lat']:.6f}, {data['lng']:.6f}")
        
        if st.button("🌐 Geocode Address to Compare", type="primary"):
            with st.spinner("🌐 Geocoding the address to get Google's coordinates..."):
                formatted_address, geo_lat, geo_lng = geocode_address(data['original_address'])
                if formatted_address and geo_lat and geo_lng:
                    st.session_state.geocoded_data = {
                        'formatted_address': formatted_address,
                        'lat': geo_lat,
                        'lng': geo_lng
                    }
                    st.rerun()
        
        st.subheader("🗺️ Map from Input Coordinates")
        st.markdown(f'<div class="map-caption">Using coordinates: {data["lat"]:.6f}, {data["lng"]:.6f}</div>', unsafe_allow_html=True)
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        components.iframe(embed_map_from_coords(data['lat'], data['lng']), height=400)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(
            f"🔗 [Open Input Coordinates in Google Maps](https://www.google.com/maps?q={data['lat']},{data['lng']})"
        )

# API Setup Help Section
if st.session_state.processed_data and not st.session_state.geocoded_data:
    with st.expander("🔧 Want to enable precise geocoding? Set up Google Maps API"):
        st.markdown("""
        ### 🚀 Enable Advanced Features
        
        **What you'll get with Google Maps API:**
        - ✅ Precise latitude/longitude coordinates
        - 📍 Address validation and formatting
        - 📏 Accurate distance calculations
        - 🗺️ Interactive map comparisons
        
        **Setup Steps:**
        1. 🌐 Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. 📁 Create a new project or select existing one
        3. 🔌 Enable the Geocoding API
        4. 🔑 Create credentials (API key)
        5. 🔧 Replace the API key in the code
        
        **Security Note:** For production, use Streamlit secrets to store your API key securely.
        """)

# Footer with enhanced design
st.markdown("---")
st.markdown("""
<div class="footer-section">
    <h4>🚀 CRM Address Validator</h4>
    <p>Built with ❤️ using Streamlit | Enhanced with Google Maps API</p>
    <p>💡 <strong>Pro Tip:</strong> Use the geocoding feature to ensure your CRM addresses are accurate and up-to-date!</p>
</div>
""", unsafe_allow_html=True)

# Show helpful tips in sidebar
with st.sidebar:
    st.markdown("---")
    st.header("💡 Tips & Tricks")
    st.markdown("""
    **🎯 Best Practices:**
    - Validate addresses before storing in CRM
    - Check distances > 100m for accuracy
    - Use interactive maps for visual verification
    - Keep API keys secure in production
    
    **🔍 Understanding Results:**
    - 🎯 Excellent: < 10m difference
    - ✅ Good: < 100m difference  
    - ⚠️ Fair: < 1km difference
    - ❌ Poor: > 1km difference
    """)

# Welcome message when no data is processed
if not st.session_state.processed_data:
    st.markdown("""
    <div class="comparison-section">
        <h3>👋 Welcome to CRM Address Validator!</h3>
        <p>Get started by pasting your CRM address data in the text area above.</p>
        
        <h4>✨ What this tool does:</h4>
        <ul>
            <li>🔍 <strong>Extract</strong> address and coordinates from CRM data</li>
            <li>🌐 <strong>Geocode</strong> the address to get Google's coordinates</li>
            <li>📏 <strong>Calculate</strong> distance difference between input coordinates and geocoded coordinates</li>
            <li>�️ <strong>Show two maps:</strong> One from input coordinates, one from geocoded coordinates</li>
            <li>⚡ <strong>Validate</strong> accuracy of your CRM coordinates</li>
        </ul>
        
        <h4>📝 Expected Input Format:</h4>
        <code>Selected address: [Your Address Here], latitude: [Latitude], longitude: [Longitude]</code>
        
        <h4>🎯 Purpose:</h4>
        <p>Compare the coordinates stored in your CRM with what Google Maps thinks those coordinates should be for the same address.</p>
    </div>
    """, unsafe_allow_html=True)
