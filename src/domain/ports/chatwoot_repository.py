"""
Puerto: ChatwootRepository
Define el contrato para interactuar con Chatwoot
"""
from abc import ABC, abstractmethod
from typing import Optional


class ChatwootRepository(ABC):
    """
    Puerto de salida para operaciones con Chatwoot.
    
    Esta interfaz define las operaciones necesarias sin saber
    cómo se implementan (desacoplamiento).
    """
    
    @abstractmethod
    async def create_or_get_contact(
        self, 
        phone: str, 
        name: Optional[str] = None,
        avatar_url: Optional[str] = None  # 🔥 NUEVO PARÁMETRO
    ) -> Optional[int]:
        """
        Crea o recupera un contacto en Chatwoot.
        
        Args:
            phone: Número de teléfono
            name: Nombre del contacto (opcional)
            avatar_url: URL de la foto de perfil (opcional)
            
        Returns:
            ID del contacto o None si falla
        """
        pass
    
    @abstractmethod
    async def create_or_get_conversation(
        self, 
        contact_id: int, 
        source_id: str
    ) -> Optional[int]:
        """
        Crea o recupera una conversación.
        
        Args:
            contact_id: ID del contacto
            source_id: Identificador único de la conversación
            
        Returns:
            ID de la conversación o None si falla
        """
        pass
    
    @abstractmethod
    async def send_message(
        self, 
        conversation_id: int, 
        content: str,
        message_type: str = 'incoming'
    ) -> bool:
        """
        Envía un mensaje de TEXTO simple a una conversación.
        
        Args:
            conversation_id: ID de la conversación
            content: Contenido del mensaje
            message_type: 'incoming' o 'outgoing'
            
        Returns:
            True si fue exitoso, False si falló
        """
        pass
    
    @abstractmethod
    async def send_message_with_attachments(
        self,
        conversation_id: int,
        content: str,
        message_type: str = 'incoming',
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None,
        mimetype: Optional[str] = None
    ) -> bool:
        """
        Envía un mensaje con archivo multimedia adjunto.
        
        Args:
            conversation_id: ID de la conversación en Chatwoot
            content: Contenido del mensaje (puede ser caption)
            message_type: 'incoming' o 'outgoing'
            file_data: Bytes del archivo multimedia
            filename: Nombre del archivo
            mimetype: MIME type del archivo
            
        Returns:
            True si fue exitoso, False si falló
        """
        pass