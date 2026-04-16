import time
import logging

logger = logging.getLogger(__name__)

security_logs = []

def log_security_event(event_type, details):
    event = {
        "timestamp": time.time(),
        "type": event_type,
        "details": details
    }

    security_logs.append(event)
    logger.warning(f"[SECURITY] {event}")

def get_security_logs():
    return security_logs
