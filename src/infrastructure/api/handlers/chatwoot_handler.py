"""
src/infrastructure/api/handlers/chatwoot_handler.py

Handler concreto para eventos de Chatwoot.
Hereda de BaseWebhookHandler e implementa lógica específica
para procesar mensajes salientes de Chatwoot.

Responsabilidad única:
- Validar tipo de evento (message_created)
- Validar mensaje outgoing (de agente)
- Ejecutar caso de uso de envío a WhatsApp
"""
import logging
from typing import Dict, Any

from .base_handler import BaseWebhookHandler
from ....application.use_cases.send_message_to_whatsapp import SendMessageToWhatsAppUseCase

logger = logging.getLogger(__name__)


class ChatwootWebhookHandler(BaseWebhookHandler):
    """
    Handler para webhooks de Chatwoot.
    
    Procesa mensajes salientes de Chatwoot y los envía a WhatsApp.
    """
    
    def __init__(self, send_use_case: SendMessageToWhatsAppUseCase):
        """
        Args:
            send_use_case: Caso de uso para enviar mensajes a WhatsApp
        """
        super().__init__(handler_name="Chatwoot")
        self.send_use_case = send_use_case
    
    async def handle_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa evento de Chatwoot.
        
        Flujo:
        1. Extraer tipo de evento
        2. Ejecutar caso de uso de envío
        
        Returns:
            Dict con resultado del procesamiento
        """
        event_type = event_data.get('event', 'unknown')
        self.logger.info(f"📋 Tipo: {event_type}")
        
        # Ejecutar caso de uso
        success = await self._send_to_whatsapp(event_data)
        
        if success:
            return {
                "success": True,
                "data": {"event": event_type}
            }
        else:
            return {
                "success": False,
                "reason": "not_processed_or_ignored",
                "data": {"event": event_type}
            }
    
    async def _send_to_whatsapp(self, event_data: Dict[str, Any]) -> bool:
        """
        Ejecuta caso de uso de envío a WhatsApp.
        
        Args:
            event_data: Datos del evento Chatwoot
            
        Returns:
            True si envío exitoso o ignorado correctamente, False si error
        """
        try:
            success = await self.send_use_case.execute(event_data)
            
            if success:
                self.logger.info(f"✅ Mensaje enviado exitosamente a WhatsApp")
            else:
                self.logger.info(f"ℹ️  Evento ignorado o no procesado")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Excepción en envío: {e}", exc_info=True)
            return False