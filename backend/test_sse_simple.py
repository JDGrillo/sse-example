"""Simple SSE streaming test without Unicode characters."""

import requests
import json

url = "http://127.0.0.1:8001/api/corrections/stream"
payload = {"text": "Test text with error.", "request_id": "test-001"}
headers = {"Accept": "text/event-stream"}

try:
    response = requests.post(
        url, json=payload, stream=True, headers=headers, timeout=10
    )
    print(f"Status Code: {response.status_code}")
    print(f'Content-Type: {response.headers.get("content-type")}')
    print(f'Cache-Control: {response.headers.get("cache-control")}')
    print(f'Connection: {response.headers.get("connection")}')
    print("\nFirst 10 events:")
    count = 0
    for line in response.iter_lines(decode_unicode=True):
        if line and count < 10:
            print(f"  {line}")
            count += 1
    print(f"\nTotal lines received: {count}")
    print("Test PASSED" if response.status_code == 200 else "Test FAILED")
except Exception as e:
    print(f"Error: {e}")
