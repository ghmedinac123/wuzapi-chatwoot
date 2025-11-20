"""
Adaptador: RedisCache
Implementación COMPLETA del puerto CacheRepository usando Redis
"""
import logging
from typing import Optional
import redis.asyncio as redis

from ...domain.ports.cache_repository import CacheRepository


logger = logging.getLogger(__name__)


class RedisCache(CacheRepository):
    """
    Adaptador que implementa caché usando Redis
    
    Usa prefijos para organizar las keys:
    - chatwoot:conv:{phone} → conversation_id
    - chatwoot:msg:{message_id} → flag de procesado
    """
    
    def __init__(self, redis_url: str):
        """
        Args:
            redis_url: URL de conexión (ej: redis://localhost:6379/0)
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
    
    # ========================================================================
    # CICLO DE VIDA
    # ========================================================================
    
    async def connect(self) -> bool:
        """Conecta a Redis"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Conectado a Redis")
            return True
        except Exception as e:
            logger.warning(f"⚠️  No se pudo conectar a Redis: {e}")
            self.redis_client = None
            return False
    
    async def close(self) -> None:
        """Cierra conexión a Redis"""
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("👋 Conexión Redis cerrada")
    
    # ========================================================================
    # CONVERSACIONES
    # ========================================================================
    
    async def get_conversation_id(self, phone: str) -> Optional[int]:
        """Obtiene ID de conversación desde caché"""
        if not self.redis_client:
            return None
        
        try:
            key = f"chatwoot:conv:{phone}"
            value = await self.redis_client.get(key)
            
            if value:
                logger.debug(f"🔍 Caché HIT: conv:{phone} → {value}")
                return int(value)
            else:
                logger.debug(f"🔍 Caché MISS: conv:{phone}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo de caché: {e}")
            return None
    
    async def set_conversation_id(
        self, 
        phone: str, 
        conversation_id: int, 
        ttl: int = 3600
    ) -> bool:
        """Guarda ID de conversación en caché"""
        if not self.redis_client:
            return False
        
        try:
            key = f"chatwoot:conv:{phone}"
            await self.redis_client.setex(key, ttl, str(conversation_id))
            logger.debug(f"💾 Caché SET: conv:{phone} → {conversation_id} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando en caché: {e}")
            return False
    
    async def delete_conversation_id(self, phone: str) -> bool:
        """Elimina conversación del caché"""
        if not self.redis_client:
            return False
        
        try:
            key = f"chatwoot:conv:{phone}"
            deleted = await self.redis_client.delete(key)
            
            if deleted:
                logger.debug(f"🗑️  Caché DELETE: conv:{phone}")
            
            return bool(deleted)
        except Exception as e:
            logger.error(f"❌ Error eliminando de caché: {e}")
            return False
    
    # ========================================================================
    # IDEMPOTENCIA (Mensajes Procesados)
    # ========================================================================
    
    async def has_processed_message(self, message_id: str) -> bool:
        """
        Verifica si un mensaje ya fue procesado
        
        Key: chatwoot:msg:{message_id}
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"chatwoot:msg:{message_id}"
            exists = await self.redis_client.exists(key)
            
            if exists:
                logger.debug(f"✅ Mensaje YA procesado: {message_id}")
            else:
                logger.debug(f"🆕 Mensaje NUEVO: {message_id}")
            
            return bool(exists)
            
        except Exception as e:
            logger.error(f"❌ Error verificando mensaje: {e}")
            # En caso de error, asumir que NO fue procesado (seguro)
            return False
    
    async def mark_message_as_processed(
        self, 
        message_id: str, 
        ttl: int = 86400
    ) -> bool:
        """
        Marca un mensaje como procesado
        
        Key: chatwoot:msg:{message_id}
        Valor: "1"
        TTL: 24 horas (configurable)
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"chatwoot:msg:{message_id}"
            await self.redis_client.setex(key, ttl, "1")
            logger.debug(f"✅ Mensaje marcado: {message_id} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error marcando mensaje: {e}")
            return False