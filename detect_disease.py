from inference_sdk import InferenceHTTPClient
from PIL import Image

# Initialize the Inference Client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="X345vMQr4qEBT3G38COB"
)

# Path to the image
image_path = r"C:\Users\hp\Desktop\24\download.jpeg"  # Use raw string to handle backslashes

# Open the image using PIL
image = Image.open(image_path)

# Perform inference using the model
result = CLIENT.infer(image, model_id="plants-diseases-detection-and-classification/12")

# Show the raw result (optional for debugging)
print("API Response:", result)

# Check if 'predictions' key exists and if there are predictions
if 'predictions' in result and len(result['predictions']) > 0:
    # Extract the first prediction
    prediction = result['predictions'][0]
    disease_class = prediction['class']
    confidence = prediction['confidence'] * 100

    # Print the results to the terminal
    print(f"Disease Detected: {disease_class}")
    print(f"Confidence: {confidence:.2f}%")
else:
    print("No predictions found.")

