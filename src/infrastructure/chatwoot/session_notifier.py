"""
Adapter: Notificador de sesiones a Chatwoot
Arquitectura Hexagonal - Capa de Infraestructura
"""
import logging
from typing import Optional

from ...domain.entities.wuzapi_session import WuzAPISession
from ...domain.ports.session_repository import SessionNotifierPort
from .client import ChatwootClient

logger = logging.getLogger(__name__)


class ChatwootSessionNotifier(SessionNotifierPort):
    """Envía notificaciones de sesión WuzAPI a Chatwoot"""
    
    def __init__(
        self,
        chatwoot_client: ChatwootClient,
        contact_name: str,
        source_id: str
    ):
        self.chatwoot = chatwoot_client
        self.contact_name = contact_name
        self.source_id = source_id
        self._contact_id: Optional[int] = None
        self._conversation_id: Optional[int] = None
    
    async def _ensure_contact_and_conversation(self) -> bool:
        """Asegura que exista el contacto y conversación"""
        try:
            if not self._contact_id:
                # 🔥 Buscar por identifier primero
                self._contact_id = await self._find_or_create_bot_contact()
            
            if not self._contact_id:
                logger.error("❌ No se pudo crear/obtener contacto")
                return False
            
            if not self._conversation_id:
                self._conversation_id = await self.chatwoot.create_or_get_conversation(
                    contact_id=self._contact_id,
                    source_id=self.source_id
                )
            
            if not self._conversation_id:
                logger.error("❌ No se pudo crear/obtener conversación")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en _ensure_contact_and_conversation: {e}")
            return False
        

    async def _find_or_create_bot_contact(self) -> Optional[int]:
        """
        Busca o crea el contacto del bot.
        
        🔥 FIX: Usa identifier en lugar de phone_number para evitar error E164
        """
        try:
            # 1️⃣ Buscar por identifier
            search_url = f"/api/v1/accounts/{self.chatwoot.account_id}/contacts/search"
            response = await self.chatwoot.client.get(search_url, params={'q': self.source_id})
            
            if response.status_code == 200:
                contacts = response.json().get('payload', [])
                for contact in contacts:
                    if contact.get('identifier') == self.source_id:
                        logger.info(f"✅ Contacto bot encontrado: {contact['id']}")
                        return contact['id']
            
            # 2️⃣ Crear contacto SIN phone_number (solo identifier)
            logger.info(f"📝 Creando contacto bot: {self.contact_name}")
            
            create_url = f"/api/v1/accounts/{self.chatwoot.account_id}/contacts"
            data = {
                'inbox_id': int(self.chatwoot.inbox_id),
                'name': self.contact_name,
                'identifier': self.source_id
                # 🔥 NO incluir phone_number para evitar error E164
            }
            
            response = await self.chatwoot.client.post(create_url, json=data)
            
            if response.status_code in [200, 201]:
                contact_id = response.json()['payload']['contact']['id']
                logger.info(f"✅ Contacto bot creado: {contact_id}")
                return contact_id
            
            logger.error(f"❌ Error creando contacto bot: {response.status_code}")
            logger.error(f"❌ Response: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Excepción creando contacto bot: {e}")
            return None    
    
    async def notify_qr(self, session: WuzAPISession) -> bool:
        """Envía imagen QR a Chatwoot"""
        try:
            if not await self._ensure_contact_and_conversation():
                return False
            
            qr_bytes = session.qr_bytes
            if not qr_bytes:
                logger.error("❌ No se pudo extraer QR bytes")
                return False
            
            # Enviar mensaje con imagen
            message = (
                f"⚠️ **Sesión desconectada**\n\n"
                f"📱 Instancia: `{session.instance_name}`\n"
                f"🔑 ID: `{session.instance_id[:8]}...`\n\n"
                f"Escanea el código QR con WhatsApp para reconectar."
            )
            
            result = await self.chatwoot.send_message_with_attachments(
                conversation_id=self._conversation_id,
                content=message,
                message_type='incoming',
                file_data=qr_bytes,
                filename='qr_code.png',
                mimetype='image/png'
            )
            
            if result:
                logger.info(f"✅ QR enviado a Chatwoot (Conv: {self._conversation_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error en notify_qr: {e}")
            return False
    
    async def notify_connected(self, session: WuzAPISession) -> bool:
        """Notifica conexión exitosa"""
        try:
            if not await self._ensure_contact_and_conversation():
                return False
            
            message = (
                f"✅ **Sesión conectada**\n\n"
                f"📱 Instancia: `{session.instance_name}`\n"
                f"📞 JID: `{session.jid or 'N/A'}`"
            )
            
            result = await self.chatwoot.send_message(
                conversation_id=self._conversation_id,
                content=message,
                message_type='incoming'
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"❌ Error en notify_connected: {e}")
            return False
    
    async def notify_disconnected(self, session: WuzAPISession) -> bool:
        """Notifica desconexión"""
        try:
            if not await self._ensure_contact_and_conversation():
                return False
            
            message = (
                f"🔴 **Sesión desconectada**\n\n"
                f"📱 Instancia: `{session.instance_name}`\n\n"
                f"Esperando nuevo código QR..."
            )
            
            result = await self.chatwoot.send_message(
                conversation_id=self._conversation_id,
                content=message,
                message_type='incoming'
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"❌ Error en notify_disconnected: {e}")
            return False

    async def respond(self, conversation_id: int, response) -> bool:
        """
        Responde a un comando en la conversación.
        
        Args:
            conversation_id: ID de la conversación
            response: Texto o dict con tipo especial (ej: QR)
            
        Returns:
            True si se envió correctamente
        """
        try:
            # Si es dict especial (QR con imagen)
            if isinstance(response, dict) and response.get('type') == 'qr':
                session = response.get('session')
                message = response.get('message', '')
                
                if session and session.qr_bytes:
                    result = await self.chatwoot.send_message_with_attachments(
                        conversation_id=conversation_id,
                        content=message,
                        message_type='incoming',
                        file_data=session.qr_bytes,
                        filename='qr_code.png',
                        mimetype='image/png'
                    )
                    return result is not None
                else:
                    # Fallback a texto
                    response = message
            
            # Respuesta de texto normal
            result = await self.chatwoot.send_message(
                conversation_id=conversation_id,
                content=response,
                message_type='incoming'
            )
            return result is not None
            
        except Exception as e:
            logger.error(f"❌ Error en respond: {e}")
            return False        