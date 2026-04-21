from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from chef_system import (
    ChefPromptBuilder, 
    ChefStateManager, 
    ChefCreativity, 
    ChefVerbosity
)
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Chef System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# Initialize state manager
state_manager = ChefStateManager()

# ============ REQUEST/RESPONSE MODELS ============

class ChatRequest(BaseModel):
    """Chat request from user"""
    session_id: str = "default"
    message: str
    creativity: Optional[str] = "balanced"  # strict, balanced, creative
    verbosity: Optional[str] = "normal"  # concise, normal, detailed

class ChefResponse(BaseModel):
    """Chef response"""
    response: str
    session_id: str
    step_count: int
    current_stage: str
    collected_ingredients: List[str]
    message_count: int

class SessionStateResponse(BaseModel):
    """Current session state"""
    session_id: str
    step_count: int
    current_stage: str
    collected_ingredients: List[str]
    message_count: int
    creativity: str
    verbosity: str
    conversation_history: List[dict]

class PersonalityRequest(BaseModel):
    """Set chef personality"""
    session_id: str = "default"
    creativity: str = "balanced"  # strict, balanced, creative
    verbosity: str = "normal"  # concise, normal, detailed

# ============ ENDPOINTS ============

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "AI Chef System"}

@app.post("/chat")
async def chat(request: ChatRequest) -> ChefResponse:
    """
    Chat with the AI Chef
    
    - session_id: Unique session identifier
    - message: User message
    - creativity: Chef creativity level (strict/balanced/creative)
    - verbosity: Response detail level (concise/normal/detailed)
    """
    try:
        # Get or create session state
        state = state_manager.get_or_create_session(request.session_id)
        
        # Update personality if provided
        state_manager.set_personality(
            request.session_id, 
            request.creativity or "balanced",
            request.verbosity or "normal"
        )
        
        # Update step counter
        state.step_count += 1
        
        # Build prompts
        system_prompt = ChefPromptBuilder.build_system_prompt(state)
        user_context = ChefPromptBuilder.build_user_prompt(request.message, state)
        
        # Build full conversation history for context
        conversation_text = ""
        if state.conversation_history:
            conversation_text = "\n\nPrevious conversation:\n"
            for msg in state.conversation_history:
                role = "User" if msg["role"] == "user" else "Chef"
                conversation_text += f"{role}: {msg['content']}\n"
        
        # Get response from LLM with full context
        full_prompt = f"{system_prompt}\n{user_context}\n{conversation_text}\n\nRespond as the chef:"
        response = llm.invoke(full_prompt)
        chef_response = response.content
        
        # Add to conversation history
        state.add_message("user", request.message)
        state.add_message("assistant", chef_response)
        
        # Auto-extract ingredients from user message (simple approach)
        # In a real system, you'd use NER or LLM to extract these
        if state.current_stage == "ingredients":
            # Check for common ingredient keywords
            ingredient_keywords = [
                "chicken", "beef", "pork", "fish", "salmon", "tuna", "shrimp",
                "tomato", "lettuce", "onion", "garlic", "carrot", "potato", "rice",
                "oil", "butter", "salt", "pepper", "soy", "vinegar", "sauce",
                "egg", "milk", "cheese", "bread", "pasta", "beans", "lemon",
                "basil", "oregano", "thyme", "cumin", "paprika"
            ]
            msg_lower = request.message.lower()
            for keyword in ingredient_keywords:
                if keyword in msg_lower:
                    state_manager.add_ingredient(request.session_id, keyword)
        
        # Determine if stage should advance (simple heuristic)
        # In production, you'd use LLM to decide when to advance
        if state.current_stage == "greeting" and any(
            word in request.message.lower() for word in ["have", "got", "want", "cook"]
        ):
            state.current_stage = "recipe"  # Skip ingredients stage, go directly to recipe
        
        return ChefResponse(
            response=chef_response,
            session_id=request.session_id,
            step_count=state.step_count,
            current_stage=state.current_stage,
            collected_ingredients=state.collected_ingredients,
            message_count=len(state.conversation_history)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set-personality")
async def set_personality(request: PersonalityRequest):
    """Set chef personality traits"""
    try:
        state = state_manager.get_or_create_session(request.session_id)
        state_manager.set_personality(
            request.session_id,
            request.creativity,
            request.verbosity
        )
        return {
            "message": "Personality updated",
            "creativity": request.creativity,
            "verbosity": request.verbosity
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid personality setting: {str(e)}")

@app.get("/session/{session_id}")
async def get_session_state(session_id: str) -> SessionStateResponse:
    """Get current session state"""
    try:
        state = state_manager.get_or_create_session(session_id)
        return SessionStateResponse(
            session_id=session_id,
            step_count=state.step_count,
            current_stage=state.current_stage,
            collected_ingredients=state.collected_ingredients,
            message_count=len(state.conversation_history),
            creativity=state.creativity.value,
            verbosity=state.verbosity.value,
            conversation_history=state.conversation_history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset/{session_id}")
async def reset_session(session_id: str):
    """Reset a session"""
    if session_id in state_manager.sessions:
        del state_manager.sessions[session_id]
    return {"message": f"Session {session_id} reset"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
