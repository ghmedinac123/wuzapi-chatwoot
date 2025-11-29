"""
Adapter: Cliente de sesiones WuzAPI
Arquitectura Hexagonal - Capa de Infraestructura
"""
import logging
from typing import Optional
import httpx

from ...domain.entities.wuzapi_session import WuzAPISession
from ...domain.ports.session_repository import SessionRepository

logger = logging.getLogger(__name__)


class WuzAPISessionClient(SessionRepository):
    """Implementación del repositorio de sesiones para WuzAPI"""
    
    def __init__(self, base_url: str, user_token: str, instance_token: str = "", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.user_token = user_token
        self.instance_token = instance_token
        self.timeout = timeout
        
        # 🔥 FIX: WuzAPI usa INSTANCE_TOKEN en header 'token'
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={'token': instance_token},  # 🔥 CAMBIO AQUÍ
            timeout=timeout
        )
        
        logger.info(f"🔧 WuzAPISessionClient configurado")
        logger.info(f"   Base URL: {self.base_url}")
    
    async def get_status(self) -> Optional[WuzAPISession]:
        """GET /session/status"""
        try:
            logger.info("📡 Consultando /session/status...")
            response = await self.client.get('/session/status')
            
            logger.info(f"📡 Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"📦 Data: {data}")
                session = WuzAPISession.from_status_response(data)
                logger.info(f"📊 Estado sesión: {session.status.value}")
                return session
            
            # 🔥 Log del error completo
            logger.error(f"❌ Error obteniendo status: {response.status_code}")
            logger.error(f"❌ Response body: {response.text[:500]}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Excepción en get_status: {e}", exc_info=True)
            return None
    
    async def connect(self) -> bool:
        """POST /session/connect"""
        try:
            logger.info("🔌 Conectando sesión...")
            
            payload = {
                'Subscribe': ['All'],
                'Immediate': True
            }
            
            response = await self.client.post('/session/connect', json=payload)
            
            logger.info(f"📡 Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"📦 Data: {data}")
                if data.get('success'):
                    logger.info("✅ Sesión conectada")
                    return True
            
            logger.error(f"❌ Error conectando: {response.status_code}")
            logger.error(f"❌ Response body: {response.text[:500]}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Excepción en connect: {e}", exc_info=True)
            return False
    
    async def disconnect(self) -> bool:
        """POST /session/disconnect"""
        try:
            logger.info("🔌 Desconectando sesión...")
            
            response = await self.client.post('/session/disconnect')
            
            logger.info(f"📡 Response: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Sesión desconectada")
                return True
            
            logger.error(f"❌ Error desconectando: {response.status_code}")
            logger.error(f"❌ Response body: {response.text[:500]}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Excepción en disconnect: {e}", exc_info=True)
            return False
    
    async def close(self) -> None:
        await self.client.aclose()


    async def logout(self) -> bool:
        """POST /session/logout - Cierra sesión completamente"""
        try:
            logger.info("🚪 Cerrando sesión (logout)...")
            
            response = await self.client.post('/session/logout')
            
            logger.info(f"📡 Response: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Sesión cerrada (logout)")
                return True
            
            logger.error(f"❌ Error en logout: {response.status_code}")
            logger.error(f"❌ Response body: {response.text[:500]}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Excepción en logout: {e}", exc_info=True)
            return False
    
    async def get_qr(self) -> Optional[str]:
        """GET /session/qr - Obtiene QR en base64"""
        try:
            logger.info("📱 Obteniendo QR...")
            
            response = await self.client.get('/session/qr')
            
            logger.info(f"📡 Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                qr_code = data.get('data', {}).get('qrcode') or data.get('qrcode')
                
                if qr_code:
                    logger.info("✅ QR obtenido")
                    return qr_code
                else:
                    logger.warning("⚠️ Respuesta sin QR (¿ya conectado?)")
                    return None
            
            logger.error(f"❌ Error obteniendo QR: {response.status_code}")
            logger.error(f"❌ Response body: {response.text[:500]}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Excepción en get_qr: {e}", exc_info=True)
            return None    