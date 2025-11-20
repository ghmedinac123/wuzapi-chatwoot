# 🤖 CLAUDE.md - Contexto para Claude AI

Este archivo contiene el contexto completo del proyecto para que Claude AI pueda asistir efectivamente en el desarrollo y mantenimiento.

---

## 🎯 Propósito del Proyecto

Integración bidireccional profesional entre **WuzAPI (WhatsApp Business API)** y **Chatwoot (Customer Service Platform)** para Fututel, empresa de telecomunicaciones en Colombia con 5,000 clientes de internet.

### Objetivo de Negocio

Centralizar todas las conversaciones de WhatsApp de clientes en Chatwoot para:
- ✅ Gestión eficiente por equipo de soporte
- ✅ Métricas y reportes de atención
- ✅ Asignación de conversaciones a agentes
- ✅ Historial centralizado de interacciones

---

## 🏗️ Arquitectura

### Estilo Arquitectónico: Hexagonal (Ports & Adapters)

**¿Por qué Hexagonal?**
- Separación clara entre lógica de negocio y detalles técnicos
- Facilita testing (puedes mockear adaptadores)
- Permite cambiar implementaciones sin afectar el core
- Escalable y mantenible a largo plazo

### Capas y Responsabilidades

```
domain/ (CORE)
├─ entities/         → Objetos con identidad (WhatsAppMessage)
├─ value_objects/    → Objetos inmutables (PhoneNumber)
└─ ports/            → Interfaces que define el dominio

application/
└─ use_cases/        → Orquestación de lógica de negocio

infrastructure/
├─ api/              → Entrada HTTP (FastAPI) - Arquitectura Router-Handler
│  ├─ app.py         → Application Factory (crea FastAPI app)
│  ├─ dependencies.py → DI Container (singletons, inyección)
│  ├─ routers/       → Definición de rutas HTTP
│  │  ├─ wuzapi_router.py
│  │  └─ chatwoot_router.py
│  └─ handlers/      → Lógica de procesamiento de webhooks
│     ├─ base_handler.py    → Template Method Pattern
│     ├─ wuzapi_handler.py
│     └─ chatwoot_handler.py
├─ chatwoot/         → Salida a Chatwoot (HTTP client)
├─ wuzapi/           → Salida a WuzAPI (HTTP client)
├─ media/            → Descarga multimedia (MediaDownloader)
└─ persistence/      → Salida a caché (Redis/Memory)

shared/
└─ config.py         → Configuración centralizada
```

### Flujo de Dependencias

```
infrastructure/api/routers/wuzapi_router.py
    ↓ usa
infrastructure/api/handlers/wuzapi_handler.py
    ↓ usa
application/use_cases/sync_message_to_chatwoot.py
    ↓ usa (via interfaces)
domain/ports/chatwoot_repository.py
    ↑ implementa
infrastructure/chatwoot/client.py
```

**REGLA CRÍTICA**: `domain/` NUNCA importa de `infrastructure/` o `application/`

---

## 📋 Reglas de Desarrollo (CRÍTICO)

### 1. **NUNCA Modificar Código Que Funciona**

```python
# ❌ MAL
def existing_function():
    # Cambiar implementación existente
    pass

# ✅ BIEN
def existing_function():
    # Código original intacto
    pass

def new_improved_function():
    # Nueva funcionalidad sin tocar la antigua
    pass
```

### 2. **Siempre Extender, Nunca Reemplazar**

```python
# ❌ MAL - Reemplazar clase existente
class WuzAPIClient:
    def send_message(self):
        # Nueva implementación que rompe lo existente
        pass

# ✅ BIEN - Agregar nuevo método
class WuzAPIClient:
    def send_message(self):
        # Implementación original intacta
        pass
    
    def send_message_v2(self):
        # Nueva funcionalidad
        pass
```

### 3. **Respetar la Arquitectura de Capas**

```python
# ❌ MAL - domain/ importa de infrastructure/
# src/domain/entities/message.py
from infrastructure.wuzapi.client import WuzAPIClient  # ❌

# ✅ BIEN - domain/ solo conoce interfaces
# src/domain/entities/message.py
from domain.ports.wuzapi_repository import WuzAPIRepository  # ✅
```

### 4. **Dependency Injection Siempre**

