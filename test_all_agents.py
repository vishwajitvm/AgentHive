import requests
import time

def test_agents():
    # Get all agents
    res = requests.get("http://localhost:8000/api/agents")
    agents = res.json()
    print(f"Testing {len(agents)} agents...")
    
    for idx, agent in enumerate(agents):
        print(f"\n--- Testing Agent {idx+1}/{len(agents)}: {agent['name']} (ID: {agent['id']}) ---")
        
        # Test Query 1 (Cold Start)
        payload = {"query": "Hello, this is a test query. Just respond with a brief greeting."}
        start = time.time()
        try:
            r = requests.post(f"http://localhost:8000/api/agents/{agent['id']}/run", json=payload)
            elapsed = time.time() - start
            data = r.json()
            status = r.status_code
            print(f"Cold Start | Status: {status} | Latency: {elapsed:.3f}s")
        except Exception as e:
            print(f"Cold Start Failed: {e}")
            continue

        # Test Query 2 (Cache Hit)
        start = time.time()
        try:
            r = requests.post(f"http://localhost:8000/api/agents/{agent['id']}/run", json=payload)
            elapsed2 = time.time() - start
            print(f"Cache Hit  | Status: {r.status_code} | Latency: {elapsed2:.3f}s")
            
            if elapsed2 < 0.1:
                print("✅ Cache working perfectly!")
            else:
                print("❌ Cache failed to optimize!")
        except Exception as e:
            print(f"Cache Hit Failed: {e}")

if __name__ == "__main__":
    test_agents()
