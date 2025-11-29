"""
UseCase: Conectar sesión WuzAPI
Arquitectura Hexagonal - Capa de Aplicación
"""
import logging

from ...domain.ports.session_repository import SessionRepository, SessionNotifierPort

logger = logging.getLogger(__name__)


class ConnectSessionUseCase:
    """Reconecta sesión de WuzAPI"""
    
    def __init__(
        self,
        session_repo: SessionRepository,
        notifier: SessionNotifierPort
    ):
        self.session_repo = session_repo
        self.notifier = notifier
    
    async def execute(self) -> bool:
        """Ejecuta reconexión"""
        try:
            logger.info("=" * 70)
            logger.info("🔄 RECONECTANDO SESIÓN WUZAPI")
            logger.info("=" * 70)
            
            success = await self.session_repo.connect()
            
            if success:
                logger.info("✅ Comando de conexión enviado")
                
                # Obtener estado actualizado
                session = await self.session_repo.get_status()
                if session and session.is_connected:
                    await self.notifier.notify_connected(session)
            else:
                logger.error("❌ Error enviando comando de conexión")
            
            logger.info("=" * 70)
            return success
            
        except Exception as e:
            logger.error(f"❌ Excepción: {e}", exc_info=True)
            return False