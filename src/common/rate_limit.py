"""Rate limiting configuration."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter with IP-based key function
limiter = Limiter(key_func=get_remote_address)

# Rate limit constants
DEFAULT_RATE = "100/minute"
QUERY_RATE = "30/minute"
CONVERSATION_RATE = "60/minute"
