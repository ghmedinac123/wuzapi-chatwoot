"""
src/infrastructure/media/audio_converter.py
Implementación de conversión de audio usando FFmpeg/pydub
"""
import logging
import subprocess
import tempfile
import os
from typing import Optional, List

import struct
import math
from ...domain.ports.audio_converter import AudioConverterPort

logger = logging.getLogger(__name__)


class FFmpegAudioConverter(AudioConverterPort):
    """
    Conversor de audio usando FFmpeg.
    
    Convierte cualquier formato a OGG Opus para WhatsApp PTT.
    """
    
    # Formatos que NO necesitan conversión (ya son compatibles con PTT)
    PTT_COMPATIBLE_FORMATS = ['audio/ogg', 'audio/opus', 'audio/ogg; codecs=opus']
    
    def __init__(self):
        self._ffmpeg_available: Optional[bool] = None
    
    def is_conversion_available(self) -> bool:
        """Verifica si ffmpeg está instalado"""
        if self._ffmpeg_available is not None:
            return self._ffmpeg_available
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            self._ffmpeg_available = result.returncode == 0
            if self._ffmpeg_available:
                logger.info("✅ FFmpeg disponible para conversión de audio")
            else:
                logger.warning("⚠️  FFmpeg no disponible")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._ffmpeg_available = False
            logger.warning("⚠️  FFmpeg no instalado")
        
        return self._ffmpeg_available
    
    def needs_conversion(self, content_type: str) -> bool:
        """Determina si el formato necesita conversión"""
        content_type_lower = content_type.lower()
        
        for compatible in self.PTT_COMPATIBLE_FORMATS:
            if compatible in content_type_lower:
                return False
        
        return True
    
    async def convert_to_ogg_opus(
        self, 
        audio_bytes: bytes, 
        source_format: str
    ) -> Optional[bytes]:
        """
        Convierte audio a OGG Opus usando FFmpeg.
        
        Proceso:
        1. Guardar bytes en archivo temporal
        2. Ejecutar ffmpeg para convertir
        3. Leer resultado
        4. Limpiar archivos temporales
        """
        if not self.is_conversion_available():
            logger.error("❌ FFmpeg no disponible para conversión")
            return None
        
        input_file = None
        output_file = None
        
        try:
            # Determinar extensión del archivo origen
            ext = self._get_extension(source_format)
            
            # Crear archivos temporales
            input_file = tempfile.NamedTemporaryFile(
                suffix=f'.{ext}', 
                delete=False
            )
            output_file = tempfile.NamedTemporaryFile(
                suffix='.ogg', 
                delete=False
            )
            
            # Escribir audio origen
            input_file.write(audio_bytes)
            input_file.close()
            
            output_path = output_file.name
            output_file.close()
            
            logger.info(f"🔄 Convirtiendo {ext.upper()} → OGG Opus...")
            logger.info(f"   📥 Input: {len(audio_bytes)} bytes")
            
            # Ejecutar FFmpeg
            # -y: sobrescribir sin preguntar
            # -i: archivo de entrada
            # -c:a libopus: codec de audio Opus
            # -b:a 64k: bitrate de audio
            # -vn: sin video
            # -ar 48000: sample rate 48kHz (requerido por Opus)
            cmd = [
                'ffmpeg', '-y',
                '-i', input_file.name,
                '-c:a', 'libopus',
                '-b:a', '64k',
                '-vn',
                '-ar', '48000',
                '-ac', '1',  # Mono (mejor para voz)
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"❌ FFmpeg error: {result.stderr.decode()[:200]}")
                return None
            
            # Leer resultado
            with open(output_path, 'rb') as f:
                ogg_bytes = f.read()
            
            logger.info(f"   📤 Output: {len(ogg_bytes)} bytes")
            logger.info(f"   📉 Compresión: {len(audio_bytes)/len(ogg_bytes):.1f}x")
            logger.info(f"✅ Conversión exitosa")
            
            return ogg_bytes
            
        except subprocess.TimeoutExpired:
            logger.error("❌ FFmpeg timeout")
            return None
        except Exception as e:
            logger.error(f"❌ Error en conversión: {e}", exc_info=True)
            return None
        finally:
            # Limpiar archivos temporales
            if input_file and os.path.exists(input_file.name):
                os.unlink(input_file.name)
            if output_file and os.path.exists(output_file.name):
                os.unlink(output_file.name)
    
    def _get_extension(self, content_type: str) -> str:
        """Obtiene extensión según content-type"""
        mapping = {
            'audio/wav': 'wav',
            'audio/x-wav': 'wav',
            'audio/mpeg': 'mp3',
            'audio/mp3': 'mp3',
            'audio/ogg': 'ogg',
            'audio/webm': 'webm',
            'audio/aac': 'aac',
        }
        
        for key, ext in mapping.items():
            if key in content_type.lower():
                return ext
        
        return 'wav'  # Default
    

    def get_duration_seconds(self, audio_bytes: bytes) -> int:
        """Obtiene duración usando ffprobe"""
        if not self.is_conversion_available():
            return 0
        
        input_file = None
        try:
            import tempfile
            input_file = tempfile.NamedTemporaryFile(suffix='.ogg', delete=False)
            input_file.write(audio_bytes)
            input_file.close()
            
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                input_file.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                duration_str = result.stdout.decode().strip()
                return int(float(duration_str))
            return 0
            
        except Exception as e:
            logger.warning(f"⚠️  Error obteniendo duración: {e}")
            return 0
        finally:
            if input_file and os.path.exists(input_file.name):
                os.unlink(input_file.name)



    def get_waveform(self, audio_bytes: bytes, num_points: int = 64) -> List[int]:
        """Genera waveform extrayendo PCM raw con ffmpeg"""
        if not self.is_conversion_available():
            return [0] * num_points
        
        input_file = None
        try:
            input_file = tempfile.NamedTemporaryFile(suffix='.ogg', delete=False)
            input_file.write(audio_bytes)
            input_file.close()
            
            # Extraer audio como PCM raw 16-bit mono 8kHz
            cmd = [
                'ffmpeg', '-y', '-i', input_file.name,
                '-f', 's16le',
                '-acodec', 'pcm_s16le',
                '-ar', '8000',
                '-ac', '1',
                'pipe:1'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode != 0:
                logger.warning(f"⚠️  Error extrayendo PCM: {result.stderr.decode()[:100]}")
                return [0] * num_points
            
            pcm_data = result.stdout
            
            # Convertir bytes a samples (16-bit signed)
            num_samples = len(pcm_data) // 2
            if num_samples == 0:
                return [0] * num_points
            
            samples = struct.unpack(f'<{num_samples}h', pcm_data)
            
            # Dividir en chunks
            chunk_size = max(1, num_samples // num_points)
            waveform = []
            
            for i in range(num_points):
                start = i * chunk_size
                end = min(start + chunk_size, num_samples)
                chunk = samples[start:end]
                
                if chunk:
                    # Calcular RMS (Root Mean Square)
                    rms = math.sqrt(sum(s * s for s in chunk) / len(chunk))
                    # Normalizar a 0-100 (max 16-bit = 32767)
                    normalized = min(100, int((rms / 32767) * 200))
                    waveform.append(normalized)
                else:
                    waveform.append(0)
            
            logger.info(f"📊 Waveform generado: {len(waveform)} puntos")
            return waveform
            
        except Exception as e:
            logger.warning(f"⚠️  Error generando waveform: {e}")
            return [0] * num_points
        finally:
            if input_file and os.path.exists(input_file.name):
                os.unlink(input_file.name)            