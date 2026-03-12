# Chatbot Configuration & Security Guide

## 🤖 Chatbot Overview

The STEM LMS includes an AI-powered chatbot using Google's Gemini API that:
- Answers student questions in real-time on the forum
- Searches course materials (RAG - Retrieval Augmented Generation)
- Falls back to internet search when course materials don't cover the topic
- Caches responses to avoid redundant API calls
- Tracks conversation history per student

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `main/static/js/chatbot.js` | Frontend chatbot UI logic & API calls |
| `main/templates/Forum.html` | Forum page with embedded chatbot widget |
| `main/views/chatbotview.py` | Backend chatbot API endpoint (`/api/chatbot/`) |
| `main/views/gemini.py` | Google Gemini API wrapper & model fallback |
| `main/models/chatbotmodel.py` | Database models for conversations & cache |
| `.env` | **LOCAL ONLY** - Contains GEMINI_API_KEY (never commit) |
| `.env.example` | Template showing env vars needed (no secrets) |
| `render.yaml` | Deployment config for Render.com |
| `stem_app/settings.py` | Django settings (loads GEMINI_API_KEY from env) |

---

## 🔑 API Key Management

### Local Development Setup

#### 1. Get Your API Key
```bash
# Visit: https://aistudio.google.com/apikey
# Click "Get API Key"
# Create new project (important!)
# Copy the generated key
```

#### 2. Create `.env` File (LOCAL ONLY)
```bash
# Create file: .env in project root
# Add this line:
GEMINI_API_KEY=AIzaSyXx...your_actual_key_here...
```

#### 3. Verify `.env` is in `.gitignore`
```bash
# Check that .env is listed in .gitignore
cat .gitignore | grep "\.env"

# Output should show:
# .env
```

### What Files to Commit ✅

```
✅ Commit to GitHub:
   - .env.example (no secrets, just template)
   - .gitignore (includes .env)
   - All Python/JavaScript source code
   - render.yaml (deployment config)

❌ Never commit:
   - .env (contains real API key)
   - __pycache__/ directories
   - *.pyc files
   - Virtual environment
```

### What NOT to Do ❌

```
❌ WRONG - Never do this:
   - Paste API key in .env.example
   - Hardcode API key in Python files
   - Commit .env file
   - Share API key in comments or docs
   - Put key in render.yaml hardcoded

✅ RIGHT - Always do this:
   - Keep key only in local .env
   - Use environment variables
   - Set secrets in Render dashboard
   - Use placeholder in .env.example
```

---

## 🚀 Deployment on Render.com

### Step 1: Set Secrets in Render Dashboard

1. Go to your Render service dashboard
2. Click "Environment"
3. Add new environment variable:
   ```
   Key: GEMINI_API_KEY
   Value: AIzaSyXx...your_production_key...
   ```
4. Save and redeploy

### Step 2: Verify render.yaml

```yaml
# render.yaml - Production environment config

services:
  - type: web
    name: stem-lms
    plan: standard
    
    env: python
    envVars:
      - key: DEBUG
        value: "false"
      - key: ALLOWED_HOSTS
        value: "yourdomain.com,www.yourdomain.com"
      
      # IMPORTANT: API key comes from Render secrets, not hardcoded
      # DO NOT put actual key value here
      - key: GEMINI_API_KEY
        fromService:
          type: env  # Render looks for this env var
```

### Step 3: How Django Loads the Key

```python
# stem_app/settings.py - Line 225

# Load from .env file locally
load_dotenv(BASE_DIR / ".env")

# Read the API key from environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
# ↓ Returns value from:
#   - .env file (local development)
#   - Render environment variable (production)
#   - Empty string (if not found - will show error)
```

---

## 🔐 Security Checklist

### Before Pushing to GitHub

- [ ] Run: `git status` 
- [ ] Verify `.env` is **NOT** in staged files
- [ ] Check `.gitignore` includes `.env`
- [ ] Search repo: `grep -r "AIzaSy" .` (no keys should appear)
- [ ] Don't push if any API keys visible

### Before Deploying to Render

- [ ] Set `GEMINI_API_KEY` in Render "Environment" tab
- [ ] Don't put key in `render.yaml` file
- [ ] Verify `DEBUG=false` in production
- [ ] Test deployment with fresh key

### If You Accidentally Expose a Key

1. **Immediately revoke the key:**
   - Go to https://aistudio.google.com/apikey
   - Delete the exposed key
   - Create a new key

2. **Update everywhere:**
   - Update local `.env` file
   - Update Render dashboard environment variable
   - Restart Render service: `Redeployment → Deploy latest`

3. **Check git history** (if already pushed):
   ```bash
   # Remove from git history
   git filter-branch --tree-filter 'rm -f .env' HEAD
   git push origin --force-with-lease
   ```

---

## 🛠️ How the Chatbot Works

### Data Flow

