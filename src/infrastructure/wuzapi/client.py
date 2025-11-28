"""
src/infrastructure/wuzapi/client.py
Cliente HTTP para comunicación con WuzAPI
"""
import logging
from typing import Optional, Dict, Any, Literal,List
import httpx
from urllib.parse import urlencode
import base64 

logger = logging.getLogger(__name__)


MediaType = Literal['audio', 'image', 'video', 'document']


class WuzAPIClient:
    """
    Adaptador que implementa la comunicación con WuzAPI via HTTP.
    
    Responsabilidades:
    - Envío de mensajes (texto, multimedia)
    - Descarga de archivos multimedia
    """
    
    def __init__(
        self,
        base_url: str,
        user_token: str,
        instance_token: str,
        cache_repo=None,  # 🔥 NUEVO PARÁMETRO
        timeout: int = 90
    ):
        """
        Args:
            base_url: URL base de WuzAPI
            user_token: Token de usuario para autenticación
            instance_token: Token de instancia
            timeout: Timeout en segundos para requests
        """
        self.base_url = base_url.rstrip('/')
        self.user_token = user_token
        self.instance_token = instance_token
        self.cache_repo = cache_repo  # 🔥 NUEVO
        self.timeout = timeout
        
        self.headers = {
            'token': user_token,
            'Content-Type': 'application/json'
        }
        
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=self.headers,
            timeout=timeout
        )
        
        logger.info(f"🟢 WuzAPIClient inicializado")
        logger.info(f"🌐 Base URL: {base_url}")
        logger.info(f"🔑 User Token: {user_token[:20]}...")
        logger.info(f"🔑 Instance Token: {instance_token[:20]}...")
    
    # ==================== MÉTODOS DE ENVÍO ====================
    
    async def send_text_message(
        self, 
        phone: str, 
        message: str
    ) -> bool:
        """
        Envía mensaje de texto a través de WuzAPI.
        
        🔥 NUEVO: Guarda message_id en caché para detectar loops
        """
        try:
            phone_clean = phone.replace('+', '')
            
            url = "/chat/send/text"
            
            data = {
                'Phone': phone_clean,
                'Body': message
            }
            
            headers = {
                'token': self.instance_token,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"📤 Enviando texto a {phone_clean}")
            logger.info(f"📍 URL: {url}")
            logger.info(f"📦 Data: {data}")
            
            response = await self.client.post(url, json=data, headers=headers)
            
            logger.info(f"📡 Status: {response.status_code}")
            logger.info(f"📡 Response: {response.text[:200]}")
            
            if response.status_code in [200, 201]:
                # 🔥 NUEVO: Guardar message_id en caché
                if self.cache_repo:
                    try:
                        result = response.json()
                        msg_id = result.get('data', {}).get('Id')
                        
                        if msg_id:
                            cache_key = f"sent_from_chatwoot:{msg_id}"
                            # Guardar por 30 segundos (suficiente para el webhook)
                            await self.cache_repo.set_conversation_id(cache_key, "1", ttl=30)
                            logger.info(f"📝 Cacheado msg_id: {msg_id}")
                    except Exception as e:
                        logger.debug(f"⚠️  Error cacheando msg_id: {e}")
                
                logger.info(f"✅ Texto enviado")
                return True
            else:
                logger.error(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción: {e}", exc_info=True)
            return False
        

    async def send_image_message(
        self, 
        phone: str, 
        image_url: str, 
        caption: str = ""
    ) -> bool:
        """
        Envía imagen a través de WuzAPI.
        
        Args:
            phone: Número de teléfono
            image_url: URL pública de la imagen
            caption: Texto que acompaña la imagen
            
        Returns:
            True si fue exitoso, False si falló
        """
        try:
            phone_clean = phone.replace('+', '')
            
            # 🔥 ENDPOINT CORRECTO
            url = "/chat/send/image"
            
            # 🔥 FORMATO CORRECTO (capitalizado como la API lo requiere)
            data = {
                'Phone': phone_clean,
                'Image': image_url,
                'Caption': caption or ''
            }
            
            # 🔥 HEADERS CON INSTANCE TOKEN
            headers = {
                'token': self.instance_token,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"📤 Enviando imagen a {phone_clean}")
            logger.info(f"📍 URL: {url}")
            logger.info(f"📦 Caption: {caption[:50] if caption else '(sin caption)'}...")
            
            response = await self.client.post(url, json=data, headers=headers)
            
            logger.info(f"📡 Status: {response.status_code}")
            logger.info(f"📡 Response: {response.text[:200]}")
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Imagen enviada")
                return True
            else:
                logger.error(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción enviando imagen: {e}", exc_info=True)
            return False
    
    async def send_video_message(self, phone: str, video_url: str, caption: str = "") -> bool:
        """Envía video a través de WuzAPI."""
        try:
            phone_clean = phone.replace('+', '')
            
            url = "/chat/send/video"
            
            data = {
                'Phone': phone_clean,
                'Video': video_url,
                'Caption': caption or ''
            }
            
            headers = {
                'token': self.instance_token,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"📤 Enviando video a {phone_clean}")
            logger.info(f"📍 URL: {url}")
            
            response = await self.client.post(url, json=data, headers=headers)
            
            logger.info(f"📡 Status: {response.status_code}")
            logger.info(f"📡 Response: {response.text[:200]}")
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Video enviado")
                return True
            else:
                logger.error(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción enviando video: {e}", exc_info=True)
            return False

    async def send_document_message(self, phone: str, document_url: str, filename: str) -> bool:
        """Envía documento a través de WuzAPI."""
        try:
            phone_clean = phone.replace('+', '')
            
            url = "/chat/send/document"
            
            data = {
                'Phone': phone_clean,
                'Document': document_url,
                'FileName': filename
            }
            
            headers = {
                'token': self.instance_token,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"📤 Enviando documento a {phone_clean}")
            logger.info(f"📍 URL: {url}")
            logger.info(f"📄 Filename: {filename}")
            
            response = await self.client.post(url, json=data, headers=headers)
            
            logger.info(f"📡 Status: {response.status_code}")
            logger.info(f"📡 Response: {response.text[:200]}")
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Documento enviado")
                return True
            else:
                logger.error(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción enviando documento: {e}", exc_info=True)
            return False
    
    async def send_audio_message(
        self, 
        phone: str, 
        audio_bytes: bytes,
        mime_type: str = 'audio/ogg; codecs=opus',
        seconds: int = 0,  # 🔥 NUEVO,
        waveform: List[int] = None  # 🔥 NUEVO
    ) -> bool:
        """
        Envía audio a través de WuzAPI.
        
        IMPORTANTE: El audio DEBE estar en formato OGG Opus para PTT.
        La conversión debe hacerse ANTES de llamar a este método.
        
        Args:
            phone: Número de teléfono
            audio_bytes: Bytes del audio (ya convertido a OGG)
            mime_type: MIME type del audio
        """
        try:
            phone_clean = phone.replace('+', '')
            
            logger.info(f"📤 Enviando audio a {phone_clean}")
            logger.info(f"📦 Tamaño: {len(audio_bytes)} bytes")
            logger.info(f"📦 MimeType: {mime_type}")
            
            # Convertir a base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            data_uri = f"data:audio/ogg;base64,{audio_base64}"
            
            url = "/chat/send/audio"
            data = {
                'Phone': phone_clean,
                'Audio': data_uri,
                'PTT': True,
                'MimeType': mime_type,
                'Seconds': seconds ,  # 🔥 NUEVO
                'Waveform': waveform  # 🔥 NUEVO
            }
            
            headers = {
                'token': self.instance_token,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"📍 URL: {url}")
            logger.info(f"🎤 PTT: True")
            
            response = await self.client.post(url, json=data, headers=headers)
            
            logger.info(f"📡 Status: {response.status_code}")
            logger.info(f"📡 Response: {response.text[:200]}")
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Audio enviado")
                return True
            else:
                logger.error(f"❌ Error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción: {e}", exc_info=True)
            return False
    
    
    # ==================== MÉTODOS DE DESCARGA ====================
    
    async def download_audio(
        self,
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Descarga archivo de audio usando endpoint oficial de WuzAPI.
        
        Args:
            message_id: ID del mensaje de WhatsApp (Info.ID)
            
        Returns:
            Dict con file_data (bytes), filename, mimetype, size_bytes o None si falla
        """
        return await self._download_media(message_id, 'audio')
    
    async def download_image(
        self,
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Descarga imagen usando endpoint oficial de WuzAPI.
        
        Args:
            message_id: ID del mensaje de WhatsApp (Info.ID)
            
        Returns:
            Dict con file_data (bytes), filename, mimetype, size_bytes o None si falla
        """
        return await self._download_media(message_id, 'image')
    
    async def download_video(
        self,
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Descarga video usando endpoint oficial de WuzAPI.
        
        Args:
            message_id: ID del mensaje de WhatsApp (Info.ID)
            
        Returns:
            Dict con file_data (bytes), filename, mimetype, size_bytes o None si falla
        """
        return await self._download_media(message_id, 'video')
    
    async def download_document(
        self,
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Descarga documento usando endpoint oficial de WuzAPI.
        
        Args:
            message_id: ID del mensaje de WhatsApp (Info.ID)
            
        Returns:
            Dict con file_data (bytes), filename, mimetype, size_bytes o None si falla
        """
        return await self._download_media(message_id, 'document')
    
    async def _download_media(
        self,
        message_id: str,
        media_type: MediaType
    ) -> Optional[Dict[str, Any]]:
        """
        Método interno para descargar multimedia usando endpoints oficiales.
        
        Args:
            message_id: ID del mensaje
            media_type: Tipo de multimedia
            
        Returns:
            Dict con datos del archivo o None
        """
        try:
            logger.info("=" * 70)
            logger.info(f"⬇️  DESCARGANDO {media_type.upper()} DESDE WUZAPI")
            logger.info("=" * 70)
            logger.info(f"📥 Message ID: {message_id}")
            
            # Construir endpoint
            endpoint = self._get_download_endpoint(media_type)
            
            # Construir URL con parámetros
            params = {
                'messageId': message_id,
                'token': self.instance_token
            }
            
            url_with_params = f"{endpoint}?{urlencode(params)}"
            
            logger.info(f"🌐 Endpoint: {endpoint}")
            logger.info(f"🌐 URL (truncada): {self.base_url}{url_with_params[:60]}...")
            
            # Realizar descarga
            response = await self.client.get(url_with_params)
            
            logger.info(f"📡 Status Code: {response.status_code}")
            logger.info(f"📡 Content-Type: {response.headers.get('content-type')}")
            logger.info(f"📡 Content-Length: {response.headers.get('content-length')}")
            
            if response.status_code != 200:
                logger.error(f"❌ Error descargando: HTTP {response.status_code}")
                logger.error(f"❌ Response: {response.text[:500]}")
                return None
            
            file_data = response.content
            content_type = response.headers.get('content-type', '')
            
            logger.info(f"✅ Descarga exitosa")
            logger.info(f"📦 Tamaño: {len(file_data)} bytes ({len(file_data)/1024:.1f} KB)")
            logger.info("=" * 70)
            
            return {
                'file_data': file_data,
                'filename': f"{message_id}.{self._get_extension(content_type, media_type)}",
                'mimetype': content_type or self._get_default_mimetype(media_type),
                'size_bytes': len(file_data)
            }
            
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ EXCEPCIÓN EN DESCARGA DE {media_type.upper()}")
            logger.error(f"❌ Error: {e}", exc_info=True)
            logger.error("=" * 70)
            return None
    
    def _get_download_endpoint(self, media_type: MediaType) -> str:
        """Retorna el endpoint de descarga según tipo de media"""
        endpoints = {
            'audio': '/chat/downloadaudio',
            'image': '/chat/downloadimage',
            'video': '/chat/downloadvideo',
            'document': '/chat/downloaddocument'
        }
        return endpoints[media_type]
    
    def _get_extension(self, content_type: str, media_type: str) -> str:
        """Determina la extensión del archivo"""
        content_type_map = {
            'audio/ogg': 'ogg',
            'audio/mpeg': 'mp3',
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/webp': 'webp',
            'video/mp4': 'mp4',
            'application/pdf': 'pdf',
        }
        
        if content_type in content_type_map:
            return content_type_map[content_type]
        
        type_fallback = {
            'audio': 'ogg',
            'image': 'jpg',
            'video': 'mp4',
            'document': 'pdf',
        }
        
        return type_fallback.get(media_type, 'bin')
    
    def _get_default_mimetype(self, media_type: str) -> str:
        """MIME type por defecto según tipo"""
        defaults = {
            'audio': 'audio/ogg',
            'image': 'image/jpeg',
            'video': 'video/mp4',
            'document': 'application/pdf',
        }
        return defaults.get(media_type, 'application/octet-stream')
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
        logger.info("👋 WuzAPIClient cerrado")


    async def get_user_avatar(
        self,
        phone: str,
        preview: bool = False
    ) -> Optional[str]:
        """
        Obtiene la URL del avatar/foto de perfil de un usuario de WhatsApp.
        
        Args:
            phone: Número de teléfono (con o sin formato WhatsApp)
            preview: Si es True, obtiene versión preview (96x96), si False obtiene full
            
        Returns:
            URL de la imagen o None si falla
        """
        try:
            # Limpiar número
            phone_clean = phone.replace('+', '').replace('@s.whatsapp.net', '').replace('@newsletter', '').replace('group_', '')
            
            url = "/user/avatar"
            data = {
                'Phone': phone_clean,
                'Preview': preview
            }
            
            # 🔥 CRÍTICO: Este endpoint requiere INSTANCE TOKEN, no USER TOKEN
            headers = {
                'token': self.instance_token,  # ← CAMBIO: Usar instance_token
                'Content-Type': 'application/json'
            }
            
            logger.debug(f"🖼️  Obteniendo avatar de {phone_clean}...")
            
            response = await self.client.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success') or result.get('code') == 200:
                    avatar_data = result.get('data', {})
                    avatar_url = avatar_data.get('url', '')
                    
                    if avatar_url:
                        logger.debug(f"✅ Avatar obtenido: {avatar_url[:60]}...")
                        return avatar_url
            
            logger.debug(f"⚠️  Sin avatar para {phone_clean}")
            return None
            
        except Exception as e:
            logger.debug(f"⚠️  Error obteniendo avatar: {e}")
            return None
        


 