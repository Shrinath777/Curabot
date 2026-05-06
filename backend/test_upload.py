import requests
import sys

url = "http://127.0.0.1:8000/api/upload-record"
headers = {"x-user-id": "test-user-123"}
try:
    files = {"file": open("synthetic_records/Sarah_Jenkins_COMPLETE.pdf", "rb")}
except FileNotFoundError:
    print("File not found.")
    sys.exit(1)
    
data = {"report_type": "lab_result"}

try:
    print(f"Testing upload to {url}...")
    response = requests.post(url, headers=headers, files=files, data=data)
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", response.json())
    except Exception:
        print("Response Text:", response.text)
except Exception as e:
    print("Error:", e)
