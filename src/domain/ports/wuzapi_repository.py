# src/domain/ports/wuzapi_repository.py
"""
Puerto: WuzAPIRepository
Define el contrato para enviar mensajes a través de WuzAPI
"""
from abc import ABC, abstractmethod
from typing import Optional


class WuzAPIRepository(ABC):
    """Puerto de salida para operaciones con WuzAPI"""
    
    # ==================== MÉTODO EXISTENTE ====================
    
    @abstractmethod
    async def send_text_message(self, phone: str, message: str) -> bool:
        """Envía un mensaje de texto"""
        pass
    
    # ==================== NUEVOS MÉTODOS (MULTIMEDIA) ====================
    
    @abstractmethod
    async def send_image_message(
        self,
        phone: str,
        image_url: str,
        caption: str = ""
    ) -> bool:
        """
        Envía una imagen por WhatsApp.
        
        Args:
            phone: Número de teléfono destino
            image_url: URL pública de la imagen
            caption: Texto opcional que acompaña la imagen
            
        Returns:
            True si fue exitoso
        """
        pass
    
    @abstractmethod
    async def send_video_message(
        self,
        phone: str,
        video_url: str,
        caption: str = ""
    ) -> bool:
        """
        Envía un video por WhatsApp.
        
        Args:
            phone: Número de teléfono destino
            video_url: URL pública del video
            caption: Texto opcional que acompaña el video
            
        Returns:
            True si fue exitoso
        """
        pass
    
    @abstractmethod
    async def send_audio_message(
        self,
        phone: str,
        audio_url: str
    ) -> bool:
        """
        Envía un audio por WhatsApp.
        
        Args:
            phone: Número de teléfono destino
            audio_url: URL pública del archivo de audio
            
        Returns:
            True si fue exitoso
        """
        pass
    
    @abstractmethod
    async def send_document_message(
        self,
        phone: str,
        document_url: str,
        filename: str
    ) -> bool:
        """
        Envía un documento por WhatsApp.
        
        Args:
            phone: Número de teléfono destino
            document_url: URL pública del documento
            filename: Nombre del archivo
            
        Returns:
            True si fue exitoso
        """
        pass