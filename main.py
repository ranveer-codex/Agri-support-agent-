from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Agrochemical Support Agent", version="0.1.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Try to import Anthropic, but allow graceful fallback
try:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except Exception as e:
    logger.warning(f"Anthropic client initialization failed: {e}. Using mock responses.")
    client = None

# In-memory storage
conversations = {}

# System prompts
SYSTEM_PROMPT = """You are a helpful customer support agent for an agrochemical company. 
You provide product knowledge, answer questions about pest control, fertilizers, and crop management.
Be friendly, professional, and educational. When relevant, suggest products based on customer needs."""

# Product database (keyword-based matching)
PRODUCTS = {
    "pest": [
        {"name": "PestGuard Pro", "type": "Insecticide", "use": "Controls common crop pests"},
        {"name": "BugShield", "type": "Organic Insecticide", "use": "Natural pest control solution"},
    ],
    "fertilizer": [
        {"name": "NutriMax", "type": "NPK Fertilizer", "use": "Balanced nutrient blend"},
        {"name": "GrowthBoost", "type": "Micronutrient Mix", "use": "Enhances crop yield"},
    ],
    "fungus": [
        {"name": "FungaStop", "type": "Fungicide", "use": "Prevents fungal diseases"},
        {"name": "MoldBlock", "type": "Systemic Fungicide", "use": "Protects against mold and mildew"},
    ],
    "weed": [
        {"name": "WeedKill", "type": "Herbicide", "use": "Selective weed control"},
        {"name": "CropShield", "type": "Herbicide", "use": "Pre-emergent weed control"},
    ],
}


class ConversationManager:
    def __init__(self, customer_id: str, channel: str = "web"):
        self.customer_id = customer_id
        self.channel = channel
        self.conversation_id = f"{customer_id}_{channel}_{datetime.now().isoformat()}"
        self.messages = []
        self.created_at = datetime.now()

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_claude_response(self, user_message: str) -> str:
        """Get response from Claude API or use mock"""
        self.add_message("user", user_message)
        
        # Try real Claude API first
        if client:
            try:
                messages_for_claude = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in self.messages
                ]
                
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=messages_for_claude
                )
                assistant_message = response.content[0].text
                self.add_message("assistant", assistant_message)
                return assistant_message
            except Exception as e:
                logger.error(f"Claude API error: {e}. Falling back to mock response.")
        
        # Fallback to mock response
        assistant_message = self._get_mock_response(user_message)
        self.add_message("assistant", assistant_message)
        return assistant_message

    def _get_mock_response(self, user_message: str) -> str:
        """Generate mock response for testing without API credits"""
        user_lower = user_message.lower()
        
        if any(word in user_lower for word in ["hello", "hi", "hey", "start"]):
            return "Hello! Welcome to our Agrochemical Support Agent. I'm here to help you with questions about pest control, fertilizers, crop management, and product recommendations. What can I help you with today?"
        
        elif any(word in user_lower for word in ["pest", "insect", "bug"]):
            return "Pests can significantly impact crop yield. We have several solutions:\n\n1. **PestGuard Pro** - A comprehensive insecticide for common crop pests\n2. **BugShield** - An organic alternative for natural pest control\n\nWhat type of pests are you dealing with? I can provide more specific recommendations."
        
        elif any(word in user_lower for word in ["fertilizer", "nutrient", "nitrogen"]):
            return "Good question about fertilizers! Proper nutrition is key to healthy crops.\n\n**Our recommendations:**\n- **NutriMax** - Balanced NPK formula for most crops\n- **GrowthBoost** - Micronutrient mix for enhanced yield\n\nWhat's your primary crop? I can suggest the best option."
        
        elif any(word in user_lower for word in ["fungus", "disease", "mold", "mildew"]):
            return "Fungal diseases can be managed with proper treatment. We recommend:\n\n- **FungaStop** - Effective fungicide for disease prevention\n- **MoldBlock** - Systemic fungicide for mold and mildew control\n\nWhen did you first notice the issue?"
        
        elif any(word in user_lower for word in ["weed", "grass"]):
            return "Weed management is crucial for crop success. Our options:\n\n- **WeedKill** - Selective herbicide for targeted weed control\n- **CropShield** - Pre-emergent for preventing weed growth\n\nWhich stage of growth is your crop in?"
        
        else:
            return "That's an interesting question about agricultural practices. Could you provide more details? For example, are you dealing with pest management, fertilization, disease control, or weed management? I can give more targeted advice with that information."

    def get_recommendations(self, user_message: str) -> list:
        """Match products based on keywords in user message"""
        user_lower = user_message.lower()
        recommendations = []
        
        for keyword, products in PRODUCTS.items():
            if keyword in user_lower:
                recommendations.extend(products)
        
        return recommendations[:3]  # Return top 3 recommendations


# HTTP Endpoints
@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/conversations")
async def create_conversation(customer_id: str, channel: str = "web"):
    try:
        conv_manager = ConversationManager(customer_id, channel)
        conversations[conv_manager.conversation_id] = conv_manager
        return {
            "conversation_id": conv_manager.conversation_id,
            "customer_id": customer_id,
            "channel": channel
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv = conversations[conversation_id]
    return {
        "conversation_id": conversation_id,
        "customer_id": conv.customer_id,
        "channel": conv.channel,
        "messages": conv.messages,
        "created_at": conv.created_at.isoformat()
    }


# WebSocket Endpoint
@app.websocket("/ws/chat/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    
    if conversation_id not in conversations:
        await websocket.send_json({"type": "error", "message": "Conversation not found"})
        await websocket.close()
        return
    
    conv = conversations[conversation_id]
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            
            if not user_message.strip():
                continue
            
            # Get recommendations based on keywords
            recommendations = conv.get_recommendations(user_message)
            
            # Get Claude response (or mock)
            response = conv.get_claude_response(user_message)
            
            # Send response back to client
            await websocket.send_json({
                "type": "message",
                "role": "assistant",
                "content": response,
                "recommendations": recommendations
            })
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
