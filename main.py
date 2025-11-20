"""
main.py

Entry point de la aplicación.

Responsabilidades:
- Importar factory de aplicación (create_app)
- Configurar y ejecutar servidor Uvicorn
- Punto de entrada para systemd/docker

Arquitectura:
- Usa Factory Pattern (create_app) en lugar de importar app global
- Permite múltiples instancias para testing
- Configuración centralizada vía Settings

Uso:
  Desarrollo:
    python main.py
  
  Producción:
    uvicorn main:app --host 0.0.0.0 --port 8789
  
  Systemd:
    uv run python main.py
"""
import logging
from src.infrastructure.api.app import create_app
from src.shared.config import Settings

# Configurar logging básico antes de crear app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Crear instancia de aplicación usando Factory Pattern
# Esto permite:
# - Testing: crear múltiples instancias con configuraciones diferentes
# - Flexibilidad: modificar configuración sin cambiar código
# - Limpieza: toda la lógica de inicialización está en app.py
app = create_app()


if __name__ == "__main__":
    """
    Ejecuta servidor Uvicorn solo si se ejecuta directamente.
    
    En producción con systemd:
      ExecStart=uv run python main.py
    
    En producción con uvicorn directo:
      ExecStart=uvicorn main:app --host 0.0.0.0 --port 8789
    """
    import uvicorn
    
    settings = Settings()
    
    # Configuración de Uvicorn
    uvicorn_config = {
        "app": "main:app",              # Importa app desde este módulo
        "host": settings.HOST,          # 0.0.0.0 para escuchar en todas las interfaces
        "port": settings.PORT,          # 8789 por defecto
        "log_level": settings.LOG_LEVEL.lower(),
        "reload": False,                # ⚠️  SIEMPRE False en producción
        "access_log": True,             # Log de requests HTTP
        "use_colors": True,             # Colores en terminal
    }
    
    # Log de configuración
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info("🚀 Iniciando servidor Uvicorn")
    logger.info("=" * 70)
    logger.info(f"📍 Host: {settings.HOST}")
    logger.info(f"🔌 Puerto: {settings.PORT}")
    logger.info(f"📝 Log Level: {settings.LOG_LEVEL}")
    logger.info(f"🔄 Reload: {uvicorn_config['reload']}")
    logger.info("=" * 70)
    
    # Ejecutar servidor
    uvicorn.run(**uvicorn_config)