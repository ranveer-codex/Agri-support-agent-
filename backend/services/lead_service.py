import time
from storage.memory_store import leads
from security.logger import log_security_event

def capture_lead(data):
    lead = {
        "name": data.name,
        "phone": data.phone,
        "message": data.message,
        "product": data.product,
        "timestamp": time.time()
    }

    leads.append(lead)
    log_security_event("LEAD_CAPTURED", lead)

    return lead
