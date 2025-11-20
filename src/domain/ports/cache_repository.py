"""
Puerto: CacheRepository
Define el contrato COMPLETO para caché de conversaciones y mensajes
"""
from abc import ABC, abstractmethod
from typing import Optional


class CacheRepository(ABC):
    """
    Puerto de salida para operaciones de caché
    
    Permite:
    1. Cachear IDs de conversaciones (evitar consultas repetitivas)
    2. Implementar idempotencia (evitar mensajes duplicados)
    """
    
    # ========================================================================
    # MÉTODOS PARA CONVERSACIONES
    # ========================================================================
    
    @abstractmethod
    async def get_conversation_id(self, phone: str) -> Optional[int]:
        """
        Obtiene el ID de conversación desde caché
        
        Args:
            phone: Número de teléfono del contacto
            
        Returns:
            ID de la conversación o None si no existe en caché
        """
        pass
    
    @abstractmethod
    async def set_conversation_id(
        self, 
        phone: str, 
        conversation_id: int, 
        ttl: int = 3600
    ) -> bool:
        """
        Guarda el ID de conversación en caché
        
        Args:
            phone: Número de teléfono del contacto
            conversation_id: ID de la conversación en Chatwoot
            ttl: Tiempo de vida en segundos (default: 1 hora)
            
        Returns:
            True si se guardó exitosamente
        """
        pass
    
    @abstractmethod
    async def delete_conversation_id(self, phone: str) -> bool:
        """
        Elimina una conversación del caché
        
        Args:
            phone: Número de teléfono del contacto
            
        Returns:
            True si se eliminó exitosamente
        """
        pass
    
    # ========================================================================
    # MÉTODOS PARA IDEMPOTENCIA (Evitar Mensajes Duplicados)
    # ========================================================================
    
    @abstractmethod
    async def has_processed_message(self, message_id: str) -> bool:
        """
        Verifica si un mensaje ya fue procesado
        
        Args:
            message_id: ID único del mensaje de WhatsApp
            
        Returns:
            True si el mensaje ya fue procesado, False si es nuevo
        """
        pass
    
    @abstractmethod
    async def mark_message_as_processed(
        self, 
        message_id: str, 
        ttl: int = 86400
    ) -> bool:
        """
        Marca un mensaje como procesado
        
        Args:
            message_id: ID único del mensaje de WhatsApp
            ttl: Tiempo de vida en segundos (default: 24 horas)
            
        Returns:
            True si se marcó exitosamente
        """
        pass
    
    # ========================================================================
    # MÉTODOS DE CICLO DE VIDA
    # ========================================================================
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establece conexión con el backend de caché
        
        Returns:
            True si la conexión fue exitosa
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Cierra la conexión con el backend de caché"""
        pass