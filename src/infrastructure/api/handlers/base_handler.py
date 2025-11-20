"""
src/infrastructure/api/handlers/base_handler.py

Clase base abstracta para handlers de webhooks.
Implementa Template Method Pattern y define el contrato
que todos los handlers concretos deben seguir.

Principios aplicados:
- SRP: Solo define comportamiento común de handlers
- OCP: Extensible mediante herencia
- LSP: Todos los handlers son intercambiables
- DIP: Depende de abstracciones (ABC)
"""
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class BaseWebhookHandler(ABC):
    """
    Handler base para procesamiento de webhooks.
    
    Template Method Pattern: Define el esqueleto del algoritmo
    en process_event(), delegando pasos específicos a subclases.
    """
    
    def __init__(self, handler_name: str):
        """
        Args:
            handler_name: Nombre identificador del handler (ej: "WuzAPI", "Chatwoot")
        """
        self.handler_name = handler_name
        self.logger = logging.getLogger(f"{__name__}.{handler_name}")
    
    async def process_event(self, event_data: Dict[str, Any]) -> JSONResponse:
        """
        Template Method: Define el flujo completo de procesamiento.
        
        Pasos:
        1. Log del evento recibido
        2. Validación del payload
        3. Procesamiento específico (delegado a subclase)
        4. Respuesta HTTP
        
        Args:
            event_data: Datos del webhook recibido
            
        Returns:
            JSONResponse con resultado del procesamiento
        """
        try:
            # 1. Log estructurado del evento
            self._log_event_received(event_data)
            
            # 2. Validación genérica
            if not self._validate_payload(event_data):
                return self._error_response(
                    "invalid_payload",
                    "Payload no válido o incompleto"
                )
            
            # 3. Procesamiento específico (ABSTRACTO - implementado por subclase)
            result = await self.handle_event(event_data)
            
            # 4. Respuesta según resultado
            if result.get("success"):
                return self._success_response(result)
            else:
                return self._ignored_response(result)
                
        except Exception as e:
            self.logger.error(f"❌ EXCEPCIÓN EN {self.handler_name}", exc_info=True)
            self._log_error_context(event_data)
            return self._exception_response(str(e))
    
    @abstractmethod
    async def handle_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        MÉTODO ABSTRACTO: Procesamiento específico del webhook.
        
        Cada handler concreto implementa su lógica aquí.
        
        Args:
            event_data: Datos del webhook
            
        Returns:
            Dict con:
                - success: bool
                - reason: str (si success=False)
                - data: Dict[str, Any] (información adicional)
        """
        pass
    
    def _validate_payload(self, event_data: Dict[str, Any]) -> bool:
        """
        Validación básica del payload.
        Subclases pueden sobrescribir para validaciones específicas.
        
        Args:
            event_data: Datos a validar
            
        Returns:
            True si válido, False si no
        """
        return event_data is not None and isinstance(event_data, dict)
    
    def _log_event_received(self, event_data: Dict[str, Any]) -> None:
        """Log estructurado del evento recibido."""
        self.logger.info("=" * 70)
        self.logger.info(f"📥 EVENTO {self.handler_name}")
        self.logger.info("=" * 70)
        
        # Log del payload completo (útil para debugging)
        try:
            payload_str = json.dumps(event_data, indent=2, ensure_ascii=False)
            self.logger.debug(f"📦 Payload completo:\n{payload_str}")
        except Exception:
            self.logger.warning("⚠️  No se pudo serializar payload a JSON")
    
    def _log_error_context(self, event_data: Dict[str, Any]) -> None:
        """Log del contexto en caso de error."""
        try:
            self.logger.error(f"❌ Event data que causó la excepción:")
            self.logger.error(json.dumps(event_data, indent=2, ensure_ascii=False))
        except Exception:
            self.logger.error(f"❌ No se pudo serializar event_data")
    
    def _success_response(self, result: Dict[str, Any]) -> JSONResponse:
        """Respuesta HTTP exitosa."""
        self.logger.info(f"✅ Procesamiento exitoso")
        self.logger.info("=" * 70)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "handler": self.handler_name,
                **result.get("data", {})
            }
        )
    
    def _ignored_response(self, result: Dict[str, Any]) -> JSONResponse:
        """Respuesta HTTP para eventos ignorados."""
        reason = result.get("reason", "unknown")
        self.logger.info(f"ℹ️  Evento ignorado: {reason}")
        self.logger.info("=" * 70)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "ignored",
                "reason": reason,
                "handler": self.handler_name
            }
        )
    
    def _error_response(self, reason: str, message: str) -> JSONResponse:
        """Respuesta HTTP para errores de validación."""
        self.logger.warning(f"⚠️  {message}")
        self.logger.info("=" * 70)
        
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "reason": reason,
                "message": message,
                "handler": self.handler_name
            }
        )
    
    def _exception_response(self, error: str) -> JSONResponse:
        """Respuesta HTTP para excepciones."""
        return JSONResponse(
            status_code=500,
            content={
                "status": "exception",
                "error": error,
                "handler": self.handler_name
            }
        )   