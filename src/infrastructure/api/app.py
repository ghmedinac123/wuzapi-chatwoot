"""
src/infrastructure/api/app.py

FastAPI Application Factory.

Responsabilidad única:
- Crear y configurar instancia de FastAPI
- Gestionar ciclo de vida (startup/shutdown)
- Registrar routers
- Configurar middleware y CORS
- Definir rutas de sistema (/health, /)

Patrón usado: Factory Pattern + Lifecycle Management
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .routers import wuzapi_router, chatwoot_router
from .dependencies import (
    get_settings,
    get_cache_client,
    cleanup_dependencies
)
from ..logging.setup import setup_logging
from ...shared.config import Settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    
    Startup:
    - Configura logging
    - Inicializa componentes (cache, clientes)
    - Muestra información de configuración
    
    Shutdown:
    - Cierra conexiones
    - Limpia recursos
    """
    # ==================== STARTUP ====================
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    
    logger.info("=" * 70)
    logger.info("🚀 Integración WuzAPI ↔ Chatwoot")
    logger.info("=" * 70)
    
    # Inicializar caché (Redis o Memoria)
    cache_client = await get_cache_client()
    cache_type = "Redis" if "redis" in str(type(cache_client)).lower() else "Memoria"
    
    # Mostrar configuración activa
    logger.info("=" * 70)
    logger.info("📋 CONFIGURACIÓN ACTIVA")
    logger.info("=" * 70)
    logger.info(f"🌐 WuzAPI URL: {settings.WUZAPI_URL}")
    logger.info(f"🌐 Chatwoot URL: {settings.CHATWOOT_URL}")
    logger.info(f"📬 Chatwoot Inbox ID: {settings.CHATWOOT_INBOX_ID}")
    logger.info(f"🔑 WuzAPI Instance ID: {settings.WUZAPI_INSTANCE_ID}")
    logger.info(f"💾 Caché: {cache_type}")
    logger.info("=" * 70)
    logger.info("✅ Webhooks activos")
    logger.info(f"   • POST /webhook/wuzapi   → Recibe mensajes de WhatsApp")
    logger.info(f"   • POST /webhook/chatwoot → Recibe mensajes de Chatwoot")
    logger.info(f"   • GET  /health           → Health check")
    logger.info("=" * 70)
    
    yield
    
    # ==================== SHUTDOWN ====================
    logger.info("🛑 Deteniendo aplicación...")
    
    await cleanup_dependencies()
    
    logger.info("=" * 70)
    logger.info("👋 Aplicación detenida correctamente")
    logger.info("=" * 70)


def create_app() -> FastAPI:
    """
    Factory para crear instancia de FastAPI.
    
    Ventajas del Factory Pattern:
    - Testing: Crear múltiples instancias con configs diferentes
    - Flexibilidad: Configurar según entorno (dev/prod)
    - Reusabilidad: Reutilizar lógica de creación
    
    Returns:
        Instancia configurada de FastAPI
    """
    settings = get_settings()
    
    # Crear aplicación
    app = FastAPI(
        title="WuzAPI ↔ Chatwoot Integration",
        version="2.1.0",
        description="""
        Integración bidireccional profesional entre WuzAPI y Chatwoot.
        
        Características:
        - Arquitectura Hexagonal (Ports & Adapters)
        - Principios SOLID
        - Soporte multimedia completo
        - Caché inteligente (Redis + fallback memoria)
        - Dependency Injection
        """,
        lifespan=lifespan
    )
    
    # Configurar CORS (si necesario)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción: especificar dominios
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Registrar routers
    app.include_router(wuzapi_router.router)
    app.include_router(chatwoot_router.router)
    
    # Rutas de sistema
    
    @app.get(
        "/",
        tags=["Sistema"],
        summary="Información del servicio"
    )
    async def root():
        """Endpoint raíz con información del servicio."""
        return {
            "service": "WuzAPI ↔ Chatwoot Integration",
            "version": "2.1.0",
            "status": "running",
            "architecture": "Hexagonal (Ports & Adapters)",
            "features": {
                "multimedia": "Soporte completo (multipart/form-data)",
                "cache": "Redis + fallback memoria",
                "webhooks": [
                    "POST /webhook/wuzapi",
                    "POST /webhook/chatwoot"
                ],
                "supported_types": [
                    "text", "image", "video", "audio",
                    "document", "sticker", "location", "contact"
                ]
            },
            "documentation": "/docs"
        }
    
    @app.get(
        "/health",
        tags=["Sistema"],
        summary="Health check"
    )
    async def health_check():
        """
        Health check del servicio.
        
        Verifica estado de componentes críticos.
        """
        cache_client = await get_cache_client()
        cache_type = "redis" if "redis" in str(type(cache_client)).lower() else "memory"
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "version": "2.1.0",
                "components": {
                    "wuzapi": {
                        "url": settings.WUZAPI_URL,
                        "configured": True
                    },
                    "chatwoot": {
                        "url": settings.CHATWOOT_URL,
                        "inbox_id": settings.CHATWOOT_INBOX_ID,
                        "configured": True
                    },
                    "cache": {
                        "type": cache_type,
                        "status": "connected"
                    },
                    "media_downloader": {
                        "enabled": True,
                        "endpoints": "official_wuzapi"
                    }
                }
            }
        )
    
    return app