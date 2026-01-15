import urllib.request
import json
import random
import string
import urllib.error

def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def test_register():
    email = f"{random_string()}@example.com"
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "mobile": "1234567890",
        "city": "Test City",
        "dob": "01-01-2000",
        "password": "Password@123"
    }
    
    print(f"Sending payload: {payload}")
    url = "http://127.0.0.1:8000/auth/register"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Status Code: {response.getcode()}")
            print(f"Response Body: {response.read().decode('utf-8')}")
    except urllib.error.HTTPError as e:
        print(f"Request failed: {e.code} {e.reason}")
        print(f"Error Body: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_register()
