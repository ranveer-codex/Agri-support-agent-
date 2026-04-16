import time
import random
from storage.memory_store import conversations
from security.logger import log_security_event

PRODUCTS = {
    "pest": [
        {
            "name": "AgroAsian PestX",
            "usage": "2ml per liter",
            "target": "aphids"
        }
    ]
}

FOLLOW_UPS = [
    "Let me know if you'd like product recommendations.",
    None
]


class ConversationManager:
    def __init__(self, customer_id):
        self.conversation_id = f"{customer_id}_{int(time.time())}"
        self.messages = []

    def process(self, message):
        self.messages.append({"role": "user", "content": message})

        reply = "Based on your issue, we recommend AgroAsian PestX."
        recs = PRODUCTS.get("pest", [])

        final = f"{reply}\n\n{random.choice(FOLLOW_UPS) or ''}"

        self.messages.append({"role": "assistant", "content": final})

        return final, recs


def create_conversation(customer_id):
    conv = ConversationManager(customer_id)
    conversations[conv.conversation_id] = conv
    return conv.conversation_id


def process_chat(conversation_id, message):
    conv = conversations[conversation_id]
    return conv.process(message)
