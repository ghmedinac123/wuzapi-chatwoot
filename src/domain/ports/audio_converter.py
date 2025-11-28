"""
src/domain/ports/audio_converter.py
Puerto para conversión de audio - Define QUÉ hacer, no CÓMO
"""
from abc import ABC, abstractmethod
from typing import Optional, List


class AudioConverterPort(ABC):
    """
    Interfaz para conversión de formatos de audio.
    
    WhatsApp PTT requiere OGG Opus.
    Este puerto permite diferentes implementaciones:
    - FFmpeg (producción)
    - Mock (testing)
    """
    
    @abstractmethod
    async def convert_to_ogg_opus(
        self, 
        audio_bytes: bytes, 
        source_format: str
    ) -> Optional[bytes]:
        """
        Convierte audio a formato OGG Opus (compatible con WhatsApp PTT).
        
        Args:
            audio_bytes: Bytes del audio original
            source_format: Formato origen (wav, mp3, etc.)
            
        Returns:
            Bytes del audio en OGG Opus, o None si falla
        """
        pass
    
    @abstractmethod
    def is_conversion_available(self) -> bool:
        """
        Verifica si el conversor está disponible.
        
        Returns:
            True si ffmpeg está instalado y funcional
        """
        pass
    
    @abstractmethod
    def needs_conversion(self, content_type: str) -> bool:
        """
        Determina si el formato necesita conversión para PTT.
        
        Args:
            content_type: MIME type del audio
            
        Returns:
            True si necesita conversión (ej: WAV), False si ya es compatible (ej: OGG)
        """
        pass

    @abstractmethod
    def get_duration_seconds(self, audio_bytes: bytes) -> int:
        """
        Obtiene la duración del audio en segundos.
        
        Args:
            audio_bytes: Bytes del audio (OGG Opus)
            
        Returns:
            Duración en segundos enteros
        """
        pass

    @abstractmethod
    def get_waveform(self, audio_bytes: bytes, num_points: int = 64) -> List[int]:
        """
        Genera waveform (forma de onda) para visualización.
        
        Args:
            audio_bytes: Bytes del audio OGG
            num_points: Cantidad de puntos (default 64)
            
        Returns:
            Lista de valores 0-100 representando amplitud
        """
        pass