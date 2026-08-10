import urllib.request
import urllib.parse
import json

def post(url, data):
    req = urllib.request.Request(url, method="POST", data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

def get(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

print("Testing Tools API")
base_url = "http://localhost:8000"

print(f"\nRoot: {get(base_url + '/')}")
print(f"Ready: {get(base_url + '/ready')}")

print("\nTesting code_tool...")
print(post(f"{base_url}/api/tools/code_tool/run", {"expression": "2 + 2"}))

print("\nTesting file_tool write...")
print(post(f"{base_url}/api/tools/file_tool/run", {"action": "write", "filename": "test.txt", "content": "hello world"}))

print("\nTesting file_tool read...")
print(post(f"{base_url}/api/tools/file_tool/run", {"action": "read", "filename": "test.txt"}))

print("\nTesting search_tool...")
print(post(f"{base_url}/api/tools/search_tool/run", {"query": "fastapi"}))

print("\nTesting youtube_transcript_tool...")
print(post(f"{base_url}/api/tools/youtube_transcript_tool/run", {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}))
