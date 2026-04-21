# AI Chef System - Manual Test Guide with Postman

## Quick Start

1. **Start the server:**
   ```bash
   fastapi dev main.py
   ```

2. **Open Postman** and import the requests below or use the collection file

3. **API Base URL:** `http://localhost:8000`

---

## Test Cases

### 1. Health Check ✅
**Endpoint:** `GET /health`

**Expected Response:**
```json
{
    "status": "ok",
    "service": "AI Chef System"
}
```

**Test Steps:**
- Open Postman
- Create new request: GET
- URL: `http://localhost:8000/health`
- Send
- Should return 200 OK

---

### 2. Initial Chef Greeting 👨‍🍳
**Endpoint:** `POST /chat`

**Request Body:**
```json
{
    "session_id": "user_john_001",
    "message": "Hi chef! I want to cook something delicious",
    "creativity": "balanced",
    "verbosity": "normal"
}
```

**Expected Behavior:**
- Chef welcomes you warmly
- Should transition to ingredients stage
- Response includes: `current_stage: "ingredients"`
- Chef asks about available ingredients

**Test Steps:**
- Create new POST request
- URL: `http://localhost:8000/chat`
- Body: Raw JSON (paste the request above)
- Send
- Verify chef greeting is friendly and mentions ingredients

---

### 3. Provide Ingredients 🥬🍗🧅
**Endpoint:** `POST /chat`

**Request Body:**
```json
{
    "session_id": "user_john_001",
    "message": "I have chicken, tomato, onion, garlic, olive oil, basil, and salt",
    "creativity": "balanced",
    "verbosity": "normal"
}
```

**Expected Behavior:**
- Chef acknowledges the ingredients
- `collected_ingredients` array shows: ["chicken", "tomato", "onion", "garlic", "oil", "basil", "salt"]
- Chef may ask follow-up questions about more ingredients or move to preferences

**Test Steps:**
- Send the request above
- Check response includes all ingredients in `collected_ingredients`
- Verify chef responds naturally with enthusiasm

---

### 4. Set Creative Personality 🎨
**Endpoint:** `POST /set-personality`

**Request Body:**
```json
{
    "session_id": "user_john_001",
    "creativity": "creative",
    "verbosity": "detailed"
}
```

**Expected Response:**
```json
{
    "message": "Personality updated",
    "creativity": "creative",
    "verbosity": "detailed"
}
```

**Test Steps:**
- Create new POST request
- URL: `http://localhost:8000/set-personality`
- Body: Raw JSON (paste the request above)
- Send
- Should return 200 OK

---

### 5. Get Creative Recipe Suggestions 🎯
**Endpoint:** `POST /chat`

**Request Body (After setting creative personality):**
```json
{
    "session_id": "user_john_001",
    "message": "OK, I'm ready! What should I cook? Any creative ideas?"
}
```

**Expected Behavior:**
- Chef now responds in "creative" mode - more experimental suggestions
- Response is "detailed" - longer explanations
- Chef might suggest creative twists on classic dishes
- Responses show exclamation: "Ah!", "Brilliant!", etc.

**Test Steps:**
- Send the request
- Compare response with previous requests
- Should be noticeably more creative and detailed

---

### 6. Strict/Traditional Mode 🏛️
**Endpoint:** `POST /chat`

**First, set to strict mode:**
```json
{
    "session_id": "user_strict_001",
    "creativity": "strict",
    "verbosity": "concise"
}
```

**Then send a greeting:**
```json
{
    "session_id": "user_strict_001",
    "message": "I want to learn cooking the classic way",
    "creativity": "strict",
    "verbosity": "concise"
}
```

**Expected Behavior:**
- Chef responds in concise mode (1-2 sentences max)
- Chef emphasizes traditional recipes only
- No creative suggestions

**Test Steps:**
- Set personality to strict
- Send greeting
- Responses should be short, direct, traditional

---

### 7. Check Session State 📊
**Endpoint:** `GET /session/{session_id}`

**URL:** `http://localhost:8000/session/user_john_001`

**Expected Response:**
```json
{
    "session_id": "user_john_001",
    "step_count": 5,
    "current_stage": "ingredients",
    "collected_ingredients": ["chicken", "tomato", "onion", "garlic", "oil", "basil", "salt"],
    "message_count": 10,
    "creativity": "creative",
    "verbosity": "detailed",
    "conversation_history": [
        {"role": "user", "content": "Hi chef! I want to cook something delicious"},
        {"role": "assistant", "content": "Chef's response..."},
        ...
    ]
}
```

**Test Steps:**
- Create new GET request
- URL: `http://localhost:8000/session/user_john_001`
- Send
- Review full conversation history and all state

---

### 8. Reset Session 🔄
**Endpoint:** `POST /reset/{session_id}`

**URL:** `http://localhost:8000/reset/user_john_001`

**Expected Response:**
```json
{
    "message": "Session user_john_001 reset"
}
```

**Test Steps:**
- Create new POST request
- URL: `http://localhost:8000/reset/user_john_001`
- Send
- Get session state again - should be empty (greeting stage)

---

## Complete Conversation Flow (Step-by-Step)

### Flow: From Greeting to Recipe
Follow these steps in order to see the full flow:

**Step 1: Greeting**
```json
{
    "session_id": "flow_test",
    "message": "Hey chef! I have some chicken and veggies. Want to help me cook?",
    "creativity": "balanced",
    "verbosity": "normal"
}
```

**Step 2: List Ingredients**
```json
{
    "session_id": "flow_test",
    "message": "I have chicken breast, onion, garlic, bell pepper, tomato, olive oil, salt, pepper, and basil"
}
```

**Step 3: Share Preferences**
```json
{
    "session_id": "flow_test",
    "message": "I like Italian food, I have about 30 minutes, and I'm a beginner cook"
}
```

**Step 4: Ask for Recipe**
```json
{
    "session_id": "flow_test",
    "message": "Great! What recipe would you suggest?"
}
```

**Step 5: Get Recipe Steps**
```json
{
    "session_id": "flow_test",
    "message": "Ok I'm ready! Tell me the first step"
}
```

After each step:
- Check `step_count` increases
- Review `current_stage` progression
- Observe how chef memory works (references previous messages)

---

## System Features Verification Checklist

- [ ] **Memory**: Chef references previous ingredients/preferences
- [ ] **Humanly Written**: Chef uses enthusiasm ("Ah!", "Brilliant!")
- [ ] **Guides Step-by-Step**: Never skips to recipe without collecting ingredients
- [ ] **Understands Context**: Responds to available food, not generic answers
- [ ] **Personality Adjustable**: Creativity levels change responses
- [ ] **Verbosity Control**: Detailed vs Concise actually changes response length
- [ ] **Session Tracking**: Different sessions have separate conversations
- [ ] **Step Counter**: Increments correctly with each message

---

## Tips for Testing

1. **Use Variables**: In Postman, create a variable for `session_id` to reuse it across requests
2. **Monitor Response Time**: Should be <5s per request (depends on LLM)
3. **Test Error Cases**: Try invalid creativity/verbosity values
4. **Long Conversations**: Test if memory stays consistent over 10+ messages
5. **Multi-Session**: Simultaneously run requests with different session_ids to verify isolation

---

## Troubleshooting

**If getting 500 error on /chat:**
- Check server logs for LLM errors
- Verify OPENAI_API_KEY is set in .env
- Check API key has available credits

**If chef doesn't remember previous messages:**
- Check conversation_history in /session endpoint
- Verify same session_id is being used

**If personality changes don't work:**
- First call /set-personality
- Then make chat requests
- Verify response in /session shows updated creativity/verbosity
