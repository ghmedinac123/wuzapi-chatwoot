"""
src/infrastructure/chatwoot/client.py
Cliente Chatwoot con soporte REAL de multimedia (multipart/form-data)
"""
import logging,json
from typing import Optional, List, Dict, Any
import httpx
from io import BytesIO

from ...domain.ports.chatwoot_repository import ChatwootRepository


logger = logging.getLogger(__name__)


class ChatwootClient(ChatwootRepository):
    """Cliente HTTP para Chatwoot con soporte multimedia REAL"""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        account_id: str,
        inbox_id: str,
        timeout: int = 60
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.account_id = account_id
        self.inbox_id = inbox_id
        self.timeout = timeout
        
        self.headers = {
            'api_access_token': api_key
        }
        
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=self.headers,
            timeout=timeout
        )
        
      
    
    # ==================== MÉTODOS ORIGINALES ====================
    
    async def create_or_get_contact(
        self, 
        phone: str, 
        name: Optional[str] = None,
        avatar_url: Optional[str] = None  # 🔥 NUEVO PARÁMETRO
    ) -> Optional[int]:
        """
        Crea o busca contacto.
        
        🔥 NUEVO: Soporta avatar_url para foto de perfil
        """
        try:
            phone_clean = phone.replace('+', '').replace('group_', '')
            
            # ==================== BUSCAR CONTACTO EXISTENTE ====================
            
            search_url = f"/api/v1/accounts/{self.account_id}/contacts/search"
            response = await self.client.get(search_url, params={'q': phone_clean})
            
            if response.status_code == 200:
                contacts = response.json().get('payload', [])
                if contacts:
                    contact_id = contacts[0]['id']
                   
                    
                    # 🔥 NUEVO: Si hay avatar_url, actualizar contacto existente
                    if avatar_url:
                     
                        await self._update_contact_avatar(contact_id, avatar_url)
                    
                    return contact_id
            
            # ==================== CREAR CONTACTO NUEVO ====================
            
            create_url = f"/api/v1/accounts/{self.account_id}/contacts"
            data = {
                'name': name or phone_clean,
                'phone_number': f"+{phone_clean}",
                'identifier': phone_clean
            }
            
            # 🔥 NUEVO: Agregar avatar_url si existe
            if avatar_url:
                data['avatar_url'] = avatar_url
            
            response = await self.client.post(create_url, json=data)
            
            if response.status_code in [200, 201]:
                contact_id = response.json()['payload']['contact']['id']
              
                return contact_id
            
            logger.error(f"❌ Error creando contacto: {response.status_code}")
            logger.error(f"❌ Response: {response.text[:500]}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error en create_or_get_contact: {e}", exc_info=True)
            return None
    
    async def _update_contact_avatar(
        self,
        contact_id: int,
        avatar_url: str
    ) -> bool:
        """
        Actualiza el avatar de un contacto existente.
        
        Args:
            contact_id: ID del contacto
            avatar_url: URL de la imagen
            
        Returns:
            True si fue exitoso
        """
        try:
            update_url = f"/api/v1/accounts/{self.account_id}/contacts/{contact_id}"
            data = {
                'avatar_url': avatar_url
            }
            
            response = await self.client.put(update_url, json=data)
            
            if response.status_code in [200, 204]:
                logger.info(f"✅ Avatar actualizado para contacto {contact_id}")
                return True
            else:
                logger.warning(f"⚠️  No se pudo actualizar avatar: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error actualizando avatar: {e}")
            return False
    
    async def create_or_get_conversation(
        self, 
        contact_id: int, 
        source_id: str
    ) -> Optional[int]:
        """
        Crea o busca conversación.
        
        🔥 MEJORA: Busca conversaciones directamente por contact_id
        para evitar duplicados.
        """
        try:
            logger.info("=" * 70)
            logger.info("🔍 BUSCANDO/CREANDO CONVERSACIÓN")
            logger.info("=" * 70)
            logger.info(f"👤 Contact ID: {contact_id}")
            logger.info(f"📬 Inbox ID: {self.inbox_id}")
            logger.info(f"🔑 Source ID: {source_id}")
            
            # ==================== BUSCAR CONVERSACIONES DEL CONTACTO ====================
            
            # Endpoint específico para conversaciones de un contacto
            list_url = f"/api/v1/accounts/{self.account_id}/contacts/{contact_id}/conversations"
            
            logger.info(f"🔍 Buscando conversaciones del contacto...")
            logger.info(f"📍 URL: {self.base_url}{list_url}")
            
            response = await self.client.get(list_url)
            
            logger.info(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                conversations = response.json().get('payload', [])
                
                logger.info(f"📊 Total conversaciones encontradas: {len(conversations)}")
                
                # Filtrar por inbox_id
                matching_conversations = []
                
                for conv in conversations:
                    conv_inbox_id = conv.get('inbox_id')
                    conv_id = conv.get('id')
                    conv_status = conv.get('status')
                    
                    logger.info(f"   • Conv ID: {conv_id}, Inbox: {conv_inbox_id}, Status: {conv_status}")
                    
                    # Verificar que sea del inbox correcto
                    if str(conv_inbox_id) == str(self.inbox_id):
                        matching_conversations.append(conv)
                        logger.info(f"     ✅ Match! Conv {conv_id} es del inbox {self.inbox_id}")
                
                if matching_conversations:
                    # Priorizar conversaciones abiertas (status: 'open')
                    open_conversations = [c for c in matching_conversations if c.get('status') == 'open']
                    
                    if open_conversations:
                        conv_id = open_conversations[0]['id']
                        logger.info(f"✅ Conversación ABIERTA encontrada: {conv_id}")
                        logger.info("=" * 70)
                        return conv_id
                    else:
                        # Si no hay abiertas, usar la más reciente (primera)
                        conv_id = matching_conversations[0]['id']
                        logger.info(f"✅ Conversación encontrada (cerrada): {conv_id}")
                        logger.info("=" * 70)
                        return conv_id
                else:
                    logger.info(f"ℹ️  No hay conversaciones en el inbox {self.inbox_id}")
            else:
                logger.warning(f"⚠️  Error al buscar conversaciones: HTTP {response.status_code}")
                logger.warning(f"⚠️  Response: {response.text[:500]}")
            
            # ==================== CREAR NUEVA CONVERSACIÓN ====================
            
            logger.info(f"📝 Creando conversación nueva...")
            
            create_url = f"/api/v1/accounts/{self.account_id}/conversations"
            data = {
                'source_id': source_id,
                'inbox_id': self.inbox_id,
                'contact_id': contact_id,
                'status': 'open'
            }
            
            logger.info(f"📍 URL: {self.base_url}{create_url}")
            logger.info(f"📦 Data: {data}")
            
            response = await self.client.post(create_url, json=data)
            
            logger.info(f"📡 Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                conv_id = response.json()['id']
                logger.info(f"✅ Conversación CREADA: {conv_id}")
                logger.info("=" * 70)
                return conv_id
            else:
                logger.error(f"❌ Error creando conversación: {response.status_code}")
                logger.error(f"❌ Response: {response.text[:500]}")
                logger.info("=" * 70)
                return None
            
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ EXCEPCIÓN EN create_or_get_conversation")
            logger.error(f"❌ Error: {e}", exc_info=True)
            logger.error("=" * 70)
            return None
    
    async def send_message(
        self, 
        conversation_id: int, 
        content: str,
        message_type: str = 'incoming'
    ) -> Optional[int]:
        """Envía mensaje de TEXTO con marca anti-loop"""
        try:
            url = f"/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
            
            headers = {
                'api_access_token': self.api_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'content': content,
                'message_type': message_type,
                'private': False,
                # 🔴 ELIMINAR json.dumps(). Pasar el dict directo.
                'external_source_ids': { 
                    'whatsapp_sync': 'true'
                }
            }
            
            response = await self.client.post(url, json=data, headers=headers)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Mensaje enviado a conversación {conversation_id}")
                result = response.json()
                message_id = result.get('id')
                return message_id
            
            if response.status_code == 404:
                logger.error(f"❌ Conversación {conversation_id} NO EXISTE (404)")
                return None
            
            logger.error(f"❌ Error enviando mensaje: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error en send_message: {e}", exc_info=True)
            return None
                

    
    # ==================== MULTIMEDIA CON MULTIPART/FORM-DATA ====================
    
    async def send_message_with_attachments(
        self,
        conversation_id: int,
        content: str,
        message_type: str = 'incoming',
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None,
        mimetype: Optional[str] = None
    ) -> Optional[int]:  # 🔥 CAMBIO: Ahora devuelve int (ID) o None
        """
        Envía mensaje con archivo multimedia y retorna el ID para cachear (Anti-Loop).
        """
        try:
            logger.info("=" * 70)
            logger.info("📤 SUBIENDO MULTIMEDIA A CHATWOOT")
            logger.info("=" * 70)
            
            if not file_data or not filename:
                logger.warning("⚠️  No hay archivo, enviando solo texto")
                return await self.send_message(conversation_id, content, message_type)
            
            url = f"/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
            
            logger.info(f"📍 URL: {self.base_url}{url}")
            logger.info(f"📦 Filename: {filename}")
            logger.info(f"📦 Mimetype: {mimetype}")
            logger.info(f"📦 File size: {len(file_data)} bytes")
            
            files = {
                'attachments[]': (filename, BytesIO(file_data), mimetype or 'application/octet-stream')
            }
            
            # Intentamos enviar la bandera en content_attributes, aunque Chatwoot a veces la limpie en multipart
            data = {
                'content': content or '',
                'message_type': message_type,
                'private': 'false',
                'content_attributes': json.dumps({'whatsapp_sync': True})
            }
            
            headers = {
                'api_access_token': self.api_key
            }
            
            logger.info("🚀 Enviando POST multipart/form-data...")
            
            response = await self.client.post(
                url,
                data=data,
                files=files,
                headers=headers
            )
            
            logger.info(f"📡 Response Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                message_id = response_data.get('id')
                logger.info(f"✅ Multimedia subido. Chatwoot ID: {message_id}")
                return message_id # 🔥 RETORNAMOS EL ID PARA EL CACHÉ
            else:
                logger.error(f"❌ Error {response.status_code}")
                logger.error(f"❌ Response: {response.text[:500]}")
                return None
            
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ EXCEPCIÓN EN UPLOAD A CHATWOOT")
            logger.error(f"❌ Error: {e}", exc_info=True)
            logger.error("=" * 70)
            return None
    
    async def close(self) -> None:
        """Cierra el cliente HTTP"""
        await self.client.aclose()
        logger.info("👋 Cliente Chatwoot cerrado")