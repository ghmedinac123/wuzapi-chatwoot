"""
src/infrastructure/api/handlers/wuzapi_handler.py

Handler concreto para eventos de WuzAPI.
Hereda de BaseWebhookHandler e implementa lógica específica
para procesar mensajes de WhatsApp.

Responsabilidad única:
- Validar userID de la instancia
- Parsear eventos WuzAPI a entidades del dominio
- Ejecutar caso de uso de sincronización a Chatwoot
"""
import json
import logging
from typing import Dict, Any

from .base_handler import BaseWebhookHandler
from ....domain.entities.whatsapp_message import WhatsAppMessage
from ....application.use_cases.sync_message_to_chatwoot import SyncMessageToChatwootUseCase

logger = logging.getLogger(__name__)


class WuzAPIWebhookHandler(BaseWebhookHandler):
    """
    Handler para webhooks de WuzAPI.
    
    Procesa eventos de WhatsApp y los sincroniza a Chatwoot.
    """
    
    def __init__(
        self,
        sync_use_case: SyncMessageToChatwootUseCase,
        expected_instance_id: str,
        qr_use_case = None,           # 🔥 NUEVO
        session_notifier = None        # 🔥 NUEVO
    ):
        """
        Args:
            sync_use_case: Caso de uso para sincronizar a Chatwoot
            expected_instance_id: ID de instancia WuzAPI esperado
            qr_use_case: Caso de uso para manejar QR (opcional)
            session_notifier: Notificador de sesión (opcional)
        """
        super().__init__(handler_name="WuzAPI")
        self.sync_use_case = sync_use_case
        self.expected_instance_id = expected_instance_id
        self.qr_use_case = qr_use_case              # 🔥 NUEVO
        self.session_notifier = session_notifier    # 🔥 NUEVO
    
    def _validate_payload(self, event_data: Dict[str, Any]) -> bool:
        """
        Validación específica para eventos WuzAPI.
        
        Verifica:
        1. Payload básico válido
        2. Tipo de evento es 'Message'
        3. userID coincide con instancia configurada
        """
        # Validación base
        if not super()._validate_payload(event_data):
            return False
        
        # Debe tener campos obligatorios
        if 'type' not in event_data or 'userID' not in event_data:
            self.logger.warning("⚠️  Faltan campos obligatorios: 'type' y/o 'userID'")
            return False
        
        return True
    
    async def handle_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa evento de WuzAPI.
        
        Flujo:
        1. Extraer y validar metadatos del evento
        2. Validar tipo de evento (solo 'Message')
        3. Validar userID de instancia
        4. Parsear mensaje a entidad del dominio
        5. Ejecutar caso de uso de sincronización
        
        Returns:
            Dict con resultado del procesamiento
        """
        # Extraer metadatos
        event_type = event_data.get('type', 'Unknown')
        user_id = event_data.get('userID', 'Unknown')
        instance_name = event_data.get('instanceName', 'Unknown')
        
        self.logger.info(f"📋 Tipo: {event_type}")
        self.logger.info(f"🆔 User ID: {user_id}")
        self.logger.info(f"📝 Instance: {instance_name}")
        
        # 1. Validar userID
        if not self._validate_instance_id(user_id):
            return {
                "success": False,
                "reason": "wrong_user_id",
                "data": {
                    "expected": self.expected_instance_id,
                    "received": user_id
                }
            }
        

                
        # 2. ========== NUEVO: Manejar eventos de sesión ==========
        if event_type == 'QR':
            return await self._handle_qr_event(event_data)
        
        if event_type in ('Connected', 'LoggedIn'):
            return await self._handle_connected_event(event_data)
        
        if event_type in ('Disconnected', 'LoggedOut'):
            return await self._handle_disconnected_event(event_data)
        # ========== FIN NUEVO ==========
        
        # 2. Validar tipo de evento
        if event_type != 'Message':
            self.logger.info(f"ℹ️  Tipo '{event_type}' no procesado (solo 'Message')")
            return {
                "success": False,
                "reason": "not_message_event",
                "data": {"event_type": event_type}
            }
        
        # 3. Loggear estructura del evento (debugging)
        self._log_event_structure(event_data)
        
        # 4. Parsear mensaje
        parsed_message = self._parse_message(event_data)
        if not parsed_message:
            return {
                "success": False,
                "reason": "parse_error"
            }
        
        # 5. Loggear mensaje parseado
        self._log_parsed_message(parsed_message)
        
        # 6. Ejecutar sincronización
        sync_success = await self._sync_to_chatwoot(parsed_message)
        
        if sync_success:
            return {
                "success": True,
                "data": {
                    "message_id": parsed_message.message_id,
                    "message_type": parsed_message.message_type.value,
                    "sender": parsed_message.sender.formatted
                }
            }
        else:
            return {
                "success": False,
                "reason": "sync_failed"
            }
    
    def _validate_instance_id(self, user_id: str) -> bool:
        """
        Valida que el userID coincida con la instancia esperada.
        
        Esto previene procesar eventos de otras instancias.
        """
        if user_id != self.expected_instance_id:
            self.logger.warning(f"⚠️  User ID inválido o de otra instancia")
            self.logger.warning(f"⚠️  Esperado: {self.expected_instance_id}")
            self.logger.warning(f"⚠️  Recibido: {user_id}")
            return False
        return True
    
    def _log_event_structure(self, event_data: Dict[str, Any]) -> None:
        """Log detallado de la estructura del evento (útil para debugging)."""
        event_info = event_data.get('event', {})
        info = event_info.get('Info', {})
        message = event_info.get('Message', {})
        
        self.logger.debug("📋 ESTRUCTURA DEL EVENTO:")
        self.logger.debug(f"   • Info: {json.dumps(info, indent=2, ensure_ascii=False)}")
        self.logger.debug(f"   • Message: {json.dumps(message, indent=2, ensure_ascii=False)}")
    
    def _parse_message(self, event_data: Dict[str, Any]) -> WhatsAppMessage:
        """
        Parsea evento WuzAPI a entidad WhatsAppMessage.
        
        Delega el parseo a la factory method del dominio.
        """
        try:
            return WhatsAppMessage.from_wuzapi_event(event_data)
        except Exception as e:
            self.logger.error(f"❌ Error parseando mensaje: {e}", exc_info=True)
            self.logger.error(f"❌ Event data:")
            self.logger.error(json.dumps(event_data, indent=2, ensure_ascii=False))
            return None
    
    def _log_parsed_message(self, message: WhatsAppMessage) -> None:
        """Log de mensaje parseado exitosamente."""
        self.logger.info(f"✅ Mensaje parseado exitosamente")
        self.logger.info(f"   • Tipo: {message.message_type.value}")
        self.logger.info(f"   • De: {message.sender.formatted}")
        self.logger.info(f"   • ID: {message.message_id}")
        self.logger.info(f"   • IsFromMe: {message.is_from_me}")
        self.logger.info(f"   • IsGroup: {message.is_group}")
        
        if message.metadata:
            self.logger.debug(f"📋 METADATA:")
            self.logger.debug(json.dumps(message.metadata, indent=2, ensure_ascii=False))
    
    async def _sync_to_chatwoot(self, message: WhatsAppMessage) -> bool:
        """
        Ejecuta caso de uso de sincronización a Chatwoot.
        
        Args:
            message: Mensaje parseado del dominio
            
        Returns:
            True si sincronización exitosa, False si no
        """
        self.logger.info(f"🔄 Ejecutando SyncMessageToChatwootUseCase...")
        
        try:
            success = await self.sync_use_case.execute(message)
            
            if success:
                self.logger.info(f"✅ Mensaje sincronizado exitosamente a Chatwoot")
            else:
                self.logger.warning(f"⚠️  No se pudo sincronizar el mensaje a Chatwoot")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Excepción en sincronización: {e}", exc_info=True)
            return False



    async def _handle_qr_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa evento QR - Notifica a Chatwoot"""
        self.logger.info("📱 Evento QR recibido")
        
        if not self.qr_use_case:
            self.logger.warning("⚠️  QR UseCase no configurado")
            return {"success": False, "reason": "qr_usecase_not_configured"}
        
        success = await self.qr_use_case.execute(event_data)
        
        if success:
            self.logger.info("✅ QR enviado a Chatwoot")
            return {"success": True, "data": {"event": "qr_notified"}}
        else:
            self.logger.error("❌ Error enviando QR")
            return {"success": False, "reason": "qr_notification_failed"}
    
    async def _handle_connected_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa evento Connected"""
        self.logger.info("✅ Sesión conectada")
        
        if self.session_notifier:
            from ....domain.entities.wuzapi_session import WuzAPISession
            from ....domain.value_objects.session_status import SessionStatus
            session = WuzAPISession.from_connection_event(event_data, SessionStatus.CONNECTED)
            await self.session_notifier.notify_connected(session)
        
        return {"success": True, "data": {"event": "connected"}}
    
    async def _handle_disconnected_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa evento Disconnected"""
        self.logger.info("🔴 Sesión desconectada")
        
        if self.session_notifier:
            from ....domain.entities.wuzapi_session import WuzAPISession
            from ....domain.value_objects.session_status import SessionStatus
            session = WuzAPISession.from_connection_event(event_data, SessionStatus.DISCONNECTED)
            await self.session_notifier.notify_disconnected(session)
        
        return {"success": True, "data": {"event": "disconnected"}}        