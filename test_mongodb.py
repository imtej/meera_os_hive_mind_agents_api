"""Quick MongoDB connection test script."""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def test_mongodb():
    """Test MongoDB connection."""
    print("=" * 60)
    print("MongoDB Connection Test")
    print("=" * 60)
    
    # Get connection string
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database = os.getenv("MONGODB_DATABASE", "meera_os")
    
    print(f"\nConnection String: {uri.split('@')[0]}@...")  # Hide password
    print(f"Database: {database}")
    print("\nTesting connection...")
    
    try:
        # Test connection with timeout
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Test server info
        server_info = client.server_info()
        print("✅ MongoDB connection successful!")
        print(f"   Server version: {server_info.get('version', 'Unknown')}")
        
        # Test database access
        db = client[database]
        collections = db.list_collection_names()
        print(f"✅ Database '{database}' accessible!")
        print(f"   Existing collections: {collections if collections else 'None'}")
        
        # Test write (create a test document)
        test_collection = db["_test_connection"]
        test_collection.insert_one({"test": True, "timestamp": "now"})
        test_collection.delete_one({"test": True})
        print("✅ Write/Delete test successful!")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! MongoDB is ready for Meera OS.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB connection failed!")
        print(f"   Error: {str(e)}")
        print("\n" + "=" * 60)
        print("Troubleshooting Steps:")
        print("=" * 60)
        print("1. Check MongoDB is running:")
        print("   - Windows: Get-Service MongoDB")
        print("   - Linux/Mac: sudo systemctl status mongod")
        print("\n2. Verify MONGODB_URI in .env file")
        print("   - Local: mongodb://localhost:27017")
        print("   - Atlas: mongodb+srv://user:pass@cluster.mongodb.net/...")
        print("\n3. Check firewall/network settings")
        print("4. For Atlas: Verify IP is whitelisted")
        print("\nSee MONGODB_SETUP.md for detailed instructions.")
        print("=" * 60)
        
        return False

if __name__ == "__main__":
    success = test_mongodb()
    sys.exit(0 if success else 1)

