"""
src/application/use_cases/send_message_to_whatsapp.py

Caso de Uso: Enviar Mensajes de Chatwoot a WhatsApp
Arquitectura Hexagonal - Orquestación de envío con conversión de audio
"""
import logging
from typing import Dict, Any, Optional
import httpx

from ...domain.ports.wuzapi_repository import WuzAPIRepository
from ...domain.ports.cache_repository import CacheRepository
from ...domain.ports.audio_converter import AudioConverterPort
from ...domain.value_objects.message_type import MessageType
logger = logging.getLogger(__name__)


class SendMessageToWhatsAppUseCase:
    """
    Procesa mensajes salientes de Chatwoot y los envía a WhatsApp.
    
    Responsabilidades:
    - Validar eventos de Chatwoot
    - Orquestar envío de diferentes tipos de contenido
    - Convertir audio WAV → OGG si es necesario
    """
    
    def __init__(
        self, 
        wuzapi_repo: WuzAPIRepository, 
        cache_repo: CacheRepository,
        audio_converter: Optional[AudioConverterPort] = None
    ):
        self.wuzapi = wuzapi_repo
        self.cache = cache_repo
        self.audio_converter = audio_converter
    
    async def execute(self, event_data: Dict[str, Any]) -> bool:
        """Punto de entrada principal del Use Case"""
        try:
            message_id = event_data.get('id') 

            logger.info("=" * 70)
            logger.info(f"📤 MENSAJE DESDE CHATWOOT → WHATSAPP (ID: {message_id})")
            logger.info("=" * 70)
            
            # Anti-loop: verificar si ya procesamos este mensaje
            if message_id:
                cache_key = f"synced_to_chatwoot:{message_id}"
                already_processed = await self.cache.get_conversation_id(cache_key)
                
                if already_processed:
                    logger.info(f"🛑 LOOP DETECTADO: Mensaje {message_id} ya sincronizado")
                    logger.info("=" * 70)
                    return True

            if not await self._should_process(event_data):
                logger.info("ℹ️  Evento ignorado")
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
            elif content:
                success = await self._send_text(phone, content)
            else:
                logger.warning("⚠️  Sin contenido ni attachments")
            
            logger.info("=" * 70)
            return success
            
        except Exception as e:
            logger.error(f"❌ EXCEPCIÓN: {e}", exc_info=True)
            logger.info("=" * 70)
            return False
    
    async def _should_process(self, event_data: Dict[str, Any]) -> bool:
        """Valida si el evento debe procesarse"""
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
        
        sender_type = sender.get('type', '')
        if sender_type not in ('user', 'agent_bot'):
            logger.info(f"⏭️  Ignorado: sender.type={sender_type}")
            return False
        
        logger.info(f"✅ Válido - enviar a WhatsApp")
        return True
    
    def _extract_phone(self, conversation: Dict[str, Any]) -> str:
        """Extrae teléfono de la conversación"""
        contact_inbox = conversation.get('contact_inbox', {})
        source_id = contact_inbox.get('source_id', '')
        return source_id.replace('+', '').replace('group_', '')
    
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
        """Despacha según tipo de multimedia"""
        file_type = attachment.get('file_type', 'unknown')
        data_url = attachment.get('data_url', '')
        file_name = attachment.get('file_name', 'archivo')
        
        logger.info(f"📦 Enviando {file_type.upper()}")
        logger.info(f"   📄 Filename: {file_name}")
        logger.info(f"   🔗 URL: {data_url[:60]}...")
        
        if not data_url:
            logger.error("❌ Sin data_url")
            return False
        
        if file_type == 'image':
            return await self.wuzapi.send_image_message(phone, data_url, content or '')
        
        elif file_type == 'video':
            return await self.wuzapi.send_video_message(phone, data_url, content or '')
        
        elif file_type == 'audio':
            # 🔥 Llamar al método especializado de audio
            return await self._send_audio(phone, data_url)
        
        elif file_type == 'file':
            return await self.wuzapi.send_document_message(phone, data_url, file_name)
        
        else:
            logger.warning(f"⚠️  Tipo '{file_type}' no soportado, enviando como texto")
            fallback = f"{content}\n\n[Archivo: {file_name}]" if content else f"[Archivo: {file_name}]"
            return await self.wuzapi.send_text_message(phone, fallback)
    
    # ==================== MÉTODO DE AUDIO ====================
    
    async def _send_audio(self, phone: str, audio_url: str) -> bool:
        """
        Envía audio con conversión automática si es necesario.
        
        Flujo (SRP):
        1. Descargar audio desde URL de Chatwoot
        2. Detectar formato
        3. Si WAV/MP3 → Convertir a OGG Opus
        4. Enviar a WhatsApp
        5. Si conversión falla → Enviar como documento
        """
        try:
            # 1️⃣ Descargar audio
            logger.info(f"⬇️  Descargando audio...")
            audio_bytes, content_type = await self._download_file(audio_url)
            
            if not audio_bytes:
                logger.error("❌ Error descargando audio")
                return False
            
            logger.info(f"✅ Descargado: {len(audio_bytes)} bytes")
            logger.info(f"📦 Content-Type: {content_type}")
            
            # 2️⃣ Verificar si necesita conversión
            if self.audio_converter and self.audio_converter.needs_conversion(content_type):
                logger.info(f"🔄 Formato {content_type} requiere conversión a OGG Opus...")
                
                # 3️⃣ Verificar disponibilidad de ffmpeg
                if not self.audio_converter.is_conversion_available():
                    logger.warning("⚠️  FFmpeg no disponible")
                    logger.info("📄 Enviando como DOCUMENTO (fallback)")
                    return await self._send_audio_as_document(phone, audio_bytes, content_type)
                
                # 4️⃣ Convertir a OGG Opus
                ogg_bytes = await self.audio_converter.convert_to_ogg_opus(
                    audio_bytes, content_type
                )
                
                if not ogg_bytes:
                    logger.error("❌ Conversión falló")
                    logger.info("📄 Enviando como DOCUMENTO (fallback)")
                    return await self._send_audio_as_document(phone, audio_bytes, content_type)
                
                audio_bytes = ogg_bytes
                content_type = 'audio/ogg; codecs=opus'
                logger.info(f"✅ Convertido a OGG Opus: {len(audio_bytes)} bytes")
            
            

            duration = 0
            if self.audio_converter:
                duration = self.audio_converter.get_duration_seconds(audio_bytes)
                logger.info(f"⏱️  Duración: {duration} segundos")


            waveform = []
            if self.audio_converter:
                waveform = self.audio_converter.get_waveform(audio_bytes)
                logger.info(f"📊 Waveform: {len(waveform)} puntos")    

             # 5️⃣ Enviar como PTT
            logger.info("🎤 Enviando como nota de voz (PTT)...")   
            # 7️⃣ Enviar como PTT (modificar llamada existente)
            success = await self.wuzapi.send_audio_message(
                phone, audio_bytes, content_type, duration, waveform  # 🔥 Agregar duration y waveform
            )
            
            if success:
                logger.info("✅ AUDIO enviado")
            else:
                logger.error("❌ Error enviando audio")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Excepción en _send_audio: {e}", exc_info=True)
            return False
    
    async def _download_file(self, url: str) -> tuple[Optional[bytes], str]:
        """
        Descarga archivo desde URL.
        
        Returns:
            Tuple de (bytes, content_type) o (None, '') si falla
        """
        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.error(f"❌ HTTP {response.status_code}")
                    return None, ''
                
                return response.content, response.headers.get('content-type', '')
                
        except Exception as e:
            logger.error(f"❌ Error descargando: {e}")
            return None, ''
    
    async def _send_audio_as_document(
        self, 
        phone: str, 
        audio_bytes: bytes, 
        content_type: str
    ) -> bool:
        """
        Envía audio como documento adjunto (fallback cuando no hay ffmpeg).
        
        El audio llegará como archivo reproducible, no como nota de voz.
        """
        try:
            import base64
            
            # Determinar extensión
            if 'wav' in content_type:
                ext = 'wav'
                mime = 'audio/wav'
            elif 'mp3' in content_type or 'mpeg' in content_type:
                ext = 'mp3'
                mime = 'audio/mpeg'
            else:
                ext = 'ogg'
                mime = 'audio/ogg'
            
            filename = f"audio.{ext}"
            
            # Convertir a data URI
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            data_uri = f"data:application/octet-stream;base64,{audio_base64}"
            
            logger.info(f"📄 Enviando audio como documento: {filename}")
            
            # Usar endpoint de documento
            success = await self.wuzapi.send_document_message(phone, data_uri, filename)
            
            if success:
                logger.info("✅ Audio enviado como documento")
            else:
                logger.error("❌ Error enviando documento")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en fallback documento: {e}")
            return False