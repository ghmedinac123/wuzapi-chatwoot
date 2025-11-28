"""
src/infrastructure/api/routers/wuzapi_router.py

Router de FastAPI para endpoints de WuzAPI.

Responsabilidad única:
- Definir rutas HTTP relacionadas con WuzAPI
- Recibir Request y devolver Response
- Delegar procesamiento al WuzAPIWebhookHandler

Separación de responsabilidades:
- Router: Solo HTTP (recibir/enviar)
- Handler: Lógica de procesamiento
"""
import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
import json
from ..handlers.wuzapi_handler import WuzAPIWebhookHandler
from ..dependencies import get_wuzapi_handler

logger = logging.getLogger(__name__)

# Crear router con prefijo y tags para documentación
router = APIRouter(
    prefix="/webhook",
    tags=["WuzAPI Webhooks"]
)


@router.post(
    "/wuzapi",
    response_class=JSONResponse,
    summary="Webhook de WuzAPI",
    description="""
    Recibe eventos de WuzAPI (mensajes de WhatsApp).
    
    Flujo:
    1. Recibe evento HTTP
    2. Valida estructura y userID
    3. Parsea mensaje a entidad del dominio
    4. Sincroniza a Chatwoot
    
    Eventos soportados:
    - Message: Mensajes de texto, multimedia, etc.
    
    Validaciones:
    - userID debe coincidir con instancia configurada
    - Solo procesa eventos tipo "Message"
    - Ignora grupos
    """
)
async def receive_wuzapi_event(
    request: Request,
    handler: WuzAPIWebhookHandler = Depends(get_wuzapi_handler)
) -> JSONResponse:
    """
    Endpoint que recibe eventos de WuzAPI.
    
    Args:
        request: Request HTTP de FastAPI
        handler: Handler inyectado automáticamente (Dependency Injection)
        
    Returns:
        JSONResponse con resultado del procesamiento
    """
    # Extraer payload JSON
    event_data = await request.json()
    
    # Log del evento recibido
    logger.info(f"📋 Evento recibido Wuzapi: {json.dumps(event_data, indent=2)}")
    # Delegar todo el procesamiento al handler
    # Handler se encarga de:
    # - Validación
    # - Parsing
    # - Ejecución de caso de uso
    # - Logging
    # - Respuesta HTTP
    return await handler.process_event(event_data)