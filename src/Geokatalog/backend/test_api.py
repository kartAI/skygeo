"""
Simple API test script for STAC Catalog
Run this after starting the backend server to verify everything works
"""
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"  ✓ Health check passed")
        print(f"    Data directory: {data.get('data_directory')}")
        print(f"    Catalog title: {data.get('catalog_title')}")
        return True
    except Exception as e:
        print(f"  ✗ Health check failed: {e}")
        return False

def test_root_catalog():
    """Test root catalog endpoint"""
    print("\nTesting root catalog...")
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "Catalog"
        print(f"  ✓ Root catalog retrieved")
        print(f"    Title: {data.get('title')}")
        print(f"    ID: {data.get('id')}")
        return True
    except Exception as e:
        print(f"  ✗ Root catalog failed: {e}")
        return False

def test_collections():
    """Test collections endpoint"""
    print("\nTesting collections...")
    try:
        response = requests.get(f"{BASE_URL}/collections")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        collections = data["collections"]
        print(f"  ✓ Found {len(collections)} collection(s)")
        
        for col in collections:
            print(f"    - {col['id']}: {col['title']}")
        
        return collections
    except Exception as e:
        print(f"  ✗ Collections test failed: {e}")
        return []

def test_collection_items(collection_id):
    """Test collection items endpoint"""
    print(f"\nTesting items for collection '{collection_id}'...")
    try:
        response = requests.get(f"{BASE_URL}/collections/{collection_id}/items")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        items = data["features"]
        print(f"  ✓ Collection '{collection_id}' has {len(items)} item(s)")
        
        if items:
            item = items[0]
            print(f"    First item: {item['id']}")
            print(f"    Bbox: {item.get('bbox')}")
        
        return True
    except Exception as e:
        print(f"  ✗ Collection items test failed: {e}")
        return False

def test_search():
    """Test search endpoint"""
    print("\nTesting search...")
    try:
        response = requests.get(f"{BASE_URL}/search?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        items = data["features"]
        print(f"  ✓ Search returned {len(items)} item(s)")
        
        if "context" in data:
            print(f"    Returned: {data['context'].get('returned')}")
            print(f"    Limit: {data['context'].get('limit')}")
        
        return True
    except Exception as e:
        print(f"  ✗ Search test failed: {e}")
        return False

def test_refresh():
    """Test catalog refresh endpoint"""
    print("\nTesting catalog refresh...")
    try:
        response = requests.post(f"{BASE_URL}/refresh")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        print(f"  ✓ Catalog refresh successful")
        print(f"    Message: {data.get('message')}")
        print(f"    Collections: {data.get('collections')}")
        return True
    except Exception as e:
        print(f"  ✗ Catalog refresh failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("STAC Catalog API Test Suite")
    print("=" * 60)
    
    # Test health first
    if not test_health():
        print("\n❌ Backend is not responding. Make sure it's running on http://localhost:8000")
        sys.exit(1)
    
    # Test root catalog
    test_root_catalog()
    
    # Test collections
    collections = test_collections()
    
    # Test items for each collection
    if collections:
        for collection in collections:
            test_collection_items(collection["id"])
    else:
        print("\n⚠️  No collections found. Add geospatial files to the data directory and refresh.")
    
    # Test search
    test_search()
    
    # Test refresh
    test_refresh()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check the frontend at http://localhost:3000")
    print("2. Add more geospatial files to backend/data/")
    print("3. Use the refresh button in the UI or call POST /refresh")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)

