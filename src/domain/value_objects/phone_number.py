"""
src/domain/value_objects/phone_number.py
Value Object: PhoneNumber con soporte para Estados de WhatsApp
"""
from dataclasses import dataclass
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhoneNumber:
    """Número de teléfono normalizado para WhatsApp"""
    
    raw: str
    
    def __post_init__(self):
        if not self.raw:
            raise ValueError("El número de teléfono no puede estar vacío")
    
    @property
    def clean(self) -> str:
        """Retorna el número limpio sin sufijos de WhatsApp"""
        # 🔥 Estados de WhatsApp
        if self.raw == 'status@broadcast':
            return "status_broadcast"
        
        clean = self.raw
        clean = clean.replace('@s.whatsapp.net', '')
        clean = clean.replace('@g.us', '')
        clean = clean.replace('+', '')
        
        if ':' in clean:
            clean = clean.split(':')[0]
        
        return clean
    
    @property
    def formatted(self) -> str:
        """Retorna el número con formato internacional"""
        # 🔥 Estados de WhatsApp
        if self.is_status:
            return "+status_broadcast"
        
        if self.is_group:
            group_id = self.raw.replace('@g.us', '')
            return f"+group_{group_id}"
        
        clean = self.clean
        return f"+{clean}" if not clean.startswith('+') else clean
    
    @property
    def is_group(self) -> bool:
        """Verifica si es un chat grupal"""
        return '@g.us' in self.raw
    
    @property
    def is_status(self) -> bool:
        """Verifica si es un estado/status de WhatsApp"""
        return self.raw == 'status@broadcast'
    
    def __str__(self) -> str:
        return self.formatted
    
    @classmethod
    def from_whatsapp_jid(cls, jid: str) -> Optional['PhoneNumber']:
        """
        Factory method para crear desde JID de WhatsApp.
        
        Soporta:
        - Usuarios: 573001234567@s.whatsapp.net ✅
        - Grupos: 573187267705-1551282257@g.us ✅
        - Estados: status@broadcast ✅
        
        Filtra:
        - Newsletters (@newsletter) ❌
        - LIDs (@lid) ❌
        """
        try:
            if not jid:
                logger.warning("⏭️  JID vacío")
                return None
            
            # FILTRO 1: Rechazar newsletters
            if '@newsletter' in jid:
                logger.warning(f"⏭️  Ignorando NEWSLETTER: {jid}")
                return None
            
            # FILTRO 2: Rechazar LIDs
            if '@lid' in jid:
                logger.warning(f"⏭️  Ignorando LID: {jid}")
                return None
            
            # 🔥 NUEVO: Aceptar status@broadcast (Estados de WhatsApp)
            if jid == 'status@broadcast':
                logger.debug(f"✅ Estado de WhatsApp detectado")
                return cls(raw=jid)
            
            # Crear objeto
            phone = cls(raw=jid)
            clean = phone.clean
            
            # Validar número (solo para usuarios, no grupos)
            if not phone.is_group:
                if not re.match(r'^\d+$', clean):
                    logger.warning(f"⏭️  No es número válido: {jid}")
                    return None
                
                if len(clean) < 10 or len(clean) > 15:
                    logger.warning(f"⏭️  Longitud inválida ({len(clean)}): {jid}")
                    return None
            
            logger.debug(f"✅ PhoneNumber válido: {phone.formatted}")
            return phone
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return None