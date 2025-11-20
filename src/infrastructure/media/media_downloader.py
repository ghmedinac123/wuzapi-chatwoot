"""
src/infrastructure/media/media_downloader.py
Descargador usando endpoints REALES de WuzAPI
"""
import logging
import httpx
import base64
import re
from typing import Optional, Dict, Any, Literal
import hashlib
from datetime import datetime


logger = logging.getLogger(__name__)


MediaType = Literal['audio', 'image', 'video', 'document']


class MediaDownloader:
    """Descarga multimedia desde WuzAPI usando endpoints oficiales"""
    
    def __init__(
        self,
        wuzapi_base_url: str,
        wuzapi_user_token: str,
        wuzapi_instance_token: str
    ):
        self.wuzapi_base_url = wuzapi_base_url.rstrip('/')
        self.wuzapi_user_token = wuzapi_user_token
        self.wuzapi_instance_token = wuzapi_instance_token
        
        self.http_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                'token': wuzapi_user_token,
                'Content-Type': 'application/json'
            }
        )
        
        logger.info(f"📥 MediaDownloader inicializado")
    
    async def download_from_wuzapi_endpoint(
        self,
        message_id: str,
        media_type: MediaType,
        media_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Descarga multimedia usando endpoints de WuzAPI"""
        try:
            logger.info("=" * 70)
            logger.info("⬇️  DESCARGA DESDE WUZAPI")
            logger.info("=" * 70)
            
            endpoint = self._get_endpoint(media_type)
            url = f"{self.wuzapi_base_url}{endpoint}"
            
            logger.info(f"🌐 URL: {url}")
            
            # USAR INSTANCE_TOKEN EN HEADER (no user_token)
            headers = {
                'token': self.wuzapi_instance_token,
                'Content-Type': 'application/json'
            }
            
            logger.info("🌐 POST con instance token...")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=media_info, headers=headers, timeout=60.0)
            
            logger.info(f"📡 Status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ Error: {response.text}")
                return None
            
            data = response.json()
            
            if not data.get('success'):
                return None
            
            data_url = data.get('data', {}).get('Data', '')
            mimetype = data.get('data', {}).get('Mimetype', '')
            
            if not data_url:
                return None
            
            if 'base64,' in data_url:
                base64_str = data_url.split('base64,')[1]
            else:
                base64_str = data_url
            
            file_data = base64.b64decode(base64_str)
            filename = self._generate_filename(file_data, media_type, mimetype)
            
            logger.info(f"✅ {len(file_data)} bytes - {filename}")
            logger.info("=" * 70)
            
            return {
                'file_data': file_data,
                'filename': filename,
                'mimetype': mimetype or self._get_default_mimetype(media_type),
                'size_bytes': len(file_data)
            }
            
        except Exception as e:
            logger.error(f"❌ {e}", exc_info=True)
            return None
    
    def _get_endpoint(self, media_type: MediaType) -> str:
        """Endpoint según tipo"""
        endpoints = {
            'audio': '/chat/downloadaudio',
            'image': '/chat/downloadimage',
            'video': '/chat/downloadvideo',
            'document': '/chat/downloaddocument'
        }
        return endpoints[media_type]
    
    def _generate_filename(
        self,
        content: bytes,
        file_type: str,
        content_type: str
    ) -> str:
        """Genera nombre único"""
        content_hash = hashlib.md5(content).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = self._get_extension(content_type, file_type)
        return f"{timestamp}_{content_hash}.{extension}"
    
    def _get_extension(self, content_type: str, file_type: str) -> str:
        """Determina extensión"""
        content_type_map = {
            'audio/ogg': 'ogg',
            'audio/ogg; codecs=opus': 'ogg',
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
        return type_fallback.get(file_type, 'bin')
    
    def _get_default_mimetype(self, file_type: str) -> str:
        """MIME type por defecto"""
        defaults = {
            'audio': 'audio/ogg',
            'image': 'image/jpeg',
            'video': 'video/mp4',
            'document': 'application/pdf',
        }
        return defaults.get(file_type, 'application/octet-stream')
    
    async def close(self):
        """Cierra cliente HTTP"""
        await self.http_client.aclose()
        logger.info("👋 MediaDownloader cerrado")