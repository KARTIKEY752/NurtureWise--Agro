import streamlit as st
import sqlite3
from PIL import Image
from inference_sdk import InferenceHTTPClient
import urllib.parse

# Database connection setup
conn = sqlite3.connect('farmers_data.db')
cursor = conn.cursor()

# Create the database table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS Farmers (
    FarmerID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT,
    Contact TEXT UNIQUE,
    FieldSize REAL,
    CropPlanted TEXT
)''')

# Initialize the Inference Client for crop disease detection
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="X345vMQr4qEBT3G38COB"  # Replace with your API key
)

# Functions for Farmer Management
def add_farmer(name, contact, field_size, crop_planted):
    """Add a new farmer to the database."""
    cursor.execute("INSERT OR IGNORE INTO Farmers (Name, Contact, FieldSize, CropPlanted) VALUES (?, ?, ?, ?)",
                   (name, contact, field_size, crop_planted))
    conn.commit()

def get_farmer(contact):
    """Retrieve a farmer's details by contact number."""
    cursor.execute("SELECT * FROM Farmers WHERE Contact = ?", (contact,))
    return cursor.fetchone()

# Streamlit App UI
st.markdown(
    """
    <h1 style="text-align: center; font-size: 60px; color: #2E8B57;">
        NurtureWise Agro
    </h1>
    """,
    unsafe_allow_html=True,
)
st.sidebar.title("NurtureWise Agro System")

# Farmer Registration Section
def register_farmer():
    st.sidebar.subheader("Register Farmer")
    name = st.sidebar.text_input("Name")
    contact = st.sidebar.text_input("Contact Number")
    field_size = st.sidebar.number_input("Field Size (acres)", min_value=0.0, step=0.1)
    crop_planted = st.sidebar.text_input("Crop Planted")
    
    if st.sidebar.button("Register"):
        if name and contact and field_size and crop_planted:
            add_farmer(name, contact, field_size, crop_planted)
            st.sidebar.success("Registration successful! You can now log in.")
        else:
            st.sidebar.error("Please fill out all fields.")

# Farmer Login Section
def login_farmer():
    st.sidebar.subheader("Login")
    contact = st.sidebar.text_input("Contact Number (Login)", key="login_contact")
    
    if st.sidebar.button("Login"):
        farmer = get_farmer(contact)
        if farmer:
            st.session_state.logged_in = True
            st.session_state.farmer_details = farmer
            st.sidebar.success(f"Welcome, {farmer[1]}!")
        else:
            st.sidebar.error("Farmer not found. Please register.")

# Check login status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    register_farmer()
    login_farmer()
else:
    farmer = st.session_state.farmer_details
    st.sidebar.success(f"Logged in as {farmer[1]}")
    
    # Logout Option
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.farmer_details = None
        st.experimental_rerun()
    
    # Main Dashboard Content
    st.subheader("Crop Disease Detection & Economic Impact Analysis")

    # Image Upload for Disease Detection
    uploaded_file = st.file_uploader("Upload an image of the crop leaf to detect disease.", type=["jpg", "jpeg", "png"])
    
    # Economic Input Fields
    field_size = st.number_input("Enter total field size (acres)", min_value=0.0, step=0.1, value=farmer[3])
    affected_area = st.number_input("Enter affected area (acres)", min_value=0.0, step=0.1, value=0.0)
    crop_price = st.number_input("Enter current crop price (per unit in INR)", min_value=0.0, step=0.1, value=0.0)

    if uploaded_file:
        # Display uploaded image
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

        # Process image for disease detection
        image = Image.open(uploaded_file)
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Perform disease detection
        with st.spinner("Detecting disease..."):
            result = CLIENT.infer(image, model_id="plants-diseases-detection-and-classification/12")
        
        if result and "predictions" in result and result["predictions"]:
            prediction = result["predictions"][0]
            disease = prediction["class"]
            confidence = prediction["confidence"] * 100
            
            # Display detection results
            st.write(f"**Disease Detected:** {disease}")
            st.write(f"**Confidence:** {confidence:.2f}%")
            
            # Links for additional resources
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(disease + ' fertilizer product shop')}"
            st.write(f"Find fertilizers: [Google Search]({search_url})")
            
            youtube_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(disease + ' management tips')}"
            st.write(f"Learn management tips: [YouTube Search]({youtube_url})")
        else:
            st.error("No disease detected. Please try again.")

    # Economic Calculations
    if field_size > 0 and affected_area > 0 and crop_price > 0:
        yield_loss_percent = (affected_area / field_size) * 100
        revenue_loss = (affected_area / field_size) * crop_price * field_size
        income_after_loss = (field_size - affected_area) * crop_price

        st.subheader("Economic Impact Analysis")
        st.write(f"**Field Size:** {field_size} acres")
        st.write(f"**Affected Area:** {affected_area} acres")
        st.write(f"**Crop Price:** ₹{crop_price} per unit")
        st.write(f"**Estimated Yield Loss:** {yield_loss_percent:.2f}%")
        st.write(f"**Revenue Loss:** ₹{revenue_loss:.2f}")
        st.write(f"**Income After Loss:** ₹{income_after_loss:.2f}")
    else:
        st.info("Please fill in the inputs above to calculate economic impact.")
