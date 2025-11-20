# Arquitectura del Sistema

## Principios

- **Hexagonal Architecture**: Separa lógica de negocio de detalles técnicos
- **SOLID**: Código mantenible y escalable
- **DDD**: Domain-Driven Design para modelar el negocio

## Flujos

### WhatsApp → Chatwoot

1. Mensaje llega a WuzAPI
2. WuzAPI envía webhook a `/webhook/wuzapi`
3. `webhook.py` parsea y crea `WhatsAppMessage`
4. Llama a `SyncMessageToChatwootUseCase`
5. Caso de uso coordina con `ChatwootClient`
6. Mensaje aparece en Chatwoot

### Chatwoot → WhatsApp

1. Agente responde en Chatwoot
2. Chatwoot envía webhook a `/webhook/chatwoot`
3. `webhook.py` parsea el evento
4. Llama a `SendMessageToWhatsAppUseCase`
5. Caso de uso coordina con `WuzAPIClient`
6. Mensaje enviado por WhatsApp

## Testing
```bash
# Tests unitarios
pytest tests/unit

# Tests de integración
pytest tests/integration
```
