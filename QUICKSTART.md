# Quick Start Guide

Get Meera OS running in 5 minutes!

## Prerequisites Check

- [ ] Python 3.10+ installed
- [ ] MongoDB installed and running
- [ ] Gemini API key obtained

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Start MongoDB

**Windows:**
```bash
# If MongoDB is installed as a service, it should already be running
# Otherwise, navigate to MongoDB bin directory and run:
mongod
```

**Linux/Mac:**
```bash
# If installed via package manager
sudo systemctl start mongod
# Or
mongod
```

### 4. Run Meera OS

**CLI Mode:**
```bash
python main.py 39383 "Hello, Meera!"
```

**API Server Mode:**
```bash
python -m src.api.server
```

Then in another bash terminal:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "39383",
    "message": "what is the impact of consciousness in 2030?"
  }'
```

## First Conversation

Try this example:

```bash
python main.py 39383 "what is the impact of consciousness in 2030?"
```

Meera will:
1. Retrieve relevant memories (if any exist)
2. Build a dynamic system prompt
3. Generate a contextual response
4. Save new memories from the conversation

## Troubleshooting

### MongoDB Connection Error

**Error:** `pymongo.errors.ServerSelectionTimeoutError`

**Solution:**
- Ensure MongoDB is running: `mongod` or check service status
- Verify connection string in `.env`: `MONGODB_URI=mongodb://localhost:27017`
- Check firewall settings if using remote MongoDB

### Gemini API Error

**Error:** `Invalid API key` or `403 Forbidden`

**Solution:**
- Verify your API key in `.env` file
- Check API key is active in Google AI Studio
- Ensure you have quota/credits available

### ChromaDB Path Error

**Error:** Permission denied or path not found

**Solution:**
- Ensure `CHROMA_DB_PATH` in `.env` points to a writable directory
- Default: `./chroma_db` (creates in project root)

### Import Errors

**Error:** `ModuleNotFoundError`

**Solution:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.10+)

## Next Steps

1. **Customize Configuration**: Edit `config/settings.yaml` to adjust Meera's personality
2. **Add Initial Memories**: Use the API to seed some initial memories
3. **Monitor Logs**: Check console output for detailed operation logs
4. **Scale Up**: Consider deploying with proper production settings

## Example API Usage

### Python Client

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "user_id": "39383",
        "message": "Tell me about consciousness"
    }
)

print(response.json()["response"])
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: '39383',
    message: 'Tell me about consciousness'
  })
});

const data = await response.json();
console.log(data.response);
```

## Support

For issues, check:
1. Logs in console output
2. MongoDB connection status
3. API key validity
4. Environment variables configuration

Happy building! 🚀

