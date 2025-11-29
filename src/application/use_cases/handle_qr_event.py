"""
UseCase: Manejar evento QR de WuzAPI
Arquitectura Hexagonal - Capa de Aplicación
"""
import logging
from typing import Dict, Any

from ...domain.entities.wuzapi_session import WuzAPISession
from ...domain.ports.session_repository import SessionNotifierPort

logger = logging.getLogger(__name__)


class HandleQREventUseCase:
    """Procesa eventos QR de WuzAPI y notifica a Chatwoot"""
    
    def __init__(self, notifier: SessionNotifierPort):
        self.notifier = notifier
    
    async def execute(self, event_data: Dict[str, Any]) -> bool:
        """Procesa evento QR"""
        try:
            logger.info("=" * 70)
            logger.info("📱 PROCESANDO EVENTO QR")
            logger.info("=" * 70)
            
            session = WuzAPISession.from_qr_event(event_data)
            
            logger.info(f"📋 Instance: {session.instance_name}")
            logger.info(f"🔑 ID: {session.instance_id[:8]}...")
            logger.info(f"📊 Status: {session.status.value}")
            
            if not session.qr_code:
                logger.error("❌ Evento sin QR code")
                return False
            
            success = await self.notifier.notify_qr(session)
            
            if success:
                logger.info("✅ QR notificado a Chatwoot")
            else:
                logger.error("❌ Error notificando QR")
            
            logger.info("=" * 70)
            return success
            
        except Exception as e:
            logger.error(f"❌ Excepción: {e}", exc_info=True)
            return False