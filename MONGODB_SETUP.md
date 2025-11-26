# MongoDB Setup Guide for Meera OS

## Why MongoDB is Needed

MongoDB stores:
- **Memory Nodes**: All conversation memories with metadata
- **User Identities**: User profiles that evolve over time
- **Hive Mind Memories**: Shared memories across users

Without MongoDB, memories are lost between sessions.

---

## Option 1: MongoDB Atlas (Cloud - Recommended for Development)

### Step 1: Create Free Account
1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up with Google/GitHub/Email
3. Choose **FREE tier (M0)** - Perfect for development

### Step 2: Create Cluster
1. Choose **AWS** as cloud provider
2. Select a region close to you
3. Choose **M0 Sandbox** (Free tier)
4. Click "Create Cluster" (takes 3-5 minutes)

### Step 3: Create Database User
1. Go to **Database Access** (left sidebar)
2. Click **Add New Database User**
3. Choose **Password** authentication
4. Username: `meera_user` (or any name)
5. Password: Generate a strong password (save it!)
6. Database User Privileges: **Read and write to any database**
7. Click **Add User**

### Step 4: Whitelist IP Address
1. Go to **Network Access** (left sidebar)
2. Click **Add IP Address**
3. Click **Allow Access from Anywhere** (for development)
   - Or add your specific IP: `0.0.0.0/0` (allows all IPs)
4. Click **Confirm**

### Step 5: Get Connection String
1. Go to **Database** (left sidebar)
2. Click **Connect** on your cluster
3. Choose **Connect your application**
4. Copy the connection string (looks like):
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### Step 6: Update .env File
Replace `<username>` and `<password>` with your database user credentials:

```env
MONGODB_URI=mongodb+srv://meera_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=meera_os
```

**Example:**
```env
MONGODB_URI=mongodb+srv://meera_user:MySecurePass123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=meera_os
```

### Step 7: Test Connection
```python
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"))
print("Connected:", client.server_info())
```

---

## Option 2: Local MongoDB Installation

### Windows Installation

#### Step 1: Download MongoDB
1. Go to https://www.mongodb.com/try/download/community
2. Select:
   - Version: Latest (7.0+)
   - Platform: Windows
   - Package: MSI
3. Download and run installer

#### Step 2: Install MongoDB
1. Run the MSI installer
2. Choose **Complete** installation
3. Check **Install MongoDB as a Service**
4. Service Name: `MongoDB`
5. Check **Run service as Network Service user**
6. **Uncheck** "Install MongoDB Compass" (optional GUI)
7. Click **Install**

#### Step 3: Verify Installation
Open PowerShell as Administrator:
```powershell
# Check if service is running
Get-Service MongoDB

# If not running, start it
Start-Service MongoDB

# Verify it's running
Get-Service MongoDB
```

#### Step 4: Test Connection
```python
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
print("Connected:", client.server_info())
```

#### Step 5: Update .env (if needed)
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=meera_os
```

---

## Option 3: Docker (Alternative)

### Install Docker Desktop
1. Download from https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop

### Run MongoDB Container
```bash
docker run -d \
  --name meera-mongodb \
  -p 27017:27017 \
  -v meera-mongodb-data:/data/db \
  mongo:latest
```

### Verify
```bash
docker ps  # Should show running container
```

---

## Troubleshooting

### Connection Refused Error
**Windows:**
```powershell
# Check if MongoDB service is running
Get-Service MongoDB

# Start the service
Start-Service MongoDB

# If service doesn't exist, install MongoDB first
```

**Check if port 27017 is in use:**
```powershell
netstat -an | findstr 27017
```

### Authentication Error
- Verify username and password in connection string
- Check database user has correct permissions
- Ensure IP is whitelisted (for Atlas)

### Connection Timeout
- Check firewall settings
- Verify network connectivity
- For Atlas: Check IP whitelist

---

## Quick Test Script

Create `test_mongodb.py`:
```python
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

try:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.server_info()
    print("✅ MongoDB connection successful!")
    
    # Test database access
    db = client[os.getenv("MONGODB_DATABASE", "meera_os")]
    print(f"✅ Database '{db.name}' accessible!")
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check MongoDB is running")
    print("2. Verify MONGODB_URI in .env file")
    print("3. Check firewall/network settings")
```

Run:
```bash
python test_mongodb.py
```

---

## Recommended Setup

**For Development:**
- Use **MongoDB Atlas Free Tier** (easiest, no installation)

**For Production:**
- Use **MongoDB Atlas** with paid tier
- Or self-hosted MongoDB with proper security

---

## Next Steps

Once MongoDB is connected:
1. Run Meera OS: `python main.py 39383 "Hello, Meera!"`
2. Check logs for "Memory saved" messages
3. Memories will persist between sessions!

