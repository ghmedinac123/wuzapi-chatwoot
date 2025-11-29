"""
Entity: Sesión de WuzAPI
Arquitectura Hexagonal - Capa de Dominio
"""
from dataclasses import dataclass
from typing import Optional

from ..value_objects.session_status import SessionStatus


@dataclass
class WuzAPISession:
    """Representa el estado de una sesión de WuzAPI"""
    
    instance_id: str
    instance_name: str
    status: SessionStatus
    jid: Optional[str] = None
    qr_code: Optional[str] = None
    webhook: Optional[str] = None
    
    @property
    def is_connected(self) -> bool:
        return self.status == SessionStatus.CONNECTED
    
    @property
    def needs_qr(self) -> bool:
        return self.status == SessionStatus.QR_PENDING
    
    @property
    def qr_bytes(self) -> Optional[bytes]:
        """Extrae bytes del QR desde base64"""
        if not self.qr_code:
            return None
        
        import base64
        
        try:
            # Remover prefijo data:image/png;base64,
            if ',' in self.qr_code:
                b64_data = self.qr_code.split(',')[1]
            else:
                b64_data = self.qr_code
            
            return base64.b64decode(b64_data)
        except Exception:
            return None
    
    @classmethod
    def from_status_response(cls, data: dict) -> 'WuzAPISession':
        """Factory desde respuesta de GET /session/status"""
        session_data = data.get('data', {})
        
        connected = session_data.get('connected', False)
        logged_in = session_data.get('loggedIn', False)
        has_qr = bool(session_data.get('qrcode'))
        
        if connected and logged_in:
            status = SessionStatus.CONNECTED
        elif has_qr:
            status = SessionStatus.QR_PENDING
        elif connected:
            status = SessionStatus.CONNECTING
        else:
            status = SessionStatus.DISCONNECTED
        
        return cls(
            instance_id=session_data.get('id', ''),
            instance_name=session_data.get('name', ''),
            status=status,
            jid=session_data.get('jid'),
            qr_code=session_data.get('qrcode'),
            webhook=session_data.get('webhook')
        )
    
    @classmethod
    def from_qr_event(cls, event_data: dict) -> 'WuzAPISession':
        """Factory desde evento QR del webhook"""
        return cls(
            instance_id=event_data.get('userID', ''),
            instance_name=event_data.get('instanceName', ''),
            status=SessionStatus.QR_PENDING,
            qr_code=event_data.get('qrCodeBase64')
        )
    
    @classmethod
    def from_connection_event(cls, event_data: dict, status: SessionStatus) -> 'WuzAPISession':
        """Factory desde evento Connected/Disconnected"""
        return cls(
            instance_id=event_data.get('userID', ''),
            instance_name=event_data.get('instanceName', ''),
            status=status,
            jid=event_data.get('jid')
        )