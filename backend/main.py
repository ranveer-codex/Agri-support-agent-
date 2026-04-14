from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import logging
import os
import json
from dotenv import load_dotenv

# =============================
# INITIAL SETUP
# =============================

load_dotenv()

app = FastAPI(title="Agrochemical Support Agent", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_CONVERSATIONS = 500
conversations = {}

# =============================
# AI SETUP
# =============================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

try:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except Exception as e:
    logger.warning(f"Anthropic init failed: {e}")
    client = None

SYSTEM_PROMPT = """
You are an agrochemical support assistant.
Help with pest control, fertilizers, crop diseases, and farming practices.
Give clear, practical advice and suggest products when useful.
"""

# =============================
# PRODUCT DATABASE
# =============================

PRODUCTS = {
    "pest": [{"name": "PestGuard Pro"}, {"name": "BugShield"}],
    "fertilizer": [{"name": "NutriMax"}, {"name": "GrowthBoost"}],
    "fungus": [{"name": "FungaStop"}],
    "weed": [{"name": "WeedKill"}],
}

# =============================
# MODELS
# =============================

class ChatRequest(BaseModel):
    message: str
    conversation_id: str

# =============================
# CONVERSATION MANAGER
# =============================

class ConversationManager:
    def __init__(self, customer_id: str, channel: str = "web"):
        self.customer_id = customer_id
        self.channel = channel
        self.conversation_id = f"{customer_id}_{int(datetime.now().timestamp())}"
        self.messages = []
        self.created_at = datetime.now()

    def add_message(self, role, content):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_claude_response(self, user_message: str):
        self.add_message("user", user_message)

        if client:
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": m["role"], "content": m["content"]} for m in self.messages]
                )

                text = response.content[0].text
                self.add_message("assistant", text)
                return text

            except Exception as e:
                logger.error(f"Claude API error: {e}")

        # fallback (safe)
        fallback = f"You said: {user_message}"
        self.add_message("assistant", fallback)
        return fallback

    def get_recommendations(self, user_message):
        msg = user_message.lower()
        recs = []

        for keyword, items in PRODUCTS.items():
            if keyword in msg:
                recs.extend(items)

        return recs[:3]

# =============================
# ROUTES
# =============================

@app.get("/")
def root():
    return {"status": "API running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/conversations")
def create_conversation(customer_id: str, channel: str = "web"):
    try:
        # Prevent memory overflow
        if len(conversations) >= MAX_CONVERSATIONS:
            oldest = next(iter(conversations))
            del conversations[oldest]

        conv = ConversationManager(customer_id, channel)
        conversations[conv.conversation_id] = conv

        logger.info(f"[NEW] {conv.conversation_id}")

        return {
            "conversation_id": conv.conversation_id,
            "customer_id": customer_id,
            "channel": channel
        }

    except Exception as e:
        logger.error(f"Conversation error: {e}")
        raise HTTPException(status_code=500, detail="Conversation creation failed")

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        if not req.message or not req.message.strip():
            raise HTTPException(status_code=400, detail="Empty message")

        if req.conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conv = conversations[req.conversation_id]

        logger.info(f"[CHAT] {req.conversation_id}: {req.message}")

        try:
            reply = conv.get_claude_response(req.message)
        except Exception as e:
            logger.error(f"AI failure: {e}")
            reply = f"You said: {req.message}"

        recs = conv.get_recommendations(req.message)

        return {
            "reply": reply,
            "recommendations": recs
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================
# WEBSOCKET
# =============================

@app.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    await websocket.accept()

    if conversation_id not in conversations:
        await websocket.send_json({"error": "Conversation not found"})
        await websocket.close()
        return

    conv = conversations[conversation_id]

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            msg = payload.get("message", "")

            if not msg.strip():
                await websocket.send_json({"error": "Empty message"})
                continue

            try:
                reply = conv.get_claude_response(msg)
            except Exception as e:
                logger.error(f"AI error: {e}")
                reply = f"You said: {msg}"

            recs = conv.get_recommendations(msg)

            await websocket.send_json({
                "reply": reply,
                "recommendations": recs
            })

    except WebSocketDisconnect:
        logger.info(f"Disconnected: {conversation_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": "Internal server error"})
        await websocket.close()

# =============================
# RUN
# =============================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
