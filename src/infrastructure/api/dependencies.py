"""
src/infrastructure/api/dependencies.py

Dependency Injection Container para FastAPI.

Responsabilidades:
- Crear y cachear instancias de clientes (singletons)
- Inyectar dependencias en handlers y use cases
- Facilitar testing (mockear dependencias)
- Gestionar ciclo de vida de conexiones

Patrón usado: Dependency Injection + Singleton
"""
import logging
from functools import lru_cache
from typing import Optional

from ...shared.config import Settings
from ...infrastructure.chatwoot.client import ChatwootClient
from ...infrastructure.wuzapi.client import WuzAPIClient
from ...infrastructure.persistence.redis_cache import RedisCache
from ...infrastructure.persistence.memory_cache import InMemoryCache
from ...infrastructure.media.media_downloader import MediaDownloader
from ...application.use_cases.sync_message_to_chatwoot import SyncMessageToChatwootUseCase
from ...application.use_cases.send_message_to_whatsapp import SendMessageToWhatsAppUseCase
from .handlers.wuzapi_handler import WuzAPIWebhookHandler
from .handlers.chatwoot_handler import ChatwootWebhookHandler
from ...infrastructure.media.audio_converter import FFmpegAudioConverter 
from ...infrastructure.chatwoot.session_notifier import ChatwootSessionNotifier
from ...application.use_cases.handle_qr_event import HandleQREventUseCase
from ...infrastructure.wuzapi.session_client import WuzAPISessionClient
from ...application.use_cases.handle_session_command import HandleSessionCommandUseCase
logger = logging.getLogger(__name__)

# ==================== CONFIGURACIÓN ====================