```
1. USER TYPES QUESTION
   ↓ (in Forum.html)
   Student clicks send button
   ↓
2. FRONTEND (chatbot.js)
   - Gets CSRF token
   - Creates message object
   - POST to /api/chatbot/
   ↓
3. BACKEND (chatbotview.py)
   validate_request()
   ↓
   check_cache() → Found? Return cached answer
   ↓
   search_pdf_knowledge() → Found? Generate from course materials (RAG)
   ↓
   internet_search() → Perform web search
   ↓
   generate_response() using Gemini API
   ↓
4. GEMINI API (gemini.py)
   Try model_1 → fails?
   ↓
   Try model_2 → fails?
   ↓
   Try model_3 → success! Return response
   ↓
5. RESPONSE SENT BACK
   - Stores in ChatbotConversation
   - Caches for future use
   - Returns to frontend
   ↓
6. FRONTEND DISPLAYS RESPONSE
   Animated message appears in chat widget
```

### Model Fallback Sequence

If the primary model fails, it automatically tries backups:

```python
# main/views/gemini.py - Line 17-20

FALLBACK_MODEL_SEQUENCE = [
    "gemini-2.5-flash",      # Primary (fastest, cheapest)
    "gemini-flash-latest",   # Fallback 1
    "gemini-2.0-flash",      # Fallback 2
]
```

**Why fallback?** Different API key tiers have access to different models. If primary fails, system automatically tries alternatives.

---

## 📊 Database Models

### ChatbotConversation
Stores each user question:
```python
user = ForeignKey(User)        # Which student asked?
question = TextField()         # The actual question
created_at = DateTimeField()   # When was it asked?
```

### ChatbotResponse
Stores chatbot's answer:
```python
conversation = ForeignKey(ChatbotConversation)  # Links to question
response = TextField()         # The AI-generated response
sources = JSONField()          # Where did answer come from?
response_type = CharField()    # 'rag', 'cached', 'internet_search'
created_at = DateTimeField()   # When was response generated?
```

### ChatbotCache
Avoids asking same question twice:
```python
question_hash = CharField()    # MD5 hash of question (fast lookup)
question = TextField()         # Original question text
answer = TextField()           # Cached response
```

---

## ⚙️ Configuration Options

### Environment Variables (in .env)

```bash
# Required
GEMINI_API_KEY=AIzaSyXx...  # Google Gemini API key

# Already set in .env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=stemappza@gmail.com
EMAIL_HOST_PASSWORD=ddtz gltz vscj loab
```

### Django Settings (stem_app/settings.py)

```python
# Line 229 - API key configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
# If not set, defaults to empty string
# gemini.py will show error: "API key not configured"
```

### Chatbot Config in Database

Access via Django admin panel:
- **URL:** http://localhost:8000/admin/main/chatbotconfig/
- **Settings:**
  - `is_enabled` - Turn chatbot on/off
  - `mode` - 'gemini', 'external_api', or 'ollama'
  - `allow_internet_search` - Enable web search fallback
  - `maintenance_message` - Message when disabled

---

## 🐛 Debugging

### Check if API Key is Loaded

```bash
# Create test_key.py:
import os
from dotenv import load_dotenv
load_dotenv()
print(f"API Key: {os.getenv('GEMINI_API_KEY', 'NOT FOUND')}")

# Run it:
python test_key.py
```

### View Server Logs

```bash
# Terminal where runserver is running shows:
[11/Mar/2026 11:18:33] "POST /api/chatbot/ HTTP/1.1" 200 16318

# Check for Gemini errors:
grep -i "gemini" logs.txt
# Look for: "API_KEY_INVALID", "not found", "quota exceeded"
```

### Test Chatbot Manually

```bash
# Curl test
curl -X POST http://localhost:8000/api/chatbot/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is 2+2?"}'

# Expected response:
# {"response": "2 + 2 equals 4", "conversation_id": 123, ...}
```

### If You See "API key not configured"

1. Check `.env` file exists with key
2. Check Django settings has: `GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')`
3. **Restart Django server** - it caches env vars on startup
4. Verify API key hasn't been revoked (test at https://aistudio.google.com/apikey)

---

## 📝 Summary: Safe Deployment

### Local Dev ✅
```bash
1. Create .env with real key
2. .env is in .gitignore (won't push)
3. .env.example shows template (can commit)
4. Restart server to load changes
```

### Production (Render) ✅
```bash
1. Set GEMINI_API_KEY in Render dashboard "Environment"
2. Don't put key in render.yaml
3. Render automatically passes env var to app
4. Django reads it via os.getenv()
5. Restart/redeploy service
```

### GitHub Push ✅
```bash
1. git status → verify .env not listed
2. git commit → only .env.example (no secrets)
3. .gitignore in repo → .env line prevents accidents
4. Other developers create their own .env locally
```

---

## 🚨 Red Flags (Problems)

| Problem | Cause | Fix |
|---------|-------|-----|
| "API key not configured" | .env missing or key empty | Create .env with real key, restart server |
| API key exposed on GitHub | Committed .env by accident | Revoke key, add to .gitignore, new key |
| Works locally, fails on Render | Key not in Render dashboard | Set GEMINI_API_KEY in Render Environment |
| Models not found (404) | Wrong model name or different API tier | Check gemini.py fallback sequence |
| Quota exceeded | Rate limit hit | Wait 1 hour or upgrade plan |

---

## 📞 Support

**If chatbot stops working:**

1. Check logs: `grep "Gemini" server.log`
2. Verify API key in Render dashboard
3. Test locally with fresh key
4. Check model availability: visit https://aistudio.google.com/apikey
5. Review [LEARNER_RECOMMENDATIONS_PLAN.md](../LEARNER_RECOMMENDATIONS_PLAN.md) for architecture

