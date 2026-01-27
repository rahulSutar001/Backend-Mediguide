
import requests
import os
import time

# Configuration
API_URL = "http://localhost:8000/api/v1/reports/upload"
# Using the image path provided in the user prompt metadata
IMAGE_PATH = "/Users/rahuldattasutar/.gemini/antigravity/brain/09a36565-6323-4c87-87de-6d54dae53ea7/uploaded_image_1769331566660.jpg"

# Dummy Auth Token (We need to mimic a logged-in user)
# We will use the 'get_user_id' dependency mock or we need a real token?
# The backend uses split-stack auth. Validation happens via Supabase.
# Since we don't have a frontend token easily, we might hit 401.
# However, for debugging the Local Backend, we might bypass auth or grab a token if possible.
# Alternatively, we can inspect `mediguide-backend/app/core/dependencies.py` to see how to bypass or mock.

def test_upload():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found at {IMAGE_PATH}")
        return

    print(f"Testing upload with {IMAGE_PATH}...")
    start_time = time.time()

    try:
        with open(IMAGE_PATH, 'rb') as f:
            files = {'file': (os.path.basename(IMAGE_PATH), f, 'image/jpeg')}
            # Note: Without a valid Bearer token, this will likely fail with 401/403.
            # We are testing if it HANGS or returns immediately. 
            # If it returns 401 fast, the network/server is fine.
            # If it hangs, the server is blocked.
            response = requests.post(API_URL, files=files, timeout=30)
            
        elapsed = time.time() - start_time
        print(f"Response Status: {response.status_code}")
        print(f"Response Text: {response.text}")
        print(f"Time Taken: {elapsed:.2f} seconds")

    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    test_upload()
