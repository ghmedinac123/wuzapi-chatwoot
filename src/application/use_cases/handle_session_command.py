"""
UseCase: Manejar comandos de sesión desde Chatwoot
Arquitectura Hexagonal - Capa de Aplicación
"""
import logging
from typing import Dict, Any

from ...domain.value_objects.session_command import SessionCommand
from ...domain.ports.session_repository import SessionRepository, SessionNotifierPort

logger = logging.getLogger(__name__)


class HandleSessionCommandUseCase:
    """
    Procesa comandos del admin desde Chatwoot.
    
    Responsabilidad única: Parsear comando y ejecutar acción correspondiente.
    """
    
    def __init__(
        self,
        session_repo: SessionRepository,
        notifier: SessionNotifierPort
    ):
        self.session_repo = session_repo
        self.notifier = notifier
    
    async def execute(self, message_text: str, conversation_id: int) -> bool:
        """
        Procesa un comando.
        
        Args:
            message_text: Texto del mensaje (ej: "/status")
            conversation_id: ID de conversación para responder
            
        Returns:
            True si se procesó correctamente
        """
        try:
            logger.info("=" * 70)
            logger.info("🤖 PROCESANDO COMANDO DE SESIÓN")
            logger.info("=" * 70)
            logger.info(f"📝 Texto: {message_text}")
            logger.info(f"💬 Conversación: {conversation_id}")
            
            # Parsear comando
            command, args = SessionCommand.parse(message_text)
            logger.info(f"🎯 Comando: {command.value}")
            
            # Ejecutar según comando
            if command == SessionCommand.HELP:
                response = await self._handle_help()
            
            elif command == SessionCommand.STATUS:
                response = await self._handle_status()
            
            elif command == SessionCommand.QR:
                response = await self._handle_qr()
            
            elif command == SessionCommand.CONNECT:
                response = await self._handle_connect()
            
            elif command == SessionCommand.DISCONNECT:
                response = await self._handle_disconnect()

            elif command == SessionCommand.LOGOUT:
                response = await self._handle_logout()    
            
            else:
                response = self._handle_unknown(message_text)
            
            # Enviar respuesta
            success = await self.notifier.respond(conversation_id, response)
            
            logger.info(f"{'✅' if success else '❌'} Respuesta enviada")
            logger.info("=" * 70)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Excepción: {e}", exc_info=True)
            return False
    
    async def _handle_help(self) -> str:
        """Comando /help"""
        return SessionCommand.get_help_text()
    
    async def _handle_status(self) -> str:
        """Comando /status"""
        session = await self.session_repo.get_status()
        
        if not session:
            return "❌ **Error** - No se pudo obtener estado de la sesión"
        
        status_emoji = {
            'connected': '🟢',
            'disconnected': '🔴',
            'qr_pending': '🟡',
            'connecting': '🟠',
            'unknown': '⚪'
        }
        
        emoji = status_emoji.get(session.status.value, '⚪')
        
        response = f"""📊 **Estado de la Sesión**

{emoji} **Estado:** `{session.status.value}`
📱 **Instancia:** `{session.instance_name}`
🔑 **ID:** `{session.instance_id[:12]}...`"""
        
        if session.jid:
            response += f"\n📞 **JID:** `{session.jid}`"
        
        if session.webhook:
            response += f"\n🔗 **Webhook:** Activo"
        
        if session.needs_qr:
            response += "\n\n⚠️ _Usa `/qr` para obtener el código QR_"
        
        return response
    
    async def _handle_qr(self) -> Dict[str, Any]:
            """Comando /qr - Obtiene QR fresco"""
            # Primero intentar GET /session/qr directo
            qr_code = await self.session_repo.get_qr()
            
            if qr_code:
                # Crear sesión temporal con el QR
                from ...domain.entities.wuzapi_session import WuzAPISession
                from ...domain.value_objects.session_status import SessionStatus
                
                session = WuzAPISession(
                    instance_id="",
                    instance_name="",
                    status=SessionStatus.QR_PENDING,
                    qr_code=qr_code
                )
                
                return {
                    "type": "qr",
                    "session": session,
                    "message": "📱 **Escanea el código QR** con WhatsApp para conectar"
                }
            
            # Fallback: obtener de status
            session = await self.session_repo.get_status()
            
            if not session:
                return "❌ **Error** - No se pudo obtener sesión"
            
            if session.is_connected:
                return "✅ **Sesión ya conectada** - No se necesita QR"
            
            if session.qr_code:
                return {
                    "type": "qr",
                    "session": session,
                    "message": "📱 **Escanea el código QR** con WhatsApp para conectar"
                }
            
            return "⚠️ **Sin QR disponible** - Usa `/connect` primero para generar uno"
    
    async def _handle_connect(self) -> str:
        """Comando /connect"""
        success = await self.session_repo.connect()
        
        if success:
            return """✅ **Comando de conexión enviado**

Espera unos segundos y usa `/status` para verificar.
Si aparece QR, usa `/qr` para obtenerlo."""
        else:
            return "❌ **Error** - No se pudo enviar comando de conexión"
    
    async def _handle_disconnect(self) -> str:
        """Comando /disconnect"""
        success = await self.session_repo.disconnect()
        
        if success:
            return "🔴 **Sesión desconectada**"
        else:
            return "❌ **Error** - No se pudo desconectar"
    
    def _handle_unknown(self, text: str) -> str:
        """Comando desconocido"""
        return f"""⚠️ **Comando no reconocido:** `{text}`

Usa `/help` para ver los comandos disponibles."""
    
    async def _handle_logout(self) -> str:
        """Comando /logout - Cierra sesión completamente"""
        success = await self.session_repo.logout()
        
        if success:
            return """🚪 **Sesión cerrada**

La sesión de WhatsApp ha sido cerrada completamente.

Para volver a conectar:
1. Usa `/connect` para iniciar conexión
2. Usa `/qr` para obtener el código QR
3. Escanea el QR con WhatsApp"""
        else:
            return "❌ **Error** - No se pudo cerrar la sesión"