import requests
import time

def test_exostack():
    print("🧪 Testing ExoStack...")
    
    # Test hub
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✓ Hub: {response.json()}")
    except Exception as e:
        print(f"❌ Hub test failed: {e}")
        return
    
    # Test metrics
    try:
        response = requests.get("http://localhost:8000/metrics/system")
        print(f"✓ Metrics: {response.json()}")
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
    
    # Test nodes
    try:
        response = requests.get("http://localhost:8000/nodes")
        print(f"✓ Nodes: {response.json()}")
    except Exception as e:
        print(f"❌ Nodes test failed: {e}")

if __name__ == "__main__":
    test_exostack()