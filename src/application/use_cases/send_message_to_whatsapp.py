"""
src/application/use_cases/send_message_to_whatsapp.py

Caso de Uso: Enviar Mensajes de Chatwoot a WhatsApp
CORREGIDO: Implementa deduplicación por ID usando CacheRepository para detener loops.
"""
import logging
from typing import Dict, Any

from ...domain.ports.wuzapi_repository import WuzAPIRepository
# 🔥 IMPORTANTE: Importamos el puerto de caché
from ...domain.ports.cache_repository import CacheRepository

logger = logging.getLogger(__name__)

class SendMessageToWhatsAppUseCase:
    """
    Procesa mensajes salientes de Chatwoot y los envía a WhatsApp.
    
    Trabaja directo con JSON de Chatwoot (no usa entidades).
    """
    
    # 🔥 MODIFICADO: Inyectamos cache_repo en el constructor
    def __init__(self, wuzapi_repo: WuzAPIRepository, cache_repo: CacheRepository):
        self.wuzapi = wuzapi_repo
        self.cache = cache_repo # Guardamos la referencia a la caché
    
    async def execute(self, event_data: Dict[str, Any]) -> bool:
        try:
            message_id = event_data.get('id')

            logger.info("=" * 70)
            logger.info(f"📤 MENSAJE DESDE CHATWOOT → WHATSAPP (ID: {message_id})")
            logger.info("=" * 70)
            
            
            
            # 🔥🔥🔥 NUEVA LÓGICA ANTI-LOOP (DEDUPLICACIÓN POR ID) 🔥🔥🔥
            # Verificamos si este mensaje fue subido por nosotros mismos hace poco.
            if message_id:
                cache_key = f"synced_to_chatwoot:{message_id}"
                # Consultamos al Redis
                already_processed = await self.cache.get_conversation_id(cache_key)
                
                if already_processed:
                    logger.info(f"🛑 LOOP DETECTADO: El mensaje {message_id} fue subido por la sincronización.")
                    logger.info("   🚫 Se cancela el re-envío a WhatsApp.")
                    logger.info("=" * 70)
                    return True # Retornamos True para que no se considere error
            # 🔥🔥🔥 FIN LÓGICA ANTI-LOOP 🔥🔥🔥

            if not await self._should_process(event_data):  # ✅ CON await
                logger.info("ℹ️  Evento ignorado (no es outgoing de agente)")
                logger.info("=" * 70)
                return False
            
            content = event_data.get('content', '')
            attachments = event_data.get('attachments', [])
            
            conversation = event_data.get('conversation', {})
            phone = self._extract_phone(conversation)
            
            if not phone:
                logger.error("❌ No se pudo extraer teléfono")
                logger.info("=" * 70)
                return False
            
            logger.info(f"📞 Destino: {phone}")
            logger.info(f"💬 Contenido: {content[:100] if content else '(vacío)'}...")
            logger.info(f"📎 Attachments: {len(attachments)}")
            
            success = False
            
            if attachments:
                attachment = attachments[0]
                success = await self._send_multimedia(phone, content, attachment)
            else:
                if content:
                    success = await self._send_text(phone, content)
                else:
                    logger.warning("⚠️  Sin contenido ni attachments")
            
            logger.info("=" * 70)
            return success
            
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ EXCEPCIÓN: {e}", exc_info=True)
            logger.error("=" * 70)
            return False
        
    async def _should_process(self, event_data: Dict[str, Any]) -> bool:
        """Filtros anti-loop y validaciones."""
        
        # Resto de filtros...
        event_type = event_data.get('event', '')
        message_type = event_data.get('message_type', '')
        private = event_data.get('private', False)
        sender = event_data.get('sender', {})
        
        logger.info(f"🔍 Validando:")
        logger.info(f"   • event: {event_type}")
        logger.info(f"   • message_type: {message_type}")
        
        if event_type != 'message_created':
            logger.info(f"⏭️  Ignorado: event != message_created")
            return False
        
        if message_type != 'outgoing':
            logger.info(f"⏭️  Ignorado: message_type != outgoing")
            return False
        
        if private:
            logger.info(f"⏭️  Ignorado: privado")
            return False
        
        if sender.get('type') != 'user':
            logger.info(f"⏭️  Ignorado: sender.type != user")
            return False
        
        logger.info(f"✅ Válido - enviar a WhatsApp")
        return True
    
    def _extract_phone(self, conversation: Dict[str, Any]) -> str:
        """
        Extrae el número de teléfono de la conversación.
        
        Está en: conversation.contact_inbox.source_id
        """
        contact_inbox = conversation.get('contact_inbox', {})
        source_id = contact_inbox.get('source_id', '')
        
        # Limpiar formato
        phone = source_id.replace('+', '').replace('group_', '')
        
        logger.debug(f"📞 source_id: {source_id} → phone: {phone}")
        
        return phone
    
    async def _send_text(self, phone: str, content: str) -> bool:
        """Envía texto simple"""
        logger.info("💬 Enviando TEXTO")
        
        success = await self.wuzapi.send_text_message(phone, content)
        
        if success:
            logger.info("✅ Texto enviado")
        else:
            logger.error("❌ Error enviando texto")
        
        return success
    
    async def _send_multimedia(
        self,
        phone: str,
        content: str,
        attachment: Dict[str, Any]
    ) -> bool:
        """
        Envía multimedia según file_type del attachment.
        """
        file_type = attachment.get('file_type', 'unknown')
        data_url = attachment.get('data_url', '')
        file_name = attachment.get('file_name', 'archivo')
        
        logger.info(f"📦 Enviando {file_type.upper()}")
        logger.info(f"   📄 Filename: {file_name}")
        logger.info(f"   🔗 URL: {data_url[:60]}...")
        
        if not data_url:
            logger.error("❌ Sin data_url")
            return False
        
        # Mapear file_type → método
        if file_type == 'image':
            success = await self.wuzapi.send_image_message(
                phone, data_url, content or ''
            )
        
        elif file_type == 'video':
            success = await self.wuzapi.send_video_message(
                phone, data_url, content or ''
            )
        
        elif file_type == 'audio':
            success = await self.wuzapi.send_audio_message(phone, data_url)
        
        elif file_type == 'file':
            success = await self.wuzapi.send_document_message(
                phone, data_url, file_name
            )
        
        else:
            logger.warning(f"⚠️  Tipo '{file_type}' no soportado")
            # Fallback: enviar como texto
            fallback = f"{content}\n\n[Archivo: {file_name}]" if content else f"[Archivo: {file_name}]"
            success = await self.wuzapi.send_text_message(phone, fallback)
        
        if success:
            logger.info(f"✅ {file_type.upper()} enviado")
        else:
            logger.error(f"❌ Error")
        
        return success