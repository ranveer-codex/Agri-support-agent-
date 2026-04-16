from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, LeadRequest
from services.chat_service import create_conversation, process_chat
from services.lead_service import capture_lead
from storage.memory_store import conversations
from security.security import (
    sanitize_input,
    validate_input,
    validate_phone,
    detect_suspicious
)
from security.logger import get_security_logs, log_security_event

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agri-support-agent-2r3iazxo0-sastacaptainamericas-projects.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "API running"}

@app.get("/api/security-events")
def security_events():
    return get_security_logs()

@app.post("/api/conversations")
def create_conv(customer_id: str):
    return {"conversation_id": create_conversation(customer_id)}

@app.post("/api/chat")
def chat(req: ChatRequest):

    if not validate_input(req.message):
        raise HTTPException(400, "Invalid message")

    if not sanitize_input(req.message):
        return {"reply": "Blocked request", "recommendations": []}

    detect_suspicious(req.message)

    if req.conversation_id not in conversations:
        raise HTTPException(404, "Conversation not found")

    try:
        reply, recs = process_chat(req.conversation_id, req.message)
        return {"reply": reply, "recommendations": recs}

    except Exception as e:
        log_security_event("ERROR", str(e))
        raise HTTPException(500, "Internal error")

@app.post("/api/lead")
def lead(req: LeadRequest):

    if not validate_phone(req.phone):
        raise HTTPException(400, "Invalid phone")

    lead = capture_lead(req)
    return {"status": "success", "lead": lead}
