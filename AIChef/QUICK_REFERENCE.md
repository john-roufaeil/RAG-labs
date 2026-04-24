# AI Chef System - Quick Reference

## 📁 Project Files

```
/home/john/Desktop/Lab1/
├── main.py                          # FastAPI server with all endpoints
├── chef_system.py                   # Chef logic & state management
├── requirements.txt                 # Dependencies
├── .env                             # API keys (OPENAI_API_KEY)
├── .env.example                     # Template
├── POSTMAN_TEST_GUIDE.md           # Detailed testing guide
├── AI_Chef_System.postman_collection.json  # Ready-to-import Postman collection
└── README.md                        # Project overview
```

---

## 🚀 Quick Start

```bash
# 1. Start the server
fastapi dev main.py

# 2. Server runs on http://localhost:8000
# 3. Open Postman and import: AI_Chef_System.postman_collection.json
# 4. Or visit: http://localhost:8000/docs for interactive API explorer
```

---

## 🛠️ API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check if server is running |
| POST | `/chat` | Chat with the AI Chef |
| POST | `/set-personality` | Configure chef personality |
| GET | `/session/{id}` | View session conversation history |
| POST | `/reset/{id}` | Reset a session |

---

## 💬 Sample Chat Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user_001",
    "message": "Hi chef! I have chicken and tomatoes",
    "creativity": "balanced",
    "verbosity": "normal"
  }'
```

---

## 🎭 Personality Settings

### Creativity Levels
- **`strict`**: Traditional recipes only, no improvisation
- **`balanced`**: Mix of traditional and modern (default)
- **`creative`**: Experimental and adventurous suggestions

### Verbosity Levels
- **`concise`**: 1-2 sentences max
- **`normal`**: Standard conversational length (default)
- **`detailed`**: Full explanations and background

---

## 🔄 Conversation Flow

```
1. Greeting Stage
   User: "I want to cook something"
   Chef: "Welcome! What ingredients do you have?"

2. Ingredients Stage
   User: "I have chicken, tomato, onion, garlic..."
   Chef: "Excellent! Any herbs or spices?"

3. Preferences Stage
   User: "Italian food, 30 minutes, beginner level"
   Chef: "Perfect! Let me suggest..."

4. Recipe Stage
   User: "I'm ready!"
   Chef: "Step 1: Prepare the chicken..."

5. Done Stage
   Chef: "Congratulations! You've cooked a delicious meal!"
```

---

## 🧠 Key Features

✅ **Memory**: Remembers all ingredients and preferences  
✅ **Humanly Written**: Uses exclamations and enthusiasm  
✅ **Step-by-Step**: Never skips stages  
✅ **Context Aware**: References what user told them  
✅ **Adjustable Personality**: Creativity & verbosity control  
✅ **Session Isolation**: Each user has separate conversation  
✅ **State Tracking**: Step counter & message tracking  

---

## 📊 Response Example

```json
{
  "response": "Ah, wonderful! With that chicken and fresh herbs, we could do a beautiful Italian Chicken Piccata!...",
  "session_id": "user_john_001",
  "step_count": 3,
  "current_stage": "preferences",
  "collected_ingredients": ["chicken", "tomato", "onion", "garlic", "oil", "basil", "salt"],
  "message_count": 6
}
```

---

## 🧪 Testing Checklist

### Basic Tests
- [ ] GET /health returns 200
- [ ] POST /chat accepts message
- [ ] Ingredients are collected in list
- [ ] Steps increment correctly

### Personality Tests
- [ ] Creative mode produces creative suggestions
- [ ] Strict mode sticks to traditional recipes
- [ ] Concise mode returns short responses
- [ ] Detailed mode provides explanations

### Memory Tests
- [ ] Chef references previous ingredients
- [ ] Chef remembers preferences
- [ ] Long conversations maintain context
- [ ] Session isolation works (different IDs)

### Error Handling
- [ ] Invalid personality values return 400
- [ ] Missing OPENAI_API_KEY returns 500
- [ ] Reset clears session properly

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| 500 error on /chat | Check OPENAI_API_KEY in .env |
| Chef doesn't remember ingredients | Verify same session_id in requests |
| Personality not changing | Call /set-personality first, then /chat |
| "No module named chef_system" | Ensure chef_system.py is in same directory |
| Connection refused | Make sure fastapi dev main.py is running |

---

## 📚 File Descriptions

### main.py
- FastAPI application with 5 endpoints
- Initializes LLM (ChatOpenAI)
- Manages requests/responses
- Handles ingredient extraction

### chef_system.py
- Core business logic
- ChefState: tracks conversation state
- ChefPromptBuilder: creates dynamic prompts
- ChefStateManager: manages sessions
- Enums for Creativity and Verbosity

### requirements.txt
- fastapi: API framework
- uvicorn: ASGI server
- langchain-openai: LLM integration
- python-dotenv: Environment variables

---

## 🎯 Testing Strategy

**For Simple Test:**
1. Start server: `fastapi dev main.py`
2. Visit: http://localhost:8000/docs
3. Try POST /chat with sample message
4. Check response

**For Comprehensive Test:**
1. Import Postman collection
2. Follow POSTMAN_TEST_GUIDE.md step-by-step
3. Verify all features in checklist
4. Test error cases

---

## 💡 Tips

- Use Postman variables to reuse session_id across requests
- Check full conversation history in GET /session/{id}
- Response times depend on OpenAI API (~1-3 seconds)
- Keep API key secret, never commit .env file
- Test with different session_ids for multi-user scenarios
