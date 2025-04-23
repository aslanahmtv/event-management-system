"""Configuration to use in the app"""

import os
from typing import List, Optional

from pydantic import Field, validator, BaseSettings


class CommonSettings(BaseSettings):
    APP_NAME: str = Field(default="Event-service")
    DEBUG_MODE: bool = Field(default=True)
    API_VERSION: str = Field(default="v1")
    API_PREFIX: str = Field(default="/api")


class DatabaseSettings(BaseSettings):
    MONGODB_URL: str = Field(default="mongodb://localhost:27017")
    DB_NAME: str = Field(default="event-service")
    REPOSITORY_NAME: str = Field(default="MongoRepo")


class CORSSettings(BaseSettings):
    FRONTEND_URL: str = Field(default="http://localhost:3000")
    DEBUG_FRONT_URLS: List[str] = []


class JWTSettings(BaseSettings):
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    @validator("SECRET_KEY")
    def secret_key_must_be_strong(cls, v):
        if v == "your-secret-key-change-in-production" and not CommonSettings().DEBUG_MODE:
            raise ValueError("Default SECRET_KEY not allowed in production")
        return v


class MessageBrokerSettings(BaseSettings):
    BROKER_URL: str = Field(default="amqp://guest:guest@localhost:5672/")
    EXCHANGE_NAME: str = Field(default="event_exchange")
    QUEUE_NAME: str = Field(default="event_queue")
    ROUTING_KEY: str = Field(default="event.#")

    MAX_RETRIES: int = Field(default=5)
    RETRY_DELAY: int = Field(default=5)


class WebSocketSettings(BaseSettings):
    WS_URL: str = Field(default="/ws")
    PING_INTERVAL: int = Field(default=30)


class RateLimitSettings(BaseSettings):
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    LOGIN_RATE_LIMIT: str = Field(default="5/minute")


class Settings(
    CommonSettings,
    DatabaseSettings,
    CORSSettings,
    JWTSettings,
    MessageBrokerSettings,
    WebSocketSettings,
    RateLimitSettings,
):
    class Config:
        env_file = os.environ.get("ENV_FILE", ".env")
        env_file_encoding = "utf-8"


settings = Settings()