```python
# ❌ MAL - Crear dependencias internamente
class UseCase:
    def __init__(self):
        self.repo = ChatwootClient()  # ❌ Acoplamiento fuerte

# ✅ BIEN - Recibir dependencias por constructor
class UseCase:
    def __init__(self, repo: ChatwootRepository):
        self.repo = repo  # ✅ Inversión de dependencias
```

### 5. **Type Hints en Todo**

```python
# ❌ MAL
def process_message(message):
    return something

# ✅ BIEN
def process_message(message: WhatsAppMessage) -> bool:
    return True
```

### 6. **Logging Estructurado**

```python
# ❌ MAL
print("Processing message")

# ✅ BIEN
logger.info(f"📨 Procesando mensaje de {phone}")
logger.error(f"❌ Error: {e}", exc_info=True)
```

---

## 🔧 Cómo Agregar Funcionalidad

### Ejemplo Real: Soporte para Enviar Documentos

#### PASO 1: Extender Entity (si necesario)

```python
# src/domain/entities/whatsapp_message.py

# ✅ AGREGAR nuevo método
def extract_document_info(self) -> Optional[Dict[str, str]]:
    """Extrae información del documento"""
    if self.message_type == MessageType.DOCUMENT:
        return {
            'filename': self.metadata.get('filename'),
            'mimetype': self.metadata.get('mimetype'),
            'url': self.metadata.get('url')
        }
    return None

# ❌ NO modificar métodos existentes como extract_text_content()
```

#### PASO 2: Extender Port (Interfaz)

```python
# src/domain/ports/wuzapi_repository.py

from abc import ABC, abstractmethod

class WuzAPIRepository(ABC):
    
    # Métodos existentes - NO TOCAR
    @abstractmethod
    async def send_text_message(self, phone: str, message: str) -> bool:
        pass
    
    # NUEVO método
    @abstractmethod
    async def send_document_message(
        self,
        phone: str,
        document_url: str,
        filename: str,
        caption: str = ""
    ) -> bool:
        """Envía un documento por WhatsApp"""
        pass
```

#### PASO 3: Implementar en Adaptador

```python
# src/infrastructure/wuzapi/client.py

class WuzAPIClient(WuzAPIRepository):
    
    # Métodos existentes - NO TOCAR
    async def send_text_message(self, phone: str, message: str) -> bool:
        # ... código existente ...
        pass
    
    # NUEVA implementación
    async def send_document_message(
        self,
        phone: str,
        document_url: str,
        filename: str,
        caption: str = ""
    ) -> bool:
        """Implementa envío de documento"""
        try:
            phone_clean = phone.replace('+', '').replace('@s.whatsapp.net', '')
            recipient = f"{phone_clean}@s.whatsapp.net"
            
            url = "/message/document"
            data = {
                'phone': recipient,
                'document': document_url,
                'filename': filename,
                'caption': caption
            }
            
            response = await self.client.post(url, json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Documento enviado a {phone_clean}")
                return True
            else:
                logger.error(f"❌ Error enviando documento: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Error en send_document_message: {e}")
            return False
```

#### PASO 4: Usar en Use Case

```python
# src/application/use_cases/send_message_to_whatsapp.py

async def execute(self, event_data: Dict[str, Any]) -> bool:
    # ... código existente de validación ...
    
    # NUEVO: detectar documentos
    attachments = message_data.get('attachments', [])
    if attachments:
        for attachment in attachments:
            file_type = attachment.get('file_type')
            
            # NUEVA lógica para documentos
            if file_type in ['file', 'pdf', 'document']:
                document_url = attachment.get('data_url')
                filename = attachment.get('file_name', 'documento')
                
                return await self.wuzapi_repo.send_document_message(
                    phone=phone,
                    document_url=document_url,
                    filename=filename,
                    caption=content
                )
    
    # Código existente para texto - NO TOCAR
    return await self.wuzapi_repo.send_text_message(phone, content)
```

---

## 📊 Formato de Datos

### Evento de WuzAPI (Nuevo Formato)

```json
{
  "type": "Message",
  "token": "CCE6198C6E2D-43A0-A4A9-598F53FE5C38",
  "event": {
    "Info": {
      "ID": "3F67AE008F8A522C2716",
      "Chat": "573164973474@s.whatsapp.net",
      "IsFromMe": false,
      "IsGroup": false,
      "Sender": "573164973474:14@s.whatsapp.net",
      "Timestamp": "2025-10-27T15:01:14-05:00",
      "Type": "text",
      "PushName": "Nombre del Cliente"
    },
    "Message": {
      "extendedTextMessage": {
        "text": "Hola, necesito soporte"
      }
    }
  }
}
```

