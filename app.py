import streamlit as st
import sqlite3
from datetime import datetime
from PIL import Image
from inference_sdk import InferenceHTTPClient
import urllib.parse

# Connect to the database (or create one if it doesn't exist)
conn = sqlite3.connect('farmers_data.db')
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS Farmers (
    FarmerID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT,
    Contact TEXT,
    FieldSize REAL,
    CropPlanted TEXT
)''')

# Initialize the Inference Client for crop disease detection
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",  # Replace with the actual API URL for your model
    api_key="X345vMQr4qEBT3G38COB"  # Replace with the actual API Key for your model
)

# Function to add a new farmer
def add_farmer(name, contact, field_size, crop_planted):
    cursor.execute('SELECT FarmerID FROM Farmers WHERE Contact = ?', (contact,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Return existing FarmerID
    cursor.execute('INSERT INTO Farmers (Name, Contact, FieldSize, CropPlanted) VALUES (?, ?, ?, ?)',
                   (name, contact, field_size, crop_planted))
    conn.commit()
    return cursor.lastrowid  # Return the newly inserted FarmerID

# Function to fetch a farmer's details by FarmerID
def get_farmer_details(farmer_id):
    cursor.execute('SELECT * FROM Farmers WHERE FarmerID = ?', (farmer_id,))
    return cursor.fetchone()

# Streamlit UI Setup
st.title("NurtureWise Agro")
st.subheader("Farmer Registration and Disease Record Dashboard")

# Streamlit Sidebar for Farmer Registration/Login
st.sidebar.title("Farmer Login / Registration")

# Farmer Registration
def register_farmer():
    st.sidebar.subheader("Register a New Farmer")
    name = st.sidebar.text_input("Name")
    contact = st.sidebar.text_input("Contact Number")
    field_size = st.sidebar.number_input("Field Size (acres)", min_value=0.1, step=0.1)
    crop_planted = st.sidebar.text_input("Crop Planted")
    
    if st.sidebar.button("Register Farmer"):
        if name and contact and field_size and crop_planted:
            farmer_id = add_farmer(name, contact, field_size, crop_planted)
            if farmer_id:
                st.sidebar.success(f"Farmer registered successfully! Farmer ID: {farmer_id}")
            else:
                st.sidebar.error("Error registering the farmer. Please try again.")
        else:
            st.sidebar.error("Please fill in all fields.")

# Farmer Login
def login_farmer():
    st.sidebar.subheader("Farmer Login")
    contact = st.sidebar.text_input("Contact Number (Login)")
    
    if st.sidebar.button("Login"):
        cursor.execute('SELECT * FROM Farmers WHERE Contact = ?', (contact,))
        farmer = cursor.fetchone()
        if farmer:
            st.session_state.farmer_id = farmer[0]  # Store FarmerID in session
            st.session_state.contact = farmer[2]  # Store contact in session
            st.sidebar.success(f"Welcome back, {farmer[1]}!")
        else:
            st.sidebar.error("Farmer not found. Please register first.")

# Check if the farmer is logged in
if 'farmer_id' not in st.session_state:
    register_farmer()
    login_farmer()
else:
    farmer_id = st.session_state.farmer_id
    st.sidebar.subheader(f"Logged in as {st.session_state.contact}")
    
    # Image upload widget
    uploaded_file = st.file_uploader("Upload an image of the crop leaf to detect the disease.", type=["jpg", "jpeg", "png"])
    
    # Field size and affected area input
    field_size = st.number_input("Enter total field size (acres)", min_value=0.1, step=0.1)
    affected_area = st.number_input("Enter affected area (acres)", min_value=0.1, step=0.1)
    crop_price_usd = st.number_input("Enter current crop price (per unit in USD)", min_value=0.1, step=0.1)
    crop_price_inr = crop_price_usd * 82  # Convert USD to INR (Assumed conversion rate)
    
    # Perform inference when an image is uploaded
    if uploaded_file is not None:
        # Display the uploaded image
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

        # Convert the uploaded file to a PIL image
        image = Image.open(uploaded_file)
        
        # Convert the image to RGB if it is not in that mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Perform inference using the model
        with st.spinner('Detecting disease...'):
            result = CLIENT.infer(image, model_id="plants-diseases-detection-and-classification/12")

        # Check if 'predictions' key exists and if there are predictions
        if 'predictions' in result and len(result['predictions']) > 0:
            # Extract the first prediction
            prediction = result['predictions'][0]
            disease_class = prediction['class']
            confidence = prediction['confidence'] * 100

            # Display the results
            st.write(f"**Disease Detected:** {disease_class}")
            st.write(f"**Confidence:** {confidence:.2f}%")

            # Generate the Google search link for fertilizer products based on the disease
            search_query = f"{disease_class} fertilizer product shop"
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
            st.write(f"For managing **{disease_class}**, check relevant fertilizer products here: [Search on Google]({search_url})")

            # Generate YouTube search link for disease-specific videos
            youtube_query = f"{disease_class} management tips"
            youtube_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(youtube_query)}"
            st.write(f"To learn how to manage **{disease_class}**, watch related videos here: [Search on YouTube]({youtube_url})")

            # Calculate expected income in INR based on farmer input
            if field_size > 0 and affected_area > 0 and crop_price_inr > 0:
                yield_loss_percentage = (affected_area / field_size) * 100
                expected_revenue_loss = (affected_area / field_size) * crop_price_inr * field_size  # Revenue loss in INR
                total_expected_income = (field_size - affected_area) * crop_price_inr  # Income from unaffected area in INR

                # Display expected income calculations
                st.write(f"### Expected Income Calculations (in INR)")
                st.write(f"Total field size: {field_size} acres")
                st.write(f"Affected area: {affected_area} acres")
                st.write(f"Current crop price: ₹{crop_price_inr:.2f} per unit")
                st.write(f"Estimated yield loss: {yield_loss_percentage:.2f}%")
                st.write(f"Expected revenue loss due to affected area: ₹{expected_revenue_loss:.2f}")
                st.write(f"Total expected income from unaffected crop area: ₹{total_expected_income:.2f}")
            else:
                st.info("Enter valid field details to calculate expected income.")
        else:
            st.error("No predictions found. Please try again.")
