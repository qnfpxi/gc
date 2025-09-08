import requests
import time

def test_connection():
    urls = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.13:5173"
    ]
    
    for url in urls:
        try:
            print(f"Testing {url}...")
            response = requests.get(url, timeout=5)
            print(f"  Status: {response.status_code}")
            print(f"  Content length: {len(response.content)}")
            print(f"  Headers: {dict(response.headers)}")
        except requests.exceptions.RequestException as e:
            print(f"  Error: {e}")
        print()

if __name__ == "__main__":
    test_connection()