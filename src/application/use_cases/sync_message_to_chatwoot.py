"""
Caso de Uso: Sincronizar Mensaje de WhatsApp a Chatwoot
Procesa TODOS los tipos de mensajes: texto, audio, imagen, video, documento
"""
import logging
from ...domain.entities.whatsapp_message import WhatsAppMessage, MessageType
from ...domain.ports.chatwoot_repository import ChatwootRepository
from ...domain.ports.cache_repository import CacheRepository
from ...infrastructure.media.media_downloader import MediaDownloader

logger = logging.getLogger(__name__)

class SyncMessageToChatwootUseCase:
    """
    Caso de uso que sincroniza mensajes de WhatsApp a Chatwoot.
    
    Flujo:
    1. Validar mensaje (ignorar grupos)
    2. Crear/obtener contacto en Chatwoot
    3. Crear/obtener conversación
    4. Si tiene multimedia → descargar y subir
    5. Si es texto → enviar texto simple
    """
    
    def __init__(
        self,
        chatwoot_repo: ChatwootRepository,
        cache_repo: CacheRepository,
        media_downloader: MediaDownloader,
        wuzapi_repo  # 🔥 NUEVO PARÁMETRO
    ):
        """
        Args:
            chatwoot_repo: Repositorio para interactuar con Chatwoot
            cache_repo: Repositorio de caché para conversaciones
            media_downloader: Descargador de multimedia desde WuzAPI
        """
        self.chatwoot = chatwoot_repo
        self.cache = cache_repo
        self.media_downloader = media_downloader
        self.wuzapi_repo = wuzapi_repo
    
    async def execute(self, message: WhatsAppMessage) -> bool:
        """Ejecuta la sincronización del mensaje a Chatwoot."""
        try:
            logger.info("=" * 70)
            logger.info("🔄 SINCRONIZANDO MENSAJE A CHATWOOT")
            logger.info("=" * 70)
            logger.info(f"📋 Message ID: {message.message_id}")
            logger.info(f"📋 Tipo: {message.message_type.value}")
            logger.info(f"📋 De: {message.sender.formatted}")
            logger.info(f"📋 IsFromMe: {message.is_from_me}")
            logger.info(f"📋 IsGroup: {message.is_group}")
            
            # Verificar si es mensaje de Chatwoot → WhatsApp → Webhook
            if message.is_from_me:
                cache_key = f"sent_from_chatwoot:{message.message_id}"
                is_from_chatwoot = await self.cache.get_conversation_id(cache_key)
                
                if is_from_chatwoot:
                    logger.info(f"⏭️  Mensaje enviado desde Chatwoot → NO resincronizar")
                    logger.info("=" * 70)
                    return True
                
                logger.info(f"✅ Mensaje desde WhatsApp → Sincronizar como 'outgoing'")
            
            phone = message.sender.formatted
            
            # Detectar si es grupo
            if message.is_group:
                group_name = message.metadata.get('group_id', 'Grupo de WhatsApp')
                sender_name = message.metadata.get('sender_name', 'Usuario')
                name = f"👥 {group_name}"
                logger.info(f"👥 MENSAJE DE GRUPO: {group_name}")
            else:
                push_name = message.metadata.get('PushName') if message.metadata else None
                name = push_name or phone
            
            logger.info(f"👤 Contacto: {phone} ({name})")
            
            # Avatar
            avatar_url = None
            if not message.is_group:
                try:
                    avatar_url = await self.wuzapi_repo.get_user_avatar(phone)
                except Exception as e:
                    logger.debug(f"⚠️  Error avatar: {e}")
            
            contact_id = await self.chatwoot.create_or_get_contact(phone, name, avatar_url)
            if not contact_id:
                logger.error(f"❌ Error creando contacto")
                return False
            
            logger.info(f"✅ Contacto ID: {contact_id}")
            
            # Conversación
            conversation_id = await self.cache.get_conversation_id(phone)
            
            if not conversation_id:
                conversation_id = await self.chatwoot.create_or_get_conversation(contact_id, phone)
                if conversation_id:
                    await self.cache.set_conversation_id(phone, conversation_id)
            
            if not conversation_id:
                logger.error(f"❌ Error creando conversación")
                return False
            
            logger.info(f"✅ Conv ID: {conversation_id}")
            
            message_type = 'outgoing' if message.is_from_me else 'incoming'
            success = False
            
            # MULTIMEDIA
            if message.message_type in [MessageType.IMAGE, MessageType.VIDEO, MessageType.AUDIO, MessageType.PTT, MessageType.DOCUMENT, MessageType.STICKER]:
                success = await self._process_multimedia_message(message, conversation_id, message_type)
            # TEXTO
            elif message.message_type == MessageType.TEXT:
                content = message.extract_text_content()
                
                if message.is_group:
                    sender_name = message.metadata.get('sender_name', 'Usuario')
                    content = f"**{sender_name}:** {content}"
                
                if content:
                    chatwoot_msg_id = await self.chatwoot.send_message(conversation_id, content, message_type)
                    
                    # Si IsFromMe, cachear para evitar loop
                    if chatwoot_msg_id and message.is_from_me:
                        cache_key = f"synced_to_chatwoot:{chatwoot_msg_id}"
                        await self.cache.set_conversation_id(cache_key, "1", ttl=30)
                        logger.info(f"🔒 Cacheado {chatwoot_msg_id}")
                    
                    success = chatwoot_msg_id is not None

                        # UBICACIÓN
            elif message.message_type == MessageType.LOCATION:
                location_info = message.extract_location_info()
                if location_info:
                    content = f"📍 Ubicación: {location_info['url']}"
                else:
                    content = "[LOCATION - Error]"
                
                if message.is_group:
                    sender_name = message.metadata.get('sender_name', 'Usuario')
                    content = f"**{sender_name}:** {content}"
                
                chatwoot_msg_id = await self.chatwoot.send_message(conversation_id, content, message_type)
                
                if chatwoot_msg_id and message.is_from_me:
                    cache_key = f"synced_to_chatwoot:{chatwoot_msg_id}"
                    await self.cache.set_conversation_id(cache_key, "1", ttl=60)
                    logger.info(f"🔒 Cacheado {chatwoot_msg_id}")
                
                success = chatwoot_msg_id is not None        
            
            # OTROS
            else:
                content = f"[{message.message_type.value.upper()}]"
                if message.is_group:
                    sender_name = message.metadata.get('sender_name', 'Usuario')
                    content = f"**{sender_name}:** {content}"
                success = await self.chatwoot.send_message(conversation_id, content, message_type)
            
            logger.info("=" * 70)
            logger.info(f"{'✅ ÉXITO' if success else '❌ FALLO'}")
            logger.info("=" * 70)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ ERROR: {e}", exc_info=True)
            return False
    
    async def _process_multimedia_message(
        self,
        message: WhatsAppMessage,
        conversation_id: int,
        message_type: str
    ) -> bool:
        """
        Procesa mensajes multimedia: descarga y sube a Chatwoot.
        Captura el ID para evitar loops.
        """
        try:
            logger.info("=" * 70)
            logger.info("🎬 PROCESANDO MULTIMEDIA")
            
            # Mapear tipo de mensaje a tipo de media
            media_type_map = {
                MessageType.IMAGE: 'image',
                MessageType.VIDEO: 'video',
                MessageType.AUDIO: 'audio',
                MessageType.PTT: 'audio',
                MessageType.DOCUMENT: 'document',
                MessageType.STICKER: 'sticker'  # ✅ Usa endpoint de sticker
            }
            
            media_type = media_type_map.get(message.message_type)
            logger.info(f"📦 Media Type: {media_type}")
            
            # ==================== EXTRAER MEDIA INFO ====================
            media_info = message.extract_media_info()
            
            if not media_info:
                logger.error(f"❌ No se pudo extraer media_info")
                fallback = f"[{media_type.upper()} - Error Info]"
                if message.is_group:
                    sender = message.metadata.get('sender_name', 'Usuario')
                    fallback = f"**{sender}:** {fallback}"
                return await self.chatwoot.send_message(conversation_id, fallback, message_type)
            
            # ==================== DESCARGAR ====================
            logger.info(f"⬇️  Descargando {media_type}...")
            
            media_data = await self.media_downloader.download_from_wuzapi_endpoint(
                message_id=message.message_id,
                media_type=media_type,
                media_info=media_info
            )
            
            if not media_data:
                logger.error(f"❌ Falló descarga")
                return False # O enviar fallback de error
            
            # ==================== SUBIR A CHATWOOT ====================
            caption = message.extract_text_content() or f"{media_type.upper()}"
            if message.is_group:
                sender_name = message.metadata.get('sender_name', 'Usuario')
                caption = f"**{sender_name}:** {caption}"
            
            logger.info(f"⬆️  Subiendo a Chatwoot...")

            # 🔥 CAMBIO CRÍTICO: Recibir ID en lugar de True/False
            chatwoot_msg_id = await self.chatwoot.send_message_with_attachments(
                conversation_id=conversation_id,
                content=caption,
                message_type=message_type,
                file_data=media_data['file_data'],
                filename=media_data['filename'],
                mimetype=media_data['mimetype']
            )
            
            if chatwoot_msg_id:
                logger.info(f"✅ Multimedia subido exitosamente. ID: {chatwoot_msg_id}")
                
                # 🔥 CACHEAR ID PARA ANTI-LOOP (Si lo envié yo desde el móvil)
                if message.is_from_me:
                    cache_key = f"synced_to_chatwoot:{chatwoot_msg_id}"
                    # Guardamos en Redis por 60 segundos
                    await self.cache.set_conversation_id(cache_key, "1", ttl=60)
                    logger.info(f"🔒 Cacheado multimedia {chatwoot_msg_id} para evitar loop")
                
                logger.info("=" * 70)
                return True
            else:
                logger.error(f"❌ Error subiendo multimedia a Chatwoot")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error procesando multimedia: {e}", exc_info=True)
            return False