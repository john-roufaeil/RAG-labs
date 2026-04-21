"""
AI Chef System - Core business logic for the chef assistant
"""
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field

class ChefCreativity(Enum):
    """Chef creativity level"""
    STRICT = "strict"  # Recipes only, no improvisation
    BALANCED = "balanced"  # Mix of traditional and some creativity
    CREATIVE = "creative"  # Free-flowing, experimental suggestions

class ChefVerbosity(Enum):
    """Chef verbosity level"""
    CONCISE = "concise"  # Short, direct answers
    NORMAL = "normal"  # Normal conversation
    DETAILED = "detailed"  # Detailed explanations

@dataclass
class ChefState:
    """Track conversation state"""
    session_id: str
    step_count: int = 0
    conversation_history: List[dict] = field(default_factory=list)
    collected_ingredients: List[str] = field(default_factory=list)
    current_stage: str = "greeting"  # greeting -> ingredients -> recipe -> done
    creativity: ChefCreativity = ChefCreativity.BALANCED
    verbosity: ChefVerbosity = ChefVerbosity.NORMAL
    
    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.conversation_history.append({"role": role, "content": content})
        
    def get_history_text(self) -> str:
        """Get formatted conversation history"""
        if not self.conversation_history:
            return "No prior conversation"
        history = []
        for msg in self.conversation_history[-6:]:  # Last 6 messages for context
            role = "Chef" if msg["role"] == "assistant" else "You"
            history.append(f"{role}: {msg['content']}")
        return "\n".join(history)

class ChefPromptBuilder:
    """Build prompts for the chef based on state"""
    
    @staticmethod
    def build_system_prompt(state: ChefState) -> str:
        """Build the system prompt for the chef"""
        creativity_desc = {
            ChefCreativity.STRICT: "Stick to classic, proven recipes. Be very traditional.",
            ChefCreativity.BALANCED: "Mix traditional recipes with some modern twists.",
            ChefCreativity.CREATIVE: "Be adventurous and experimental. Suggest creative combinations.",
        }
        
        verbosity_desc = {
            ChefVerbosity.CONCISE: "Keep responses SHORT and direct (1-2 sentences max)",
            ChefVerbosity.NORMAL: "Use normal conversational length responses",
            ChefVerbosity.DETAILED: "Provide detailed explanations and background info",
        }
        
        system_prompt = f"""You are a professional, friendly chef 👨‍🍳 who helps people cook amazing meals.

PERSONALITY:
- Speak like a real chef: passionate, encouraging, use food terminology naturally
- Use exclamations and enthusiasm: "Ah!", "Wonderful!", "Brilliant!"
- Call users "friend", "mate", or use casual friendly language
- Show genuine interest in what they want to cook

CREATIVITY LEVEL: {creativity_desc[state.creativity]}

RESPONSE STYLE: {verbosity_desc[state.verbosity]}

CURRENT CONVERSATION STAGE: {state.current_stage}

STAGE RULES:
1. greeting: Welcome them warmly, ask what ingredients they have
2. recipe: When user provides ingredients, IMMEDIATELY give them a complete recipe with step-by-step instructions. DO NOT ask for more ingredients. Use what they gave you.
3. done: Help with follow-up questions or offer another recipe

IMPORTANT RULES:
- When user gives ingredients, provide a FULL RECIPE with ALL STEPS immediately
- NEVER ask "Do you have any other ingredients?"
- NEVER skip to recipe without having ingredients
- List all steps clearly numbered (Step 1, Step 2, etc.)
- Be encouraging and positive about their dish
- If user seems lost, guide them back to the current step
- Step count: {state.step_count}

Previous conversation:
{state.get_history_text()}
"""
        return system_prompt
    
    @staticmethod
    def build_user_prompt(user_input: str, state: ChefState) -> str:
        """Build the final prompt to send to LLM"""
        current_ingredients = ", ".join(state.collected_ingredients) if state.collected_ingredients else "none yet"
        
        context = f"""
Current ingredients collected: {current_ingredients}
Stage: {state.current_stage}
User message: {user_input}

If user provided ingredients in their message, extract them and provide a complete recipe immediately with numbered steps.
Format the recipe clearly with ingredients list first, then numbered cooking steps.
"""
        return context

class ChefStateManager:
    """Manage chef states across sessions"""
    def __init__(self):
        self.sessions = {}
    
    def get_or_create_session(self, session_id: str) -> ChefState:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ChefState(session_id=session_id)
        return self.sessions[session_id]
    
    def update_stage(self, session_id: str, new_stage: str):
        """Update conversation stage"""
        state = self.get_or_create_session(session_id)
        state.current_stage = new_stage
    
    def add_ingredient(self, session_id: str, ingredient: str):
        """Add ingredient to session"""
        state = self.get_or_create_session(session_id)
        if ingredient.lower() not in [i.lower() for i in state.collected_ingredients]:
            state.collected_ingredients.append(ingredient)
    
    def set_personality(self, session_id: str, creativity: str, verbosity: str):
        """Set chef personality"""
        state = self.get_or_create_session(session_id)
        try:
            state.creativity = ChefCreativity(creativity)
            state.verbosity = ChefVerbosity(verbosity)
        except ValueError:
            pass

# Global state manager
state_manager = ChefStateManager()
