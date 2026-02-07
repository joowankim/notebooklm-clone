"""Rate limiting configuration."""

import slowapi
import slowapi.util

# Create limiter with IP-based key function
limiter = slowapi.Limiter(key_func=slowapi.util.get_remote_address)

# Rate limit constants
DEFAULT_RATE = "100/minute"
QUERY_RATE = "30/minute"
CONVERSATION_RATE = "60/minute"
