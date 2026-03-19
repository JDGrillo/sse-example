"""
Test client for streaming corrections endpoint.

This script tests the POST /api/corrections/stream endpoint with SSE.
"""

import requests
import json
import sys


def test_streaming_endpoint():
    """Test the streaming corrections endpoint."""
    url = "http://127.0.0.1:8001/api/corrections/stream"

    # Sample text with errors
    sample_text = "This is a test txt with some erors. The grammer is not perfect."

    payload = {"text": sample_text, "request_id": "test-001"}

    print("=" * 60)
    print("Testing Streaming Corrections Endpoint")
    print("=" * 60)
    print(f"\nSending request to: {url}")
    print(f"Text: {sample_text}")
    print(f"Request ID: {payload['request_id']}")
    print("\nStreaming response:")
    print("-" * 60)

    try:
        response = requests.post(
            url, json=payload, stream=True, headers={"Accept": "text/event-stream"}
        )

        if response.status_code != 200:
            print(f"\nError: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

        print(f"Connected (HTTP {response.status_code})")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print("\nEvents received:")
        print("-" * 60)

        event_count = 0
        for line in response.iter_lines(decode_unicode=True):
            if line:
                print(line)
                event_count += 1

                # Stop after reasonable number of events for testing
                if event_count > 100:
                    print("\n(truncated after 100 events)")
                    break

        print("\n" + "-" * 60)
        print(f"Streaming test completed ({event_count} lines received)")
        return True

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to server")
        print("  Make sure the FastAPI server is running on http://127.0.0.1:8001")
        return False
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_streaming_endpoint()
    sys.exit(0 if success else 1)
