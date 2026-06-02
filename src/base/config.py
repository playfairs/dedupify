import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    client_id: str
    client_secret: str
    redirect_url: str
    fuzzy_threshold: int = 85
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        redirect_url = os.getenv("REDIRECT_URL", "http://localhost:8888/callback")

        if not client_id:
            raise ValueError("CLIENT_ID environment variable is required")
        if not client_secret:
            raise ValueError("CLIENT_SECRET environment variable is required")

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_url=redirect_url,
        )

    @classmethod
    def with_options(
        cls,
        fuzzy_threshold: Optional[int] = None,
        log_level: Optional[str] = None,
    ) -> "Config":
        config = cls.from_env()
        if fuzzy_threshold is not None:
            config.fuzzy_threshold = fuzzy_threshold
        if log_level is not None:
            config.log_level = log_level
        return config