**Campos Importantes:**
- `token`: Identifica la instancia de WuzAPI
- `event.Info.Chat`: Número de teléfono del cliente
- `event.Info.Type`: Tipo de mensaje (text, image, video, etc.)
- `event.Message`: Contenido del mensaje (varía según tipo)

### Evento de Chatwoot

```json
{
  "event": "message_created",
  "account": {
    "id": 2,
    "name": "Fututel"
  },
  "conversation": {
    "id": 123,
    "inbox_id": 29,
    "contact_inbox": {
      "source_id": "573001234567"
    }
  },
  "message": {
    "id": 456,
    "content": "¿Cómo puedo ayudarte?",
    "message_type": "outgoing",
    "sender": {
      "type": "user",
      "name": "Agente de Soporte"
    }
  }
}
```

**Campos Importantes:**
- `event`: Tipo de evento (message_created, conversation_status_changed, etc.)
- `message.message_type`: "outgoing" (agente) o "incoming" (cliente)
- `conversation.contact_inbox.source_id`: Número de teléfono del cliente
- `message.content`: Contenido del mensaje

---

## 🔍 Debugging

### Ver Logs Estructurados

```bash
# Logs en tiempo real
journalctl -u wuzapi-chatwoot-integration -f

# Buscar errores específicos
journalctl -u wuzapi-chatwoot-integration -p err

# Ver último flujo completo
journalctl -u wuzapi-chatwoot-integration --since "5 minutes ago"
```

### Logs Típicos de un Flujo Exitoso

**WhatsApp → Chatwoot:**
```
======================================================================
📥 EVENTO WUZAPI
Tipo: Message | Token: CCE6198C...
======================================================================
✅ Mensaje parseado
   De: +573001234567
   Contenido: Hola, necesito soporte
📨 Sincronizando mensaje de 573001234567
✅ Contacto creado: 573001234567 (ID: 123)
✅ Conversación creada: 456 (Inbox: 29)
✅ Mensaje enviado a conversación 456
✅ Mensaje sincronizado a Chatwoot (Conv: 456)
```

**Chatwoot → WhatsApp:**
```
======================================================================
📥 EVENTO CHATWOOT: message_created
======================================================================
📤 Enviando mensaje a 573001234567
✅ Mensaje enviado a 573001234567 via WuzAPI
```

---

## 🎯 Contexto de Negocio

### Fututel

- **Industria**: Telecomunicaciones
- **Clientes**: 5,000 suscriptores de internet
- **Ubicación**: Colombia
- **Canales de Soporte**:
  - WhatsApp (principal)
  - Chatwoot (gestión interna)
  - Llamadas telefónicas
  - Email

### Casos de Uso Principales

1. **Soporte Técnico**
   - Cliente reporta falla de internet
   - Agente diagnostica y resuelve

2. **Ventas**
   - Cliente pregunta por planes
   - Agente ofrece opciones y cierra venta

3. **Facturación**
   - Cliente consulta sobre su factura
   - Agente verifica y explica cargos

4. **Cobranza**
   - Sistema envía recordatorios de pago
   - Cliente responde con comprobante

---

## ⚙️ Configuración Actual

### Producción

- **Dominio**: `integracion.wuzapi.torneofututel.com`
- **SSL**: Let's Encrypt (auto-renovación)
- **Servidor**: VPS en Proxmox
- **OS**: Ubuntu 24.04 LTS
- **Python**: 3.12+
- **Puerto Interno**: 8789
- **Puerto Público**: 443 (HTTPS)

### Servicios

- **FastAPI**: Backend webhooks
- **Nginx**: Reverse proxy + SSL
- **Redis**: Caché de conversaciones
- **Systemd**: Supervisión del servicio

### Instancia Actual

- **WuzAPI Token**: `CCE6198C6E2D-43A0-A4A9-598F53FE5C38`
- **Chatwoot Inbox**: `29` (Ventas Principal)
- **Número WhatsApp**: +57 316 620 3787

---

## 🚨 Errores Comunes y Soluciones

### Error: "Evento de instancia Unknown ignorado"

**Causa**: El evento no trae el campo `token` o es diferente al configurado.

