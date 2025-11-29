"""
Value Object: Estado de sesión WuzAPI
Arquitectura Hexagonal - Capa de Dominio
"""
from enum import Enum


class SessionStatus(str, Enum):
    """Estados posibles de una sesión WuzAPI"""
    
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    QR_PENDING = "qr_pending"
    CONNECTING = "connecting"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_event_type(cls, event_type: str) -> 'SessionStatus':
        """Mapea tipo de evento a estado"""
        mapping = {
            'QR': cls.QR_PENDING,
            'Connected': cls.CONNECTED,
            'Disconnected': cls.DISCONNECTED,
            'LoggedOut': cls.DISCONNECTED,
        }
        return mapping.get(event_type, cls.UNKNOWN)