# 🚀 WuzAPI ↔ Chatwoot Integration

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Architecture](https://img.shields.io/badge/architecture-hexagonal-orange.svg)](https://en.wikipedia.org/wiki/Hexagonal_architecture_(software))

Integración bidireccional profesional entre **WuzAPI (WhatsApp)** y **Chatwoot** usando **Arquitectura Hexagonal**, principios **SOLID** y mejores prácticas de ingeniería de software.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#️-arquitectura)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación](#-instalación)
- [Configuración](#️-configuración)
- [Uso](#-uso)
- [Flujos de Datos](#-flujos-de-datos)
- [Desarrollo](#-desarrollo)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Características

### Técnicas
- ✅ **Arquitectura Hexagonal** (Ports & Adapters) - Separación clara de responsabilidades
- ✅ **Principios SOLID** - Código mantenible y escalable
- ✅ **Domain-Driven Design (DDD)** - Lógica de negocio en el dominio
- ✅ **Type Hints Completos** - Type safety con Python 3.12+
- ✅ **Async/Await** - Operaciones I/O no bloqueantes
- ✅ **Dependency Injection** - Vía parámetros de constructores

### Funcionales
- ✅ **Integración Bidireccional** WhatsApp ↔ Chatwoot
- ✅ **Multi-instancia Ready** - 1 contenedor = 1 token = 1 inbox
- ✅ **Validación por TOKEN** - Seguridad y aislamiento
- ✅ **Caché Inteligente** - Redis con fallback en memoria
- ✅ **Logs Estructurados** - Debugging fácil con contexto

### Operacionales
- ✅ **Docker Compose** - Deploy rápido y reproducible
- ✅ **Nginx + SSL/TLS** - Producción con Let's Encrypt
- ✅ **Systemd Service** - Autostart y supervisión
- ✅ **Health Checks** - Monitoreo del estado

---

## 🏗️ Arquitectura

### Diagrama de Capas (Hexagonal)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA EXTERNA - ENTRADA                           │
│  📥 Adaptadores Primarios (Infraestructura)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  src/infrastructure/api/webhook.py                                  │
│  ├─ POST /webhook/wuzapi     ← Recibe eventos de WuzAPI            │
│  ├─ POST /webhook/chatwoot   ← Recibe eventos de Chatwoot          │
│  ├─ GET /health              ← Health check                        │
│  └─ GET /                    ← Info del servicio                   │
│                                                                     │
│  Responsabilidad: Transformar HTTP requests → llamadas al dominio  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN                               │
│  🎯 Casos de Uso (Application)                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  src/application/use_cases/                                         │
│  ├─ sync_message_to_chatwoot.py                                    │
│  │  Orquesta: WhatsApp → Chatwoot                                  │
│  │  1. Validar mensaje                                             │
│  │  2. Crear/buscar contacto                                       │
│  │  3. Crear/buscar conversación                                   │
│  │  4. Enviar mensaje                                              │
│  │                                                                  │
│  └─ send_message_to_whatsapp.py                                    │
│     Orquesta: Chatwoot → WhatsApp                                  │
│     1. Validar evento                                              │
│     2. Extraer datos                                               │
│     3. Enviar a WuzAPI                                             │
│                                                                     │
│  Responsabilidad: Coordinar el flujo de negocio                    │
│  NO conoce HTTP, Redis, ni detalles técnicos                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE DOMINIO (CORE)                           │
│  ❤️  Núcleo del Negocio (Domain)                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  src/domain/                                                        │
│  │                                                                  │
│  ├─ entities/                                                       │
│  │  └─ whatsapp_message.py                                         │
│  │     Entidad rica con lógica de negocio                          │
│  │     - Representa un mensaje de WhatsApp                         │
│  │     - Métodos: is_incoming(), extract_text_content()            │
│  │     - Factory: from_wuzapi_event()                              │
│  │                                                                  │
│  ├─ value_objects/                                                  │
│  │  └─ phone_number.py                                             │
│  │     Objeto de valor inmutable                                   │
│  │     - Validación automática                                     │
│  │     - Normalización de formatos                                 │
│  │     - Métodos: from_whatsapp_jid(), is_group                    │
│  │                                                                  │
│  └─ ports/  (INTERFACES - Contratos)                               │
│     ├─ chatwoot_repository.py                                      │
│     │  Define QUÉ hacer con Chatwoot (no CÓMO)                     │
│     │  - create_or_get_contact()                                   │
│     │  - create_or_get_conversation()                              │
│     │  - send_message()                                            │
│     │                                                               │
│     ├─ wuzapi_repository.py                                        │
│     │  Define QUÉ hacer con WuzAPI (no CÓMO)                       │
│     │  - send_text_message()                                       │
│     │                                                               │
│     └─ cache_repository.py                                         │
│        Define QUÉ hacer con el caché (no CÓMO)                     │
│        - get_conversation_id()                                     │
│        - set_conversation_id()                                     │
│                                                                     │
│  Responsabilidad: Reglas de negocio puras                          │
│  Define interfaces (ports) sin conocer implementaciones            │
│  CERO dependencias externas                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA EXTERNA - SALIDA                            │
│  📤 Adaptadores Secundarios (Infraestructura)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  src/infrastructure/                                                │
│  │                                                                  │
│  ├─ chatwoot/client.py                                             │
│  │  Implementa ChatwootRepository                                  │
│  │  - Comunicación HTTP con API Chatwoot                           │
│  │  - Maneja autenticación                                         │
│  │  - Transforma respuestas HTTP → entidades del dominio           │
│  │                                                                  │
│  ├─ wuzapi/client.py                                               │
│  │  Implementa WuzAPIRepository                                    │
│  │  - Comunicación HTTP con API WuzAPI                             │
│  │  - Normaliza números de teléfono                                │
│  │  - Maneja formato de mensajes                                   │
│  │                                                                  │
│  ├─ persistence/                                                    │
│  │  ├─ redis_cache.py                                              │
│  │  │  Implementa CacheRepository con Redis                        │
│  │  │  - Conexión a Redis                                          │
│  │  │  - Serialización/deserialización                             │
│  │  │                                                               │
│  │  └─ memory_cache.py                                             │
│  │     Implementa CacheRepository en memoria                       │
│  │     - Fallback cuando Redis no disponible                       │
│  │     - Dict Python simple                                        │
│  │                                                                  │
│  └─ logging/setup.py                                               │
│     Configuración de logging                                       │
│                                                                     │
│  Responsabilidad: Detalles técnicos de implementación              │
│  Pueden cambiar sin afectar el dominio                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  🛠️  SHARED - Utilidades Compartidas                               │
├─────────────────────────────────────────────────────────────────────┤
│  src/shared/config.py                                               │
│  - Configuración centralizada con Pydantic                          │
│  - Validación de variables de entorno                              │
│  - Type-safe settings                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Principios SOLID Aplicados

| Principio | Implementación en el Proyecto |
|-----------|-------------------------------|
| **S**ingle Responsibility | - WhatsAppMessage: solo representa mensajes<br>- ChatwootClient: solo se comunica con Chatwoot<br>- SyncMessageToChatwootUseCase: solo sincroniza a Chatwoot |
| **O**pen/Closed | - Puedes agregar nuevos adaptadores (ej: TwilioClient) sin modificar el dominio<br>- Extensible vía implementación de ports |
| **L**iskov Substitution | - RedisCache y InMemoryCache son intercambiables<br>- Ambos implementan CacheRepository |
| **I**nterface Segregation | - Interfaces pequeñas y específicas<br>- ChatwootRepository solo métodos de Chatwoot<br>- No hay una interfaz gigante "Repository" |
| **D**ependency Inversion | - UseCase depende de interfaces (ports), no de implementaciones<br>- ChatwootClient implementa la interfaz del dominio<br>- El dominio no conoce a FastAPI, Redis, ni HTTP |

---

## 📁 Estructura del Proyecto

```
wuzapi-consumer/
│
├── 📂 src/                          # Código fuente principal
│   │
│   ├── 📂 domain/                   # ❤️  NÚCLEO DEL NEGOCIO
│   │   │                            # Reglas de negocio puras
│   │   │                            # CERO dependencias externas
│   │   │
│   │   ├── 📂 entities/             # Entidades con identidad
│   │   │   └── whatsapp_message.py  # Representa un mensaje de WhatsApp
│   │   │                            # - ID único (message_id)
│   │   │                            # - Lógica de negocio
│   │   │                            # - Factory methods
│   │   │
│   │   ├── 📂 value_objects/        # Objetos de valor inmutables
│   │   │   └── phone_number.py      # Representa un número de teléfono
│   │   │                            # - Inmutable (frozen dataclass)
│   │   │                            # - Auto-validación
│   │   │                            # - Sin identidad propia
│   │   │
│   │   └── 📂 ports/                # Interfaces (contratos)
│   │       ├── chatwoot_repository.py    # QUÉ hacer con Chatwoot
│   │       ├── wuzapi_repository.py      # QUÉ hacer con WuzAPI
│   │       └── cache_repository.py       # QUÉ hacer con caché
│   │                                # IMPORTANTE: Solo definen métodos
│   │                                # NO implementan nada
│   │
│   ├── 📂 application/              # 🎯 CASOS DE USO
│   │   │                            # Orquestación de lógica de negocio
│   │   │                            # Coordinan múltiples operaciones
│   │   │
│   │   └── 📂 use_cases/
│   │       ├── sync_message_to_chatwoot.py
│   │       │   # Flujo: WhatsApp → Chatwoot
│   │       │   # 1. Recibe WhatsAppMessage
│   │       │   # 2. Crea/busca contacto
│   │       │   # 3. Crea/busca conversación
│   │       │   # 4. Envía mensaje
│   │       │
│   │       └── send_message_to_whatsapp.py
│   │           # Flujo: Chatwoot → WhatsApp
│   │           # 1. Recibe evento de Chatwoot
│   │           # 2. Extrae datos
│   │           # 3. Envía a WuzAPI
│   │
│   ├── 📂 infrastructure/           # 🔌 ADAPTADORES
│   │   │                            # Detalles técnicos de implementación
│   │   │                            # Pueden cambiar sin afectar dominio
│   │   │
│   │   ├── 📂 api/                  # Entrada HTTP
│   │   │   └── webhook.py           # FastAPI webhooks
│   │   │                            # - POST /webhook/wuzapi
│   │   │                            # - POST /webhook/chatwoot
│   │   │                            # - GET /health
│   │   │
│   │   ├── 📂 chatwoot/             # Salida a Chatwoot
│   │   │   └── client.py            # Implementa ChatwootRepository
│   │   │                            # - HTTP client con httpx
│   │   │                            # - Autenticación con API key
│   │   │                            # - Transforma JSON ↔ Entities
│   │   │
│   │   ├── 📂 wuzapi/               # Salida a WuzAPI
│   │   │   └── client.py            # Implementa WuzAPIRepository
│   │   │                            # - HTTP client con httpx
│   │   │                            # - Autenticación con token
│   │   │                            # - Normaliza teléfonos
│   │   │
│   │   ├── 📂 persistence/          # Salida a base de datos/caché
│   │   │   ├── redis_cache.py       # Implementación con Redis
│   │   │   │                        # - Conexión async
│   │   │   │                        # - Serialización JSON
│   │   │   │
│   │   │   └── memory_cache.py      # Implementación en memoria
│   │   │                            # - Fallback sin Redis
│   │   │                            # - Dict Python simple
│   │   │
│   │   └── 📂 logging/              # Configuración de logs
│   │       └── setup.py             # Configuración de logging
│   │
│   └── 📂 shared/                   # 🛠️  UTILIDADES COMPARTIDAS
│       └── config.py                # Configuración con Pydantic
│                                    # - Lee variables de entorno
│                                    # - Validación automática
│                                    # - Type-safe settings
│
├── 📄 main.py                       # 🚀 ENTRY POINT
│                                    # - Configura e inicia FastAPI
│                                    # - Inicializa dependencias
│                                    # - Maneja ciclo de vida
│
├── 📄 .env                          # 🔐 Variables de entorno (NO commitear)
├── 📄 .env.example                  # 📝 Template de configuración
│
├── 📄 pyproject.toml                # 📦 Dependencias del proyecto
│                                    # - Usa uv para gestión
│                                    # - Python 3.12+
│
├── 📄 docker-compose.yml            # 🐳 Orquestación de contenedores
├── 📄 Dockerfile                    # 🐳 Imagen Docker
│
├── 📄 README.md                     # 📖 Este archivo
├── 📄 ARCHITECTURE.md               # 🏗️  Detalles de arquitectura
├── 📄 CLAUDE.md                     # 🤖 Contexto para Claude AI
└── 📄 llm.txt                       # 🤖 Contexto para LLMs
```

### 🎯 Explicación de Carpetas

#### `src/domain/` - El Corazón del Sistema

**Regla de Oro**: NUNCA debe depender de `infrastructure/` o `application/`

- **entities/**: Objetos con identidad única (ej: WhatsAppMessage tiene un `message_id`)
- **value_objects/**: Objetos inmutables sin identidad (ej: PhoneNumber, Email)
- **ports/**: Interfaces que definen QUÉ hacer, no CÓMO hacerlo

#### `src/application/` - La Orquestación

**Regla de Oro**: Depende de `domain/`, NO de `infrastructure/`

- Coordina múltiples operaciones del dominio
- Usa los ports (interfaces) para comunicarse con el exterior
- NO sabe de HTTP, Redis, SQL, etc.

#### `src/infrastructure/` - Los Detalles

**Regla de Oro**: Implementa los ports del dominio

- Puede cambiar completamente sin afectar `domain/` o `application/`
- Ejemplo: cambiar de Redis a Memcached solo requiere crear nuevo adaptador

#### `src/shared/` - Utilidades Transversales

- Código usado por todas las capas
- Configuración, constantes, helpers

---

## 🚀 Instalación

### Requisitos Previos

- **Python**: 3.12+
- **Redis**: 6+ (opcional, tiene fallback en memoria)
- **Nginx**: Con SSL/TLS (producción)
- **WuzAPI**: Instancia activa con token
- **Chatwoot**: Cuenta con API key

### Paso 1: Clonar e Instalar Dependencias

```bash
cd /home/wuzapi-consumer

# Instalar uv (gestor de dependencias moderno)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias del proyecto
uv sync
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar con tus credenciales
nano .env
```

**Contenido del .env:**
```properties
# =============================================================================
# CONFIGURACIÓN WUZAPI ↔ CHATWOOT (1:1)
# =============================================================================

# Servidor
PORT=8789
HOST=0.0.0.0
LOG_LEVEL=INFO
BACKEND_URL=integracion.wuzapi.torneofututel.com

# ============= CHATWOOT =============
CHATWOOT_URL=https://chatwoot.fututel.com
CHATWOOT_API_KEY=tu_api_key_aqui
CHATWOOT_ACCOUNT_ID=2
CHATWOOT_INBOX_ID=29

# ============= WUZAPI =============
WUZAPI_URL=https://wuzapi.torneofututel.com
WUZAPI_USER_TOKEN=tu_user_token_aqui
WUZAPI_INSTANCE_TOKEN=tu_instance_token_aqui

# ============= REDIS =============
REDIS_URL=redis://localhost:6379/0

# ============= CELERY =============
USE_CELERY=false
```

### Paso 3: Configurar Nginx con SSL

```bash
# Instalar certbot si no está instalado
apt install certbot python3-certbot-nginx -y

# Obtener certificado SSL automático
certbot --nginx -d integracion.wuzapi.torneofututel.com --non-interactive --agree-tos --email tu@email.com

# Nginx configurará SSL automáticamente
systemctl reload nginx
```

### Paso 4: Crear Servicio Systemd

```bash
cat > /etc/systemd/system/wuzapi-chatwoot-integration.service << 'EOF'
[Unit]
Description=WuzAPI Chatwoot Integration Webhook
After=network.target redis.service nginx.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/wuzapi-consumer
Environment="PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/root/.local/bin/uv run python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
systemctl daemon-reload

# Habilitar autostart
systemctl enable wuzapi-chatwoot-integration

# Iniciar servicio
systemctl start wuzapi-chatwoot-integration

# Ver estado
systemctl status wuzapi-chatwoot-integration
```

---

## ⚙️ Configuración

### Configurar Webhook en WuzAPI

1. Abre la interfaz de WuzAPI
2. Ve a la configuración de tu instancia
3. Configura:
   - **Webhook URL**: `https://integracion.wuzapi.torneofututel.com/webhook/wuzapi`
   - **Events**: `Message` (todos los mensajes)
   - **IMPORTANTE**: NO incluir el puerto `:8789` en la URL

### Configurar Webhook en Chatwoot

**Opción A: Via Interfaz Web**
1. Abre Chatwoot: `https://chatwoot.fututel.com`
2. Ve a **Settings** → **Integrations** → **Webhooks**
3. Click **"Add Webhook"**
4. Completa:
   - **URL**: `https://integracion.wuzapi.torneofututel.com/webhook/chatwoot`
   - **Events**: Marca solo `message_created`
5. Click **"Create"**

**Opción B: Via API**
```bash
curl -X POST https://chatwoot.fututel.com/api/v1/accounts/2/webhooks \
  -H "api_access_token: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://integracion.wuzapi.torneofututel.com/webhook/chatwoot",
    "subscriptions": ["message_created"]
  }'
```

---

## 🎯 Uso

### Comandos Básicos

```bash
# Iniciar servicio
systemctl start wuzapi-chatwoot-integration

# Detener servicio
systemctl stop wuzapi-chatwoot-integration

# Reiniciar servicio
systemctl restart wuzapi-chatwoot-integration

# Ver estado
systemctl status wuzapi-chatwoot-integration

# Ver logs en tiempo real
journalctl -u wuzapi-chatwoot-integration -f

# Ver últimas 100 líneas de logs
journalctl -u wuzapi-chatwoot-integration -n 100

# Ver solo errores
journalctl -u wuzapi-chatwoot-integration -p err

# Ver logs desde hace 2 horas
journalctl -u wuzapi-chatwoot-integration --since "2 hours ago"
```

### Health Check

```bash
# Local
curl http://localhost:8789/health | jq

# Público (HTTPS)
curl https://integracion.wuzapi.torneofututel.com/health | jq
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "mapping": {
    "wuzapi_token": "CCE6198C6E2D-43A0-A4A9-598F53FE5C38",
    "chatwoot_inbox": "29"
  },
  "integrations": {
    "wuzapi": {
      "url": "https://wuzapi.torneofututel.com",
      "configured": true
    },
    "chatwoot": {
      "url": "https://chatwoot.fututel.com",
      "configured": true
    }
  },
  "cache": {
    "type": "redis"
  }
}
```

---

## 🔄 Flujos de Datos

### Flujo 1: WhatsApp → Chatwoot

```
┌─────────────┐
│  📱 Cliente │ Envía mensaje "Hola"
│  WhatsApp   │
└──────┬──────┘
       ↓
┌──────────────────┐
│  💚 WuzAPI       │ Recibe mensaje
│  (Tu Instancia)  │
└──────┬───────────┘
       ↓ webhook POST
┌───────────────────────────────────────────────────────────┐
│  🌐 Nginx (SSL)                                           │
│  https://integracion.wuzapi.torneofututel.com            │
└──────┬────────────────────────────────────────────────────┘
       ↓ proxy_pass
┌───────────────────────────────────────────────────────────┐
│  🐍 FastAPI Backend (localhost:8789)                      │
│  src/infrastructure/api/webhook.py                        │
│                                                           │
│  1. Valida TOKEN (¿Es mi instancia?)                     │
│  2. Parsea JSON → WhatsAppMessage entity                 │
└──────┬────────────────────────────────────────────────────┘
       ↓
┌───────────────────────────────────────────────────────────┐
│  🎯 SyncMessageToChatwootUseCase                          │
│  src/application/use_cases/sync_message_to_chatwoot.py   │
│                                                           │
│  Paso A: Buscar/crear contacto                           │
│     → ChatwootClient.create_or_get_contact()             │
│     → Busca por teléfono en Chatwoot                     │
│     → Si no existe, lo crea                              │
│                                                           │
│  Paso B: Buscar/crear conversación                       │
│     → ChatwootClient.create_or_get_conversation()        │
│     → Busca conversación existente                       │
│     → Si no existe, la crea en el inbox correcto         │
│                                                           │
│  Paso C: Enviar mensaje                                  │
│     → ChatwootClient.send_message()                      │
│     → Envía contenido del mensaje                        │
└──────┬────────────────────────────────────────────────────┘
       ↓ HTTP API calls
┌───────────────────────────────────────────────────────────┐
│  💬 Chatwoot                                              │
│  https://chatwoot.fututel.com                            │
│                                                           │
│  ✅ Mensaje aparece en Inbox 29                          │
└───────────────────────────────────────────────────────────┘
       ↓
┌──────────────┐
│  👤 Agente   │ Ve el mensaje
│  Chatwoot    │
└──────────────┘
```

### Flujo 2: Chatwoot → WhatsApp

```
┌──────────────┐
│  👤 Agente   │ Responde "¿Cómo te ayudo?"
│  Chatwoot    │
└──────┬───────┘
       ↓
┌───────────────────────────────────────────────────────────┐
│  💬 Chatwoot                                              │
│  Detecta mensaje outgoing                                │
└──────┬────────────────────────────────────────────────────┘
       ↓ webhook POST
┌───────────────────────────────────────────────────────────┐
│  🌐 Nginx (SSL)                                           │
│  https://integracion.wuzapi.torneofututel.com            │
└──────┬────────────────────────────────────────────────────┘
       ↓ proxy_pass
┌───────────────────────────────────────────────────────────┐
│  🐍 FastAPI Backend (localhost:8789)                      │
│  src/infrastructure/api/webhook.py                        │
│                                                           │
│  1. Parsea evento de Chatwoot                            │
│  2. Extrae datos del mensaje                             │
└──────┬────────────────────────────────────────────────────┘
       ↓
┌───────────────────────────────────────────────────────────┐
│  🎯 SendMessageToWhatsAppUseCase                          │
│  src/application/use_cases/send_message_to_whatsapp.py   │
│                                                           │
│  1. Valida que sea mensaje outgoing                      │
│  2. Extrae número de teléfono del contacto               │
│  3. Extrae contenido del mensaje                         │
│  4. Llama a WuzAPIClient.send_text_message()             │
└──────┬────────────────────────────────────────────────────┘
       ↓ HTTP API call
┌───────────────────────────────────────────────────────────┐
│  💚 WuzAPI                                                │
│  https://wuzapi.torneofututel.com                        │
│                                                           │
│  Envía mensaje por WhatsApp                              │
└──────┬────────────────────────────────────────────────────┘
       ↓
┌─────────────┐
│  📱 Cliente │ Recibe "¿Cómo te ayudo?"
│  WhatsApp   │
└─────────────┘
```

---

## 🛠️ Desarrollo

### Reglas de Oro

#### 1. **NUNCA Modificar lo que Funciona**
```
❌ MAL:  "Voy a refactorizar todo el código"
✅ BIEN: "Voy a agregar funcionalidad nueva sin tocar lo existente"
```

#### 2. **Siempre Agregar, Nunca Eliminar**
```
❌ MAL:  Eliminar funcionalidad antigua
✅ BIEN: Deprecar y crear nueva versión
```

#### 3. **Respetar las Capas**
```
❌ MAL:  domain/ importa de infrastructure/
✅ BIEN: domain/ solo conoce sus propias interfaces (ports)
```

#### 4. **Dependency Injection**
```
❌ MAL:  use_case = UseCase()  # Crea sus propias dependencias
✅ BIEN: use_case = UseCase(repo, cache)  # Recibe dependencias
```

### Agregar Nueva Funcionalidad

#### Ejemplo: Agregar Soporte para Enviar Imágenes

**PASO 1: Extender el Dominio (si es necesario)**
```python
# src/domain/entities/whatsapp_message.py
# ✅ AGREGAR nuevo método, NO modificar existentes

def extract_image_url(self) -> Optional[str]:
    """Extrae URL de imagen si el mensaje la contiene"""
    if self.message_type == MessageType.IMAGE:
        return self.metadata.get('url')
    return None
```

**PASO 2: Extender el Port (Interfaz)**
```python
# src/domain/ports/wuzapi_repository.py
# ✅ AGREGAR nuevo método a la interfaz

from abc import ABC, abstractmethod

class WuzAPIRepository(ABC):
    
    @abstractmethod
    async def send_text_message(self, phone: str, message: str) -> bool:
        """Método existente - NO TOCAR"""
        pass
    
    @abstractmethod
    async def send_image_message(
        self, 
        phone: str, 
        image_url: str, 
        caption: str = ""
    ) -> bool:
        """NUEVO método para enviar imágenes"""
        pass
```

**PASO 3: Implementar en el Adaptador**
```python
# src/infrastructure/wuzapi/client.py
# ✅ AGREGAR nuevo método, NO modificar send_text_message

class WuzAPIClient(WuzAPIRepository):
    
    # Método existente - NO TOCAR
    async def send_text_message(self, phone: str, message: str) -> bool:
        # ... código existente ...
        pass
    
    # NUEVO método
    async def send_image_message(
        self, 
        phone: str, 
        image_url: str, 
        caption: str = ""
    ) -> bool:
        """Implementación para enviar imagen"""
        try:
            phone_clean = phone.replace('+', '').replace('@s.whatsapp.net', '')
            recipient = f"{phone_clean}@s.whatsapp.net"
            
            url = "/message/image"
            data = {
                'phone': recipient,
                'image': image_url,
                'caption': caption
            }
            
            response = await self.client.post(url, json=data)
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error enviando imagen: {e}")
            return False
```

**PASO 4: Usar en el Caso de Uso (si aplica)**
```python
# src/application/use_cases/send_message_to_whatsapp.py
# ✅ AGREGAR lógica para detectar y enviar imágenes

async def execute(self, event_data: Dict[str, Any]) -> bool:
    # ... validaciones existentes ...
    
    # NUEVO: detectar si hay imagen
    attachments = message_data.get('attachments', [])
    if attachments:
        for attachment in attachments:
            if attachment.get('file_type') == 'image':
                image_url = attachment.get('data_url')
                await self.wuzapi_repo.send_image_message(
                    phone=phone,
                    image_url=image_url,
                    caption=content
                )
                return True
    
    # Flujo existente para texto - NO TOCAR
    return await self.wuzapi_repo.send_text_message(phone, content)
```

### Testing

```bash
# Ejecutar en modo desarrollo
uv run python main.py

# Ver logs en tiempo real
journalctl -u wuzapi-chatwoot-integration -f

# Test manual
# 1. Envía mensaje de WhatsApp
# 2. Verifica logs
# 3. Verifica que llegó a Chatwoot
# 4. Responde en Chatwoot
# 5. Verifica que llegó a WhatsApp
```

---

## 🔧 Troubleshooting

### El servicio no inicia

```bash
# Ver logs del servicio
journalctl -u wuzapi-chatwoot-integration -n 50

# Ver errores específicos
journalctl -u wuzapi-chatwoot-integration -p err

# Verificar que el puerto no esté ocupado
lsof -i :8789

# Verificar configuración
cat .env

# Probar arranque manual
cd /home/wuzapi-consumer
uv run python main.py
```

### Los mensajes de WhatsApp no llegan a Chatwoot

```bash
# 1. Verificar que el webhook esté configurado en WuzAPI
# Ve a la interfaz de WuzAPI y verifica la URL del webhook

# 2. Ver logs cuando envías un mensaje
journalctl -u wuzapi-chatwoot-integration -f

# 3. Verificar que el TOKEN sea correcto
grep WUZAPI_INSTANCE_TOKEN .env

# 4. Test manual del webhook
curl -X POST https://integracion.wuzapi.torneofututel.com/webhook/wuzapi \
  -H "Content-Type: application/json" \
  -d '{"type":"Message","token":"TU_TOKEN"}'
```

### Las respuestas de Chatwoot no llegan a WhatsApp

```bash
# 1. Verificar que el webhook esté configurado en Chatwoot
# Settings → Integrations → Webhooks

# 2. Ver logs cuando respondes en Chatwoot
journalctl -u wuzapi-chatwoot-integration -f

# 3. Verificar conectividad con WuzAPI
curl https://wuzapi.torneofututel.com/health
```

### Redis no conecta

```bash
# Verificar que Redis esté corriendo
systemctl status redis

# Iniciar Redis si está detenido
systemctl start redis

# Ver logs de Redis
journalctl -u redis -f

# Test de conexión
redis-cli ping
# Debe responder: PONG

# NOTA: Si Redis no funciona, el sistema usa caché en memoria automáticamente
```

### SSL/HTTPS no funciona

```bash
# Verificar certificados
certbot certificates

# Renovar certificados
certbot renew

# Ver logs de Nginx
tail -f /var/log/nginx/integracion_wuzapi_error.log

# Test de SSL
curl -v https://integracion.wuzapi.torneofututel.com/health
```

---

## 📚 Documentación Adicional

- **ARCHITECTURE.md**: Detalles profundos de la arquitectura hexagonal
- **CLAUDE.md**: Contexto y reglas para Claude AI
- **llm.txt**: Formato condensado para LLMs

---

## 📝 Licencia

Proyecto propietario de Fututel.

---

## 👤 Autor

**Fututel - Equipo de Ingeniería**

- Sistema desarrollado para integración empresarial
- Arquitectura diseñada para escalabilidad y mantenibilidad
- Contacto: soporte@fututel.com

---

## 🔄 Changelog

### v2.0.0 (2025-10-27)
- ✅ Arquitectura hexagonal completa
- ✅ Soporte para nuevo formato de WuzAPI (con token)
- ✅ Validación por TOKEN en lugar de instanceId
- ✅ Logs estructurados con JSON completo
- ✅ Documentación exhaustiva

### v1.0.0 (Anterior)
- Versión inicial con formato antiguo de WuzAPI
