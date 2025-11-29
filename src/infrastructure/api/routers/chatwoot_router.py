"""
src/infrastructure/api/routers/chatwoot_router.py

Router de FastAPI para endpoints de Chatwoot.

Responsabilidad única:
- Definir rutas HTTP relacionadas con Chatwoot
- Recibir Request y devolver Response
- Delegar procesamiento al ChatwootWebhookHandler

Separación de responsabilidades:
- Router: Solo HTTP (recibir/enviar)
- Handler: Lógica de procesamiento
"""
import logging,json
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from ..handlers.chatwoot_handler import ChatwootWebhookHandler
from ..dependencies import get_chatwoot_handler

logger = logging.getLogger(__name__)

# Crear router con prefijo y tags para documentación
router = APIRouter(
    prefix="/webhook",
    tags=["Chatwoot Webhooks"]
)


@router.post(
    "/chatwoot",
    response_class=JSONResponse,
    summary="Webhook de Chatwoot",
    description="""
    Recibe eventos de Chatwoot (mensajes salientes de agentes).
    
    Flujo:
    1. Recibe evento HTTP
    2. Valida tipo de evento (message_created)
    3. Valida mensaje outgoing
    4. Envía a WhatsApp vía WuzAPI
    
    Eventos soportados:
    - message_created: Nuevo mensaje en conversación
    
    Validaciones:
    - Solo procesa message_type: "outgoing"
    - Extrae número de teléfono del source_id
    - Soporta attachments multimedia
    """
)
async def receive_chatwoot_event(
    request: Request,
    handler: ChatwootWebhookHandler = Depends(get_chatwoot_handler)
) -> JSONResponse:
    """
    Endpoint que recibe eventos de Chatwoot.
    
    Args:
        request: Request HTTP de FastAPI
        handler: Handler inyectado automáticamente (Dependency Injection)
        
    Returns:
        JSONResponse con resultado del procesamiento
    """
    # Extraer payload JSON
    event_data = await request.json()
    logger.info(f"📋 Evento recibido Chatwoot: {json.dumps(event_data, indent=2)}")
    
    # Delegar todo el procesamiento al handler
    # Handler se encarga de:
    # - Validación
    # - Extracción de datos
    # - Ejecución de caso de uso
    # - Logging
    # - Respuesta HTTP
    return await handler.process_event(event_data)