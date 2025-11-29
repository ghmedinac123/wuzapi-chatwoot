"""
main.py - Entry point de la aplicación.
"""
from src.shared.config import Settings
from src.infrastructure.logging.setup import setup_logging

# 1️⃣ Cargar configuración PRIMERO
settings = Settings()

# 2️⃣ Configurar logging con el nivel del .env
setup_logging(settings.LOG_LEVEL)

# 3️⃣ Ahora sí importar y crear app
from src.infrastructure.api.app import create_app
import logging

logger = logging.getLogger(__name__)

# Crear instancia de aplicación
app = create_app()


if __name__ == "__main__":
    """
    Ejecuta servidor Uvicorn solo si se ejecuta directamente.
    """
    import uvicorn
    
    logger.info("=" * 70)
    logger.info("🚀 Iniciando servidor Uvicorn")
    logger.info("=" * 70)
    logger.info(f"📍 Host: {settings.HOST}")
    logger.info(f"🔌 Puerto: {settings.PORT}")
    logger.info(f"📝 Log Level: {settings.LOG_LEVEL}")
    logger.info("=" * 70)
    
    uvicorn.run(
        app="main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=False,
        access_log=True,
        use_colors=True,
    )