@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instancia de Settings (singleton).
    
    El decorador @lru_cache hace que se cree solo una vez
    y se reutilice en todas las llamadas.
    
    Returns:
        Instancia de Settings con variables de entorno
    """
    return Settings()


# ==================== CLIENTES HTTP (SINGLETONS) ====================

_chatwoot_client: Optional[ChatwootClient] = None
_wuzapi_client: Optional[WuzAPIClient] = None
_cache_client = None
_media_downloader: Optional[MediaDownloader] = None
_audio_converter: Optional[FFmpegAudioConverter] = None  # 🔥 NUEVO
_session_notifier: Optional[ChatwootSessionNotifier] = None
_session_client: Optional[WuzAPISessionClient] = None


def get_chatwoot_client() -> ChatwootClient:
    """
    Retorna instancia de ChatwootClient (singleton).
    
    Se crea una sola vez y se reutiliza en toda la aplicación.
    Esto es eficiente porque mantiene el pool de conexiones HTTP.
    
    Returns:
        Instancia de ChatwootClient
    """
    global _chatwoot_client
    
    if _chatwoot_client is None:
        settings = get_settings()
        _chatwoot_client = ChatwootClient(
            base_url=settings.CHATWOOT_URL,
            api_key=settings.CHATWOOT_API_KEY,
            account_id=settings.CHATWOOT_ACCOUNT_ID,
            inbox_id=settings.CHATWOOT_INBOX_ID
        )
        logger.info("✅ ChatwootClient inicializado")
    
    return _chatwoot_client


def get_wuzapi_client() -> WuzAPIClient:
    """
    Retorna instancia de WuzAPIClient (singleton).
    
    Se crea una sola vez y se reutiliza en toda la aplicación.
    Esto es eficiente porque mantiene el pool de conexiones HTTP.
    
    Returns:
        Instancia de WuzAPIClient
    """
    global _wuzapi_client
    
    if _wuzapi_client is None:
        settings = get_settings()
        _wuzapi_client = WuzAPIClient(
            base_url=settings.WUZAPI_URL,
            user_token=settings.WUZAPI_USER_TOKEN,
            instance_token=settings.WUZAPI_INSTANCE_TOKEN
        )
        logger.info("✅ WuzAPIClient inicializado")
    
    return _wuzapi_client


async def get_cache_client():
    """
    Retorna instancia de CacheClient (singleton).
    
    Intenta conectar a Redis, si falla usa caché en memoria.
    
    Returns:
        RedisCache o InMemoryCache según disponibilidad
    """
    global _cache_client
    
    if _cache_client is None:
        settings = get_settings()
        
        try:
            _cache_client = RedisCache(settings.REDIS_URL)
            await _cache_client.connect()
            logger.info("✅ Redis conectado")
        except Exception as e:
            logger.warning(f"⚠️  Redis no disponible: {e}")
            logger.warning(f"⚠️  Usando caché en memoria")
            _cache_client = InMemoryCache()
            await _cache_client.connect()
    
    return _cache_client


def get_media_downloader() -> MediaDownloader:
    """
    Retorna instancia de MediaDownloader (singleton).
    
    Returns:
        Instancia de MediaDownloader
    """
    global _media_downloader
    
    if _media_downloader is None:
        settings = get_settings()
        _media_downloader = MediaDownloader(
            wuzapi_base_url=settings.WUZAPI_URL,
            wuzapi_user_token=settings.WUZAPI_USER_TOKEN,
            wuzapi_instance_token=settings.WUZAPI_INSTANCE_TOKEN
        )
        logger.info("✅ MediaDownloader inicializado")
    
    return _media_downloader


# ==================== CASOS DE USO ====================

async def get_sync_to_chatwoot_use_case() -> SyncMessageToChatwootUseCase:
    """
    Retorna instancia de SyncMessageToChatwootUseCase.
    
    Inyecta todas las dependencias necesarias:
    - ChatwootClient (para API de Chatwoot)
    - CacheClient (para cachear conversation_id)
    - MediaDownloader (para descargar multimedia)
    - WuzAPIClient (para obtener avatares)
    
    Returns:
        Instancia del caso de uso con dependencias inyectadas
    """
    return SyncMessageToChatwootUseCase(
        chatwoot_repo=get_chatwoot_client(),
        cache_repo=await get_cache_client(),
        media_downloader=get_media_downloader(),
        wuzapi_repo=get_wuzapi_client()
    )


async def get_send_to_whatsapp_use_case() -> SendMessageToWhatsAppUseCase:
    """
    Retorna instancia de SendMessageToWhatsAppUseCase.
    """
    settings = get_settings()  # 🔥 AGREGAR ESTA LÍNEA
    
    return SendMessageToWhatsAppUseCase(
        wuzapi_repo=get_wuzapi_client(),
        cache_repo=await get_cache_client(),
        audio_converter=get_audio_converter(),
        command_use_case=get_command_use_case(),
        session_source_id=settings.WUZAPI_SESSION_SOURCE_ID
    )


# ==================== HANDLERS ====================

async def get_wuzapi_handler() -> WuzAPIWebhookHandler:
    """
    Retorna instancia de WuzAPIWebhookHandler.
    """
    settings = get_settings()
    sync_use_case = await get_sync_to_chatwoot_use_case()
    
    return WuzAPIWebhookHandler(
        sync_use_case=sync_use_case,
        expected_instance_id=settings.WUZAPI_INSTANCE_ID,
        qr_use_case=get_qr_use_case(),              # 🔥 NUEVO
        session_notifier=get_session_notifier()     # 🔥 NUEVO
    )


async def get_chatwoot_handler() -> ChatwootWebhookHandler:
    """
    Retorna instancia de ChatwootWebhookHandler.
    
    Inyecta:
    - SendMessageToWhatsAppUseCase
    
    Returns:
        Handler configurado para procesar webhooks de Chatwoot
    """
    # 🔥 CAMBIO CRÍTICO: Agregamos 'await' porque la dependencia es asíncrona
    send_use_case = await get_send_to_whatsapp_use_case()
    
    return ChatwootWebhookHandler(send_use_case=send_use_case)


# ==================== LIMPIEZA DE RECURSOS ====================

async def cleanup_dependencies():
    """
    Limpia recursos al cerrar la aplicación.
    
    Cierra conexiones HTTP y cache.
    Debe ser llamado en el shutdown del lifespan.
    """
    global _chatwoot_client, _wuzapi_client, _cache_client, _media_downloader
    
    if _chatwoot_client:
        await _chatwoot_client.close()
        logger.info("👋 ChatwootClient cerrado")
        _chatwoot_client = None
    
    if _wuzapi_client:
        await _wuzapi_client.close()
        logger.info("👋 WuzAPIClient cerrado")
        _wuzapi_client = None
    
    if _cache_client:
        await _cache_client.close()
        logger.info("👋 CacheClient cerrado")
        _cache_client = None
    
    if _media_downloader:
        await _media_downloader.close()
        logger.info("👋 MediaDownloader cerrado")
        _media_downloader = None


# 🔥🔥🔥 NUEVO: Factory para AudioConverter 🔥🔥🔥
def get_audio_converter() -> FFmpegAudioConverter:
    """
    Retorna instancia del conversor de audio.
    Verifica disponibilidad de ffmpeg al inicializar.
    """
    global _audio_converter
    if _audio_converter is None:
        _audio_converter = FFmpegAudioConverter()
        if _audio_converter.is_conversion_available():
            logger.info("✅ AudioConverter (FFmpeg) disponible")
        else:
            logger.warning("⚠️  FFmpeg NO disponible - audios se enviarán como documento")
    return _audio_converter


def get_session_notifier() -> ChatwootSessionNotifier:
    """
    Retorna instancia de SessionNotifier (singleton).
    """
    global _session_notifier
    
    if _session_notifier is None:
        settings = get_settings()
        _session_notifier = ChatwootSessionNotifier(
            chatwoot_client=get_chatwoot_client(),
            contact_name=settings.WUZAPI_SESSION_CONTACT_NAME,
            source_id=settings.WUZAPI_SESSION_SOURCE_ID
        )
        logger.info("✅ SessionNotifier inicializado")
    
    return _session_notifier


def get_qr_use_case() -> HandleQREventUseCase:
    """
    Retorna instancia de HandleQREventUseCase.
    """
    return HandleQREventUseCase(notifier=get_session_notifier())


def get_session_client() -> WuzAPISessionClient:
    """
    Retorna instancia de WuzAPISessionClient (singleton).
    """
    global _session_client
    
    if _session_client is None:
        settings = get_settings()
        _session_client = WuzAPISessionClient(
            base_url=settings.WUZAPI_URL,
            user_token=settings.WUZAPI_USER_TOKEN,
            instance_token=settings.WUZAPI_INSTANCE_TOKEN  # 🔥 AGREGAR
        )
        logger.info("✅ WuzAPISessionClient inicializado")
    
    return _session_client


def get_command_use_case() -> HandleSessionCommandUseCase:
    """
    Retorna instancia de HandleSessionCommandUseCase.
    """
    return HandleSessionCommandUseCase(
        session_repo=get_session_client(),
        notifier=get_session_notifier()
    )    