import requests

try:
    response = requests.get('http://localhost:5001/api/check_login')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")