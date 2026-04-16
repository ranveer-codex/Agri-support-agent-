from .logger import log_security_event

BLOCKED_PATTERNS = [
    "ignore previous",
    "system prompt",
    "reveal",
    "bypass",
    "act as admin"
]

SUSPICIOUS_KEYWORDS = ["hack", "exploit", "bypass"]


def sanitize_input(text: str):
    lower = text.lower()

    if any(b in lower for b in BLOCKED_PATTERNS):
        log_security_event("PROMPT_INJECTION", text)
        return False

    return True


def detect_suspicious(text: str):
    if any(word in text.lower() for word in SUSPICIOUS_KEYWORDS):
        log_security_event("SUSPICIOUS_ACTIVITY", text)


def validate_input(text: str):
    if not text.strip():
        return False
    if len(text) > 500:
        return False
    return True


def validate_phone(phone: str):
    return phone.isdigit() and len(phone) == 10
