"""
Adaptador: InMemoryCache
Implementación simple del CacheRepository en memoria (sin Redis)
"""
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from ...domain.ports.cache_repository import CacheRepository


logger = logging.getLogger(__name__)


class InMemoryCache(CacheRepository):
    """
    Caché simple en memoria
    Útil para desarrollo o cuando Redis no está disponible
    """
    
    def __init__(self):
        # ✅ TU CÓDIGO ORIGINAL - NO TOCAR
        self._cache: Dict[str, tuple[int, datetime]] = {}
        
        # 🆕 NUEVO: Diccionario adicional para mensajes procesados
        self._processed_messages: Dict[str, datetime] = {}
        
        logger.info("✅ Usando caché en memoria")
    
    # ========================================================================
    # 🆕 NUEVO: Método de ciclo de vida requerido por la interfaz
    # ========================================================================
    
    async def connect(self) -> bool:
        """
        Método requerido por CacheRepository
        En memoria no hay conexión, siempre retorna True
        """
        return True
    
    # ========================================================================
    # ✅ TU CÓDIGO ORIGINAL - CONVERSACIONES (NO MODIFICADO)
    # ========================================================================
    
    async def get_conversation_id(self, phone: str) -> Optional[int]:
        """Obtiene ID desde memoria"""
        key = f"chatwoot:conv:{phone}"
        if key in self._cache:
            conv_id, expires_at = self._cache[key]
            if datetime.now() < expires_at:
                return conv_id
            else:
                del self._cache[key]
        return None
    
    async def set_conversation_id(self, phone: str, conversation_id: int, ttl: int = 3600) -> bool:
        """Guarda ID en memoria"""
        key = f"chatwoot:conv:{phone}"
        expires_at = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (conversation_id, expires_at)
        return True
    
    async def delete_conversation_id(self, phone: str) -> bool:
        """Elimina ID de memoria"""
        key = f"chatwoot:conv:{phone}"
        if key in self._cache:
            del self._cache[key]
        return True
    
    async def close(self):
        """No hay nada que cerrar"""
        pass
    
    # ========================================================================
    # 🆕 NUEVO: Métodos de idempotencia (evitar mensajes duplicados)
    # ========================================================================
    
    async def has_processed_message(self, message_id: str) -> bool:
        """
        Verifica si un mensaje ya fue procesado
        
        Funciona igual que las conversaciones: guarda el message_id
        con un timestamp de expiración.
        """
        if message_id in self._processed_messages:
            expires_at = self._processed_messages[message_id]
            
            # Verificar si NO ha expirado
            if datetime.now() < expires_at:
                logger.debug(f"✅ Mensaje YA procesado: {message_id}")
                return True
            else:
                # Ya expiró, eliminar y considerar como NO procesado
                del self._processed_messages[message_id]
                logger.debug(f"⏰ Marca expirada para: {message_id}")
                return False
        else:
            logger.debug(f"🆕 Mensaje NUEVO: {message_id}")
            return False
    
    async def mark_message_as_processed(
        self, 
        message_id: str, 
        ttl: int = 86400
    ) -> bool:
        """
        Marca un mensaje como procesado
        
        Similar a guardar una conversación, pero para mensajes.
        TTL default: 24 horas (86400 segundos)
        """
        expires_at = datetime.now() + timedelta(seconds=ttl)
        self._processed_messages[message_id] = expires_at
        logger.debug(f"✅ Mensaje marcado como procesado: {message_id} (TTL: {ttl}s)")
        return True