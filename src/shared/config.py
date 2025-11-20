"""
Configuración 1:1 - Adaptada al nuevo formato de WuzAPI
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración centralizada 1:1"""
    
    # Servidor
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    BACKEND_URL: str = "integracion.wuzapi.torneofututel.com"
    
    # Chatwoot
    CHATWOOT_URL: str
    CHATWOOT_API_KEY: str
    CHATWOOT_ACCOUNT_ID: str = "2"
    CHATWOOT_INBOX_ID: str
    
    # WuzAPI
    WUZAPI_URL: str
    WUZAPI_USER_TOKEN: str
    WUZAPI_INSTANCE_TOKEN: str  # Token que identifica la instancia
    WUZAPI_INSTANCE_ID: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    USE_CELERY: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"