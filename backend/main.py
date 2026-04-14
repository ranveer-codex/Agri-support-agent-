from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import time
import random

# =============================
# INITIAL SETUP
# =============================

app = FastAPI(title="Agrochemical Support Agent", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agri-support-agent-2r3iazxo0-sastacaptainamericas-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_CONVERSATIONS = 500
conversations = {}
rate_limit_store = {}
leads = []

# =============================
# PRODUCT DATABASE
# =============================

PRODUCTS = {
    "pest": [
        {
            "name": "AgroAsian PestX",
            "usage": "2ml per liter of water",
            "target": "aphids, caterpillars",
        }
    ],
    "fungus": [
        {
            "name": "AgroAsian FungiStop",
            "usage": "1.5ml per liter",
            "target": "leaf spots, mildew",
        }
    ]
}

# =============================
# REQUEST MODELS
# =============================

class ChatRequest(BaseModel):
    message: str
    conversation_id: str


class LeadRequest(BaseModel):
    name: str
    phone: str
    message: str
    product: str

# =============================
# SECURITY & VALIDATION
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
        logger.warning(f"[BLOCKED INPUT] {text}")
        return False

    return True


def validate_input(text: str):
    if not text.strip():
        return False
    if len(text) > 500:
        return False
    return True


def validate_phone(phone: str):
    return phone.isdigit() and len(phone) == 10


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
    return "crop"


def generate_reply(msg):
    msg = msg.lower()
    crop = detect_crop(msg)

    if any(w in msg for w in ["pest", "insect", "bug", "worms"]):
        return (
            f"Your {crop} crop may be affected by pest activity.\n\n"
            "We recommend AgroAsian PestX.\n"
            "Usage: 2ml per liter of water.\n\n"
            "Inspect leaves early to prevent spread."
        )

    if any(w in msg for w in ["fungus", "fungal", "spots"]):
        return (
            f"Your {crop} crop may be facing fungal infection.\n\n"
            "Use AgroAsian FungiStop.\n"
            "Usage: 1.5ml per liter.\n\n"
            "Avoid excess moisture."
        )

    return "Please provide more details about your crop issue."


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

        reply = generate_reply(message)
        recs = get_recommendations(message)

        follow = (
            "I've also found some products that might help."
            if recs else random.choice(FOLLOW_UPS)
        )

        final = reply if not follow else f"{reply}\n\n{follow}"

        self.messages.append({"role": "assistant", "content": final})
        return final, recs

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
def create_conversation(customer_id: str):

    if len(conversations) >= MAX_CONVERSATIONS:
        conversations.pop(next(iter(conversations)))

    conv = ConversationManager(customer_id)
    conversations[conv.conversation_id] = conv

    logger.info(f"[NEW CONVERSATION] {conv.conversation_id}")
    return {"conversation_id": conv.conversation_id}


@app.post("/api/chat")
def chat(req: ChatRequest):

    # VALIDATION
    if not validate_input(req.message):
        raise HTTPException(status_code=400, detail="Invalid message")

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


@app.post("/api/lead")
def capture_lead(req: LeadRequest):

    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Name required")

    if not validate_phone(req.phone):
        raise HTTPException(status_code=400, detail="Invalid phone number")

    if len(req.message) > 500:
        raise HTTPException(status_code=400, detail="Message too long")

    lead = {
        "name": req.name,
        "phone": req.phone,
        "message": req.message,
        "product": req.product,
        "timestamp": time.time()
    }

    leads.append(lead)

    logger.info(f"[LEAD CAPTURED] {lead}")

    return {
        "status": "success",
        "message": "Lead captured successfully"
    }


@app.get("/api/leads")
def get_leads():
    return leads