**Solución**:
```bash
# Verificar token configurado
grep WUZAPI_INSTANCE_TOKEN .env

# Verificar token en webhook de WuzAPI
# Debe coincidir exactamente
```

### Error: "Could not parse message"

**Causa**: El formato del mensaje de WuzAPI cambió o es un tipo no soportado.

**Solución**:
1. Ver el JSON completo en los logs
2. Agregar soporte para nuevo tipo en `WhatsAppMessage.from_wuzapi_event()`

### Error: "Redis no disponible"

**No es un error crítico** - El sistema cambia automáticamente a caché en memoria.

**Para solucionarlo (opcional)**:
```bash
systemctl start redis
systemctl enable redis
```

---

## 📚 Referencias Técnicas

### Arquitectura Hexagonal

- **Paper Original**: Alistair Cockburn (2005)
- **También conocido como**: Ports and Adapters
- **Ventaja Principal**: Independencia de frameworks y librerías

### Principios SOLID

- **S**ingle Responsibility: Una clase, una razón para cambiar
- **O**pen/Closed: Abierto a extensión, cerrado a modificación
- **L**iskov Substitution: Los subtipos deben ser substituibles
- **I**nterface Segregation: Interfaces pequeñas y específicas
- **D**ependency Inversion: Depender de abstracciones, no de concreciones

### Domain-Driven Design

- **Entities**: Objetos con identidad
- **Value Objects**: Objetos inmutables sin identidad
- **Repositories**: Abstracción de persistencia
- **Use Cases**: Lógica de aplicación

---

## 🤝 Cómo Claude Puede Ayudar

### Consultas Permitidas

1. ✅ "¿Cómo agregar soporte para enviar videos?"
2. ✅ "¿Cómo mejorar el manejo de errores?"
3. ✅ "Explica cómo funciona el flujo de WhatsApp → Chatwoot"
4. ✅ "¿Cómo agregar validación de tipos de archivo?"
5. ✅ "Genera tests para el use case"

### Consultas a Evitar

1. ❌ "Refactoriza todo el proyecto"
2. ❌ "Cambia la arquitectura a microservicios"
3. ❌ "Reescribe esto en TypeScript"
4. ❌ "Elimina Redis y usa solo memoria"

### Filosofía de Asistencia

**Regla de Oro**: Si algo funciona, NO se toca.

```
Antes de sugerir cambios, Claude debe:
1. ¿El código actual funciona? → NO cambiar
2. ¿Se necesita nueva funcionalidad? → AGREGAR, no modificar
3. ¿Hay un bug? → Arreglar de forma mínima
4. ¿Mejora la arquitectura? → Solo si no afecta lo existente
```

---

## 🎓 Glosario del Proyecto

- **WuzAPI**: API de WhatsApp Business multi-sesión
- **Chatwoot**: Plataforma open-source de customer service
- **Inbox**: Buzón de entrada en Chatwoot (ej: Ventas, Soporte)
- **Instance**: Sesión de WhatsApp en WuzAPI (1 número = 1 instancia)
- **Token**: Identificador único de una instancia en WuzAPI
- **JID**: WhatsApp ID (formato: 573001234567@s.whatsapp.net)
- **RemoteJID**: Número del cliente en formato WhatsApp
- **Conversation**: Hilo de mensajes con un cliente
- **Contact**: Registro de cliente en Chatwoot

---

## 🔐 Seguridad

### Variables Sensibles

Nunca expongas en logs:
- ❌ `CHATWOOT_API_KEY`
- ❌ `WUZAPI_USER_TOKEN`
- ❌ `WUZAPI_INSTANCE_TOKEN`

Seguro para logs:
- ✅ `CHATWOOT_URL`
- ✅ `WUZAPI_URL`
- ✅ Números de teléfono (son públicos en contexto de negocio)

### Validación de TOKEN

CRÍTICO: Siempre validar que el token del evento coincida con el configurado:

```python
if token != settings.WUZAPI_INSTANCE_TOKEN:
    logger.warning(f"Token inválido: {token}")
    return  # Ignorar evento
```

---

## 📞 Contacto

Para dudas sobre el proyecto:
- **Desarrollador Principal**: Fututel Programación
- **WhatsApp**: +57 316 497 3474
- **Email**: soporte@fututel.com

---

**Última Actualización**: 2025-10-27  
**Versión del Proyecto**: 2.0.0  
**Python**: 3.12+  
**FastAPI**: 0.104+
