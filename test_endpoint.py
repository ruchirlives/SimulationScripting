import requests
import json

# Test the simulation endpoint
url = "http://127.0.0.1:5000/simulate"

# Test with just the steps parameter (should fail gracefully)
try:
    response = requests.post(url, data={"steps": "3"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
except Exception as e:
    print(f"Error: {e}")

# Test with a YAML file
try:
    with open('test_simulation.yaml', 'rb') as f:
        files = {'yaml_file': f}
        data = {'steps': '3'}
        response = requests.post(url, files=files, data=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success! Keys: {list(result.keys())}")
        if 'budget' in result:
            print(f"Budget entries: {len(result['budget'])}")
    else:
        print(f"Error response: {response.text[:500]}...")
except Exception as e:
    print(f"Error: {e}")
