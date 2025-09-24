# Servidor Local MCP - Instrucciones

## Instalación

1. **Instalar dependencias adicionales:**
```bash
pip install -r requirements_server.txt
```

## Configuración

2. **Asegurar variables de entorno:**
```bash
# Tu archivo .env debe tener:
ANTHROPIC_API_KEY=tu_api_key_aqui
CLAUDE_MODEL=claude-3-haiku-20240307
```

## Uso

### 1. Ejecutar el Servidor
```bash
# Terminal 1: Ejecutar servidor local
python3 server_local.py
```

**El servidor estará disponible en:**
-  **API**: http://localhost:8000
- 📚 **Documentación**: http://localhost:8000/docs  
- 🏥 **Health Check**: http://localhost:8000/health

### 2. Ejecutar el Cliente
```bash
# Terminal 2: Ejecutar cliente que se conecta al servidor
python3 main_client.py
```

## Modos de Uso

### Opción A: Cliente-Servidor (Recomendado)
```bash
# Terminal 1
python3 server_local.py

# Terminal 2  
python3 main_client.py
```

### Opción B: Solo Local (Modo Original)
```bash
python3 main.py
```

### Opción C: Solo Servidor (API)
```bash
# Ejecutar solo el servidor y usar las APIs directamente
python3 server_local.py

# Hacer requests HTTP a los endpoints
curl http://localhost:8000/health
```

## Endpoints Principales

### Chat
- `POST /chat` - Enviar mensaje a Claude
- `GET /sessions/{id}/stats` - Estadísticas de sesión
- `POST /sessions/{id}/clear` - Limpiar contexto

### Sistema de Belleza
- `POST /beauty/profile` - Crear perfil
- `GET /beauty/profiles` - Listar perfiles
- `GET /beauty/profile/{user_id}` - Ver perfil específico
- `POST /beauty/palette` - Generar paleta
- `GET /beauty/history/{user_id}` - Historial de usuario

### Citas Inspiracionales
- `GET /quotes/get?category=X` - Obtener cita
- `GET /quotes/search/{query}` - Buscar citas
- `GET /quotes/wisdom` - Sabiduría diaria

### Git/Filesystem
- `POST /git/command` - Ejecutar comando git/fs

### Sistema
- `GET /health` - Estado del servidor
- `GET /logs/mcp` - Logs MCP
- `GET /logs/beauty` - Logs de belleza

## Ejemplos de Comandos en el Cliente

```bash
# Crear perfil
/beauty create_profile

# Ver perfiles
/beauty list_profiles

# Generar paleta
/palette ropa usuario_123 formal

# Chat normal
¿Qué colores me quedan bien para una entrevista?

# Citas
/quotes get motivacion

# Git
/fs write test.txt "Hola mundo"
/fs read test.txt
```

## Ventajas del Modo Cliente-Servidor

✅ **Escalabilidad**: Múltiples clientes pueden conectarse al mismo servidor  
✅ **Separación**: Lógica de negocio en servidor, UI en cliente  
✅ **APIs**: Endpoints HTTP para integraciones externas  
✅ **Monitoreo**: Logs centralizados en el servidor  
✅ **Desarrollo**: Diferentes clientes (terminal, web, móvil) pueden usar la misma API

## Troubleshooting

**Error: "No se pudo conectar al servidor"**
- Verificar que el servidor esté corriendo: `python3 server_local.py`
- Verificar el puerto 8000 esté libre
- Revisar que no hay firewall bloqueando

**Error: "Service no disponible"**
- Verificar variables de entorno (.env)
- Revisar logs del servidor para errores de inicialización

**Error de dependencias**
- Ejecutar: `pip install -r requirements_server.txt`

## Logs y Monitoreo

- **Servidor**: Los logs aparecen en la consola donde ejecutaste `server_local.py`
- **Cliente**: Los errores aparecen en la consola del cliente
- **Archivos**: Los logs se guardan en la carpeta `logs/` del servidor