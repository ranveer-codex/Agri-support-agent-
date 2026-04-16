from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    conversation_id: str


class LeadRequest(BaseModel):
    name: str
    phone: str
    message: str
    product: str
