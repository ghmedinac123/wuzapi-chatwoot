"""
Configuración de logging estructurado con COLORES
"""
import logging
import sys

# Intentar importar colorlog, si no está, usar logging normal
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def setup_logging(level: str = "INFO"):
    """
    Configura logging para toda la aplicación con colores.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Formato base
    date_format = '%Y-%m-%d %H:%M:%S'
    
    if COLORLOG_AVAILABLE:
        # 🎨 Con colores (como NestJS)
        formatter = colorlog.ColoredFormatter(
            fmt='%(log_color)s%(asctime)s%(reset)s - %(name_log_color)s%(name)s%(reset)s - %(log_color)s%(levelname)s%(reset)s - %(message_log_color)s%(message)s%(reset)s',
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={
                'name': {
                    'DEBUG': 'blue',
                    'INFO': 'blue',
                    'WARNING': 'blue',
                    'ERROR': 'blue',
                    'CRITICAL': 'blue',
                },
                'message': {
                    'DEBUG': 'white',
                    'INFO': 'white',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red',
                }
            }
        )
    else:
        # Sin colores (fallback)
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt=date_format
        )
    
    # Configurar handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Limpiar handlers existentes
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Reducir ruido de librerías externas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(log_level)
    
    # Log inicial
    logger = logging.getLogger(__name__)
    logger.info(f"📋 Logging configurado: {level.upper()}")
    
    if not COLORLOG_AVAILABLE:
        logger.warning("⚠️  colorlog no instalado - logs sin colores")


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger (típicamente __name__)
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)