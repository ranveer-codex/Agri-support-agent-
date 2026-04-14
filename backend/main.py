from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import logging
import time
import random

# =============================
# INITIAL SETUP
# =============================

app = FastAPI(title="Agrochemical Support Agent", version="2.0")

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
rate_limit_store = {}

# =============================
# PRODUCT DATABASE
# =============================

PRODUCTS = {
    "pest": [
        {
            "name": "AgroAsian PestX",
            "usage": "2ml per liter of water",
            "target": "aphids, caterpillars",
            "crop": ["wheat", "rice"]
        }
    ],
    "fungus": [
        {
            "name": "AgroAsian FungiStop",
            "usage": "1.5ml per liter",
            "target": "leaf spots, mildew",
            "crop": ["wheat"]
        }
    ]
}

# =============================
# REQUEST MODEL
# =============================

class ChatRequest(BaseModel):
    message: str
    conversation_id: str

# =============================
# SECURITY LAYER
# =============================

def sanitize_input(text: str):
    blocked = [
        "ignore previous",
        "system prompt",
        "reveal",
        "bypass",
        "act as admin"
    ]

    lower = text.lower()

    if any(b in lower for b in blocked):
        logger.warning(f"[BLOCKED] {text}")
        return False

    return True


def check_rate_limit(user_id: str):
    now = time.time()

    if user_id in rate_limit_store:
        if now - rate_limit_store[user_id] < 1:
            return False

    rate_limit_store[user_id] = now
    return True

# =============================
# SMART ENGINE
# =============================

FOLLOW_UPS = [
    "Let me know if you'd like product recommendations.",
    "I can suggest the best products for this issue.",
    None
]

def detect_crop(msg):
    if "rice" in msg:
        return "rice"
    if "wheat" in msg:
        return "wheat"
    if "cotton" in msg:
        return "cotton"
    return "crop"


def generate_reply(msg):
    msg_lower = msg.lower()
    crop = detect_crop(msg_lower)

    # Pest
    if any(w in msg_lower for w in ["pest", "insect", "bug", "worms"]):
        return (
            f"Your {crop} crop may be affected by pest activity.\n\n"
            "We recommend AgroAsian PestX for effective control.\n"
            "Usage: 2ml per liter of water.\n\n"
            "Inspect leaves regularly and act early to prevent crop loss."
        )

    # Fungus
    if any(w in msg_lower for w in ["fungus", "fungal", "spots", "disease"]):
        return (
            f"Your {crop} crop may be facing a fungal issue.\n\n"
            "We recommend AgroAsian FungiStop.\n"
            "Usage: 1.5ml per liter.\n\n"
            "Ensure proper airflow and avoid excess moisture."
        )

    return (
        "I understand you're facing a crop issue.\n"
        "Please share more details so I can guide you better."
    )


def get_recommendations(msg):
    msg = msg.lower()
    results = []

    for key in PRODUCTS:
        if key in msg:
            results.extend(PRODUCTS[key])

    return results[:3]

# =============================
# CONVERSATION MANAGER
# =============================

class ConversationManager:
    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.conversation_id = f"{customer_id}_{int(time.time())}"
        self.messages = []

    def process(self, message):
        self.messages.append({"role": "user", "content": message})

        base = generate_reply(message)
        recs = get_recommendations(message)

        follow = (
            "I've also found some products that might help."
            if recs else random.choice(FOLLOW_UPS)
        )

        final = base if not follow else f"{base}\n\n{follow}"

        self.messages.append({"role": "assistant", "content": final})
        return final, recs

# =============================
# ROUTES
# =============================

@app.get("/")
def root():
    return {"status": "API running"}

@app.post("/api/conversations")
def create_conversation(customer_id: str):

    if len(conversations) >= MAX_CONVERSATIONS:
        conversations.pop(next(iter(conversations)))

    conv = ConversationManager(customer_id)
    conversations[conv.conversation_id] = conv

    logger.info(f"[NEW] {conv.conversation_id}")

    return {"conversation_id": conv.conversation_id}


@app.post("/api/chat")
def chat(req: ChatRequest):

    # 🔒 Security checks
    if not sanitize_input(req.message):
        return {
            "reply": "Sorry, I can't process that request.",
            "recommendations": []
        }

    if not check_rate_limit(req.conversation_id):
        return {
            "reply": "You're sending messages too quickly.",
            "recommendations": []
        }

    if req.conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = conversations[req.conversation_id]

    try:
        reply, recs = conv.process(req.message)

        logger.info(f"[CHAT] {req.conversation_id}: {req.message}")

        return {
            "reply": reply,
            "recommendations": recs
        }

    except Exception as e:
        logger.error(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================
# RUN
# =============================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)+
