"""
Value Object: Comandos de sesión WuzAPI
Arquitectura Hexagonal - Capa de Dominio
"""
from enum import Enum
from typing import Optional, Tuple


class SessionCommand(str, Enum):
    """Comandos disponibles para gestionar sesión WuzAPI"""
    
    HELP = "help"
    STATUS = "status"
    QR = "qr"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    LOGOUT = "logout"          # 🔥 NUEVO
    UNKNOWN = "unknown"
    
    @classmethod
    def parse(cls, text: str) -> Tuple['SessionCommand', str]:
        """
        Parsea texto a comando.
        
        Args:
            text: Texto del mensaje (ej: "/status", "help", "/qr code")
            
        Returns:
            Tuple de (comando, argumentos)
        """
        if not text:
            return cls.UNKNOWN, ""
        
        # Limpiar texto
        text = text.strip().lower()
        
        # Remover prefijo / si existe
        if text.startswith('/'):
            text = text[1:]
        
        # Separar comando de argumentos
        parts = text.split(maxsplit=1)
        cmd_text = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        
        # Mapear aliases
        aliases = {
            'help': cls.HELP,
            'ayuda': cls.HELP,
            '?': cls.HELP,
            'h': cls.HELP,
            'status': cls.STATUS,
            'estado': cls.STATUS,
            's': cls.STATUS,
            'qr': cls.QR,
            'codigo': cls.QR,
            'connect': cls.CONNECT,
            'conectar': cls.CONNECT,
            'c': cls.CONNECT,
            'start': cls.CONNECT,
            'iniciar': cls.CONNECT,
            'disconnect': cls.DISCONNECT,
            'desconectar': cls.DISCONNECT,
            'd': cls.DISCONNECT,
            'stop': cls.DISCONNECT,
            'detener': cls.DISCONNECT,
            'logout': cls.LOGOUT,
            'salir': cls.LOGOUT,
            'cerrar': cls.LOGOUT,
            'close': cls.LOGOUT,

        }
        
        return aliases.get(cmd_text, cls.UNKNOWN), args
    
    @classmethod
    def get_help_text(cls) -> str:
        return """📋 **Comandos disponibles**

🔹 `/help` - Muestra esta ayuda
🔹 `/status` - Estado actual de la sesión
🔹 `/qr` - Obtener código QR para conectar
🔹 `/connect` - Conectar al servidor de WhatsApp
🔹 `/disconnect` - Desconectar del servidor (temporal)
🔹 `/logout` - **Cerrar sesión** (requiere nuevo QR)

**Aliases:**
- `/help` = `/ayuda` = `/?`
- `/status` = `/estado` = `/s`
- `/connect` = `/conectar` = `/start`
- `/disconnect` = `/desconectar` = `/stop`
- `/logout` = `/salir` = `/cerrar`"""