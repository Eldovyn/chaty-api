from dataclasses import dataclass
from datetime import datetime

@dataclass
class AccessTokenSchema:
    access_token: str
    created_at: datetime
