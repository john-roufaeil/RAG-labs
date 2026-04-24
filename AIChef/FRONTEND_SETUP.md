# Frontend Setup & Running Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
cd ~/Desktop/Lab1/frontend
npm install
```

This installs React, Axios, and other dependencies listed in `package.json`.

**Expected output:**
```
added XXX packages in XXs
```

### Step 2: Ensure Backend is Running

Make sure the FastAPI backend is running:

```bash
# Terminal 1 (Backend)
cd ~/Desktop/Lab1
fastapi dev main.py
```

**Expected output:**
```
Server started at http://127.0.0.1:8000
```

### Step 3: Start React Frontend

In a new terminal:

```bash
# Terminal 2 (Frontend)
cd ~/Desktop/Lab1/frontend
npm start
```

**Expected output:**
```
webpack compiled successfully
Compiled successfully!

You can now view ai-chef-frontend in the browser.
  Local:            http://localhost:3000
  On Your Network:  http://192.xxx.x.x:3000

Note that the development build is not optimized.
```

### Step 4: Open in Browser

- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8000/docs
- Backend Health Check: http://localhost:8000/health

---

## 📋 Folder Structure

```
Lab1/
├── backend files (main.py, chef_system.py, etc.)
└── frontend/
    ├── src/
    │   ├── components/          # React components
    │   ├── services/            # API service
    │   ├── styles/              # CSS files
    │   ├── App.jsx              # Main component
    │   └── index.js             # Entry point
    ├── public/
    │   └── index.html           # HTML template
    ├── package.json             # Dependencies
    ├── .env                     # API URL config
    └── README.md                # Full documentation
```

---

## 🔧 Configuration

### .env File

The frontend needs to know where the backend API is located.

**File:** `frontend/.env`

```
REACT_APP_API_URL=http://localhost:8000
```

### If Backend is on Different Machine

If backend is on another computer (e.g., 192.168.1.100):

```
REACT_APP_API_URL=http://192.168.1.100:8000
```

Then restart: `npm start`

---

## 🎨 Frontend Features

### Main Components

1. **ChatWindow** - Displays messages from user and chef
2. **ChatInput** - Text area and send button
3. **Sidebar** - Settings and session info

### Personality Controls

- **Creativity Level**: Strict → Balanced → Creative
- **Verbosity**: Concise → Normal → Detailed

Changes apply to next message sent.

### Session Info (Sidebar)

- Current conversation stage
- Collected ingredients count
- Session ID (for multiple users)
- List of ingredients

### Reset Button

- Clears conversation
- Resets to greeting stage
- Keeps same session ID or starts fresh

---

## 🐛 Troubleshooting

### Error: "Cannot find module 'react'"

**Solution:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### Error: "API call failed"

**Checklist:**
1. Is backend running? → Check Terminal 1
2. Is backend healthy? → Visit http://localhost:8000/health
3. Correct API URL in .env? → Should be `http://localhost:8000`
4. Is CORS issue? → Backend may need CORS headers

**To add CORS to backend**, add to `main.py` before `app = FastAPI()`:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Error: "localhost:3000 refused to connect"

**Checklist:**
1. Is React running? → Check Terminal 2
2. Port 3000 in use? → Use `lsof -i :3000` to find process
3. Try killing and restarting:
```bash
npm start
```

### Messages not sending

**Checklist:**
1. Backend API running?
2. OpenAI API key set in backend .env?
3. API key has credits?
4. Check browser console (F12) for errors

---

## 📱 Testing the App

### Test Scenario 1: Basic Chat

1. Open http://localhost:3000
2. Type: "Hi chef! I want to cook something"
3. Send
4. Should see friendly greeting from chef

### Test Scenario 2: Personality Change

1. Use sidebar to change creativity to "Creative"
2. Send: "What can I make?"
3. Response should be more experimental

### Test Scenario 3: Ingredient Tracking

1. Tell chef: "I have chicken, tomato, onion, garlic, oil"
2. Check sidebar - should show 5 ingredients
3. Send more: "Also salt and pepper"
4. Should now show 7 ingredients

### Test Scenario 4: Reset

1. Have a conversation
2. Click "Reset Session" button
3. Chat should clear
4. Should see welcome message again

---

## 📊 Network Requests

When you send a message, the frontend makes a request like:

```
POST http://localhost:8000/chat
{
  "session_id": "user_1713693600000",
  "message": "I have chicken and tomato",
  "creativity": "balanced",
  "verbosity": "normal"
}
```

Backend responds with:

```json
{
  "response": "Wonderful! With chicken and tomato...",
  "session_id": "user_1713693600000",
  "step_count": 2,
  "current_stage": "ingredients",
  "collected_ingredients": ["chicken", "tomato"],
  "message_count": 4
}
```

Frontend updates:
- Chat window with chef response
- Sidebar with new ingredients
- Step counter

---

## 🎯 Performance Tips

- Responses take 1-3 seconds (depends on OpenAI API)
- Clear old sessions to free memory
- Use "Reset Session" between tests
- Frontend loads instantly once built

---

## 🚀 Production Build

To create optimized production build:

```bash
npm run build
```

Creates `build/` folder with optimized code (~50KB vs ~300KB dev)

To test production build locally:

```bash
npx serve -s build
```

Then visit http://localhost:5000

---

## 📝 Common Commands

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Eject configuration (⚠️ irreversible!)
npm run eject
```

---

## ✅ Verification Checklist

Before considering setup complete:

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] GET /health returns 200 OK
- [ ] Can see welcome message in chat
- [ ] Can send message and get response
- [ ] Chef response appears in chat
- [ ] Ingredients show in sidebar
- [ ] Can change personality settings
- [ ] Reset button works
- [ ] No errors in browser console (F12)

---

## 🆘 Getting Help

1. **Check browser console**: F12 → Console tab for errors
2. **Check backend logs**: Look at Terminal 1 for API errors
3. **Check network tab**: F12 → Network tab to see API calls
4. **Read error messages carefully**: They usually indicate the issue

---
