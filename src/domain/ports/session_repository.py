"""
Port: Repositorio de sesiones WuzAPI
Arquitectura Hexagonal - Capa de Dominio
"""
from abc import ABC, abstractmethod
from typing import Optional

from ..entities.wuzapi_session import WuzAPISession


class SessionRepository(ABC):
    """Interface para operaciones de sesión WuzAPI"""
    
    @abstractmethod
    async def get_status(self) -> Optional[WuzAPISession]:
        """Obtiene estado actual de la sesión"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Conecta/reconecta la sesión"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Desconecta la sesión"""
        pass

    # 🔥 NUEVOS
    @abstractmethod
    async def logout(self) -> bool:
        """Cierra sesión completamente (requiere nuevo QR)"""
        pass
    
    @abstractmethod
    async def get_qr(self) -> Optional[str]:
        """Obtiene QR en base64 desde GET /session/qr"""
        pass



class SessionNotifierPort(ABC):
    """Interface para notificar eventos de sesión a Chatwoot"""
    
    @abstractmethod
    async def notify_qr(self, session: WuzAPISession) -> bool:
        """Envía QR a Chatwoot"""
        pass
    
    @abstractmethod
    async def notify_connected(self, session: WuzAPISession) -> bool:
        """Notifica conexión exitosa"""
        pass
    
    @abstractmethod
    async def notify_disconnected(self, session: WuzAPISession) -> bool:
        """Notifica desconexión"""
        pass