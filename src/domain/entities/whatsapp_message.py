"""
src/domain/entities/whatsapp_message.py
Entidad con lógica mejorada para extraer CAPTIONS de multimedia.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import json
from ..value_objects.phone_number import PhoneNumber
from ..value_objects.message_type import MessageType, TYPE_MAPPINGS

logger = logging.getLogger(__name__)

@dataclass
class WhatsAppMessage:
    """Entidad rica que representa un mensaje de WhatsApp"""
    
    message_id: str
    sender: PhoneNumber
    timestamp: datetime
    message_type: MessageType
    is_from_me: bool
    is_group: bool
    raw_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_incoming(self) -> bool:
        return not self.is_from_me
    
    # 🔥🔥🔥 MÉTODO CORREGIDO AQUÍ 🔥🔥🔥
    def extract_text_content(self) -> str:
        """
        Extrae el contenido de texto del mensaje.
        Soporta texto plano Y captions (pies de foto) de multimedia.
        """
        try:
            message_data = self.raw_data.get('event', {}).get('Message', {})
            
            # 1. Texto plano simple
            if 'conversation' in message_data:
                return message_data['conversation']
            
            # 2. Texto extendido (respuestas, enlaces)
            if 'extendedTextMessage' in message_data:
                return message_data['extendedTextMessage'].get('text', '')
            
            # 3. 🔥 CORRECCIÓN: Extraer Caption de Imagen
            if 'imageMessage' in message_data:
                return message_data['imageMessage'].get('caption', '')

            # 4. 🔥 CORRECCIÓN: Extraer Caption de Video
            if 'videoMessage' in message_data:
                return message_data['videoMessage'].get('caption', '')
                
            # 5. 🔥 CORRECCIÓN: Extraer Caption de Documento
            if 'documentMessage' in message_data:
                return message_data['documentMessage'].get('caption', '')
            if 'documentWithCaptionMessage' in message_data:
                doc = message_data['documentWithCaptionMessage'].get('message', {}).get('documentMessage', {})
                return doc.get('caption', '')

            return ""
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo texto: {e}")
            return ""
    # 🔥🔥🔥 FIN MÉTODO CORREGIDO 🔥🔥🔥

    def extract_image_info(self) -> Optional[Dict[str, str]]:
        """Extrae información de una imagen"""
        try:
            if self.message_type not in [MessageType.IMAGE]:
                return None
            
            message_data = self.raw_data.get('event', {}).get('Message', {})
            image_msg = message_data.get('imageMessage', {})
            
            if not image_msg:
                return None
            
            url = image_msg.get('url', '')
            mimetype = image_msg.get('mimetype', 'image/jpeg')
            caption = image_msg.get('caption', '')
            
            return {
                'url': url,
                'mimetype': mimetype,
                'caption': caption
            }
        except Exception as e:
            logger.error(f"❌ Error extrayendo imagen: {e}", exc_info=True)
            return None
    
    def extract_video_info(self) -> Optional[Dict[str, str]]:
        """Extrae información de un video"""
        try:
            if self.message_type not in [MessageType.VIDEO]:
                return None
            
            message_data = self.raw_data.get('event', {}).get('Message', {})
            video_msg = message_data.get('videoMessage', {})
            
            if not video_msg:
                return None
            
            url = video_msg.get('url', '')
            mimetype = video_msg.get('mimetype', 'video/mp4')
            caption = video_msg.get('caption', '')
            
            return {
                'url': url,
                'mimetype': mimetype,
                'caption': caption
            }
        except Exception as e:
            logger.error(f"❌ Error extrayendo video: {e}", exc_info=True)
            return None
    
    def extract_audio_info(self) -> Optional[Dict[str, str]]:
        """Extrae información de un audio"""
        try:
            if self.message_type not in [MessageType.AUDIO, MessageType.PTT]:
                return None
            
            message_data = self.raw_data.get('event', {}).get('Message', {})
            
            # Buscar audioMessage
            audio_msg = message_data.get('audioMessage', {})
            
            if not audio_msg:
                # Intentar buscar en otras estructuras
                for key in message_data.keys():
                    if 'audio' in key.lower() or 'voice' in key.lower() or 'ptt' in key.lower():
                        audio_msg = message_data[key]
                        break
                
                if not audio_msg:
                    return None
            
            url = audio_msg.get('URL', '') 
            mimetype = audio_msg.get('mimetype', 'audio/ogg; codecs=opus')
            ptt = audio_msg.get('PTT', False)
            
            if not url:
                return None
            
            return {
                'url': url,
                'mimetype': mimetype,
                'ptt': str(ptt)
            }
        except Exception as e:
            logger.error(f"❌ EXCEPCIÓN extrayendo audio: {e}", exc_info=True)
            return None
    
    def extract_document_info(self) -> Optional[Dict[str, str]]:
        """Extrae información de un documento"""
        try:
            if self.message_type not in [MessageType.DOCUMENT]:
                return None
            
            message_data = self.raw_data.get('event', {}).get('Message', {})
            
            doc_msg = message_data.get('documentMessage', {})
            if not doc_msg:
                doc_msg = message_data.get('documentWithCaptionMessage', {}).get('message', {}).get('documentMessage', {})
            
            if not doc_msg:
                return None
            
            url = doc_msg.get('url', '')
            mimetype = doc_msg.get('mimetype', 'application/octet-stream')
            fileName = doc_msg.get('fileName', 'documento')
            
            return {
                'url': url,
                'mimetype': mimetype,
                'fileName': fileName
            }
        except Exception as e:
            logger.error(f"❌ Error extrayendo documento: {e}", exc_info=True)
            return None

    def extract_media_info(self) -> Optional[Dict[str, Any]]:
        """Extrae info de multimedia para descargar desde WuzAPI"""
        try:
            if not self.raw_data:
                return None
            
            message_content = self.raw_data.get('event', {}).get('Message', {})
            
            # Mapeo tipo → key en JSON
            type_keys = {
                MessageType.IMAGE: 'imageMessage',
                MessageType.VIDEO: 'videoMessage',
                MessageType.AUDIO: 'audioMessage',
                MessageType.PTT: 'audioMessage',
                MessageType.DOCUMENT: 'documentMessage'
            }
            
            key = type_keys.get(self.message_type)
            if not key:
                # Caso especial para documentos con caption
                if self.message_type == MessageType.DOCUMENT and 'documentWithCaptionMessage' in message_content:
                     media_obj = message_content.get('documentWithCaptionMessage', {}).get('message', {}).get('documentMessage', {})
                else:
                    return None
            else:
                media_obj = message_content.get(key, {})
            
            if not media_obj:
                return None
            
            # Devolver campos tal cual vienen
            required_fields = [
                'URL', 'url',
                'directPath',
                'mediaKey',
                'mimetype',
                'fileSha256', 'fileSHA256',
                'fileEncSha256', 'fileEncSHA256',
                'fileLength',
                'fileName',
                'PTT'
            ]
            
            result = {}
            for field in required_fields:
                if field in media_obj:
                    result[field] = media_obj[field]
            
            return result if result else None
            
        except:
            return None

    @classmethod
    def from_wuzapi_event(cls, event_data: Dict[str, Any]) -> Optional['WhatsAppMessage']:
        """Factory method: crea WhatsAppMessage desde evento de WuzAPI"""
        try:
            event_info = event_data.get('event', {})
            info = event_info.get('Info', {})
            
            message_id = info.get('ID')
            chat = info.get('Chat', '')
            is_from_me = info.get('IsFromMe', False)
            is_group = info.get('IsGroup', False)
            timestamp_str = info.get('Timestamp', '')
            type_str = info.get('Type', 'unknown')
            media_type_str = info.get('MediaType', '')
            
            # Fallback SenderAlt
            if '@lid' in chat:
                sender_alt = info.get('SenderAlt', '')
                if sender_alt and '@s.whatsapp.net' in sender_alt:
                    chat = sender_alt
                else:
                    return None
            
            if not message_id or not chat:
                return None
            
            sender = PhoneNumber.from_whatsapp_jid(chat)
            if not sender:
                return None
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
            
            if type_str == 'media' and media_type_str:
                type_str = media_type_str
            
            # Mapeo de tipo
            message_type = None
            try:
                message_type = MessageType(type_str)
            except ValueError:
                if type_str in TYPE_MAPPINGS:
                    message_type = TYPE_MAPPINGS[type_str]
                else:
                    # Inferencia simple
                    message_data = event_info.get('Message', {})
                    if 'audioMessage' in message_data: message_type = MessageType.AUDIO
                    elif 'imageMessage' in message_data: message_type = MessageType.IMAGE
                    elif 'videoMessage' in message_data: message_type = MessageType.VIDEO
                    elif 'documentMessage' in message_data: message_type = MessageType.DOCUMENT
                    else: message_type = MessageType.UNKNOWN

            # Metadata
            metadata = {}
            if is_group:
                metadata['group_id'] = chat
                metadata['sender_name'] = info.get('PushName', 'Usuario')
            else:
                metadata['PushName'] = info.get('PushName', '')
            
            return cls(
                message_id=message_id,
                sender=sender,
                timestamp=timestamp,
                message_type=message_type,
                is_from_me=is_from_me,
                is_group=is_group,
                raw_data=event_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Error parseando mensaje: {e}", exc_info=True)
            return None