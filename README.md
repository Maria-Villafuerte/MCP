# MCPChatbot - Sistema de Belleza con Claude API

Un sistema de chat inteligente especializado en belleza y estilo personal, construido con arquitectura MVC y capacidades MCP (Model Context Protocol).

##  Características Principales

### Sistema de Belleza Avanzado
- **Perfiles Personalizados**: Crea perfiles basados en tono de piel, color de ojos, tipo de cabello y preferencias de estilo
- **Paletas de Colores Inteligentes**: Generación automática de paletas para ropa, maquillaje y accesorios
- **Teoría del Color**: Algoritmos avanzados basados en colorimetría y armonías de color
- **Recomendaciones Contextuales**: Sugerencias específicas según evento, estación y estilo personal

### Integración con Claude API
- **Conversación Natural**: Chat fluido con Claude Haiku para consejos de belleza y estilo
- **Contexto Personalizado**: Claude considera tu perfil personal en las recomendaciones
- **Análisis Inteligente**: Evaluación de compatibilidad de colores y tendencias

### Funcionalidades Adicionales
- **Citas Inspiracionales**: Conexión con servidor remoto para motivación diaria
- **Gestión de Archivos**: Sistema completo de archivos con soporte Git
- **Historial Completo**: Seguimiento de paletas generadas y preferencias
- **Logging Avanzado**: Registro detallado de todas las interacciones

## 🏗️ Arquitectura

### Estructura MVC
```
src/
├── models/                 # Modelos de datos
│   ├── session_model.py   # Gestión de sesiones
│   ├── beauty_model.py    # Datos de belleza y perfiles
│   └── logging_model.py   # Sistema de logging
├── views/                 # Interfaces de usuario
│   ├── chat_view.py      # Vista principal del chat
│   └── beauty_view.py    # Vista del sistema de belleza
├── controllers/           # Lógica de control
│   ├── main_controller.py     # Controlador principal
│   ├── beauty_controller.py   # Controlador de belleza
│   ├── quotes_controller.py   # Controlador de citas
│   └── git_controller.py      # Controlador de archivos/git
├── services/              # Servicios especializados
│   ├── claude_service.py      # Servicio de Claude API
│   ├── beauty_service.py      # Servicio de paletas avanzado
│   └── remote_quotes_service.py # Servicio de citas remotas
└── main.py               # Punto de entrada
```

##  Instalación

### Prerrequisitos
- Python 3.8 o superior
- Cuenta de Anthropic con API key
- Git (opcional, para control de versiones)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/Maria-Villafuerte/MCP.git
cd MCP
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tu API key de Anthropic
```

5. **Ejecutar el sistema**
```bash
python main.py
```

##  Configuración

### Variables de Entorno (.env)
```bash
# API Key de Anthropic (REQUERIDO)
ANTHROPIC_API_KEY=tu_api_key_aqui

# Modelo de Claude (opcional)
CLAUDE_MODEL=claude-3-haiku-20240307

# Configuración de logging (opcional)
LOG_LEVEL=INFO
```

### Configuración Avanzada
- **Modelos disponibles**: claude-3-haiku-20240307, claude-3-sonnet-20240229, claude-3-opus-20240229
- **Directorio de trabajo**: Se crea automáticamente en `mcp_workspace/`
- **Logs**: Se guardan en el directorio `logs/`
- **Sesiones**: Se almacenan en `sessions/`
- **Datos de belleza**: Se guardan en `beauty_data/`

##  Comandos Principales

### Sistema de Belleza
```bash
# Gestión de perfiles
/beauty create_profile          # Crear perfil personalizado
/beauty profile <user_id>       # Ver perfil específico
/beauty list_profiles           # Listar todos los perfiles
/beauty history <user_id>       # Ver historial de paletas

# Generación de paletas
/palette ropa <user_id> <evento>        # Paleta de ropa
/palette maquillaje <user_id> <evento>  # Paleta de maquillaje
/palette accesorios <user_id> <evento>  # Paleta de accesorios
/palette quick <tipo> <evento>          # Paleta rápida sin perfil
```

### Citas Inspiracionales
```bash
/quotes get [categoría]      # Obtener cita inspiracional
/quotes tip                  # Consejo de belleza/bienestar
/quotes search <palabra>     # Buscar citas
/quotes wisdom               # Sabiduría diaria
```

### Gestión de Archivos
```bash
# Filesystem
/fs read <archivo>           # Leer archivo
/fs write <archivo> <texto>  # Escribir archivo
/fs list [directorio]        # Listar contenido

# Git (si está disponible)
/git init                    # Inicializar repositorio
/git add <archivo>           # Agregar al staging
/git commit "<mensaje>"      # Hacer commit
/git status                  # Ver estado
```

### Sistema
```bash
/help                        # Ayuda completa
/stats                       # Estadísticas de uso
/log                         # Ver log de interacciones
/context                     # Ver contexto actual
/clear                       # Limpiar contexto
/save                        # Guardar sesión
/quit                        # Salir
```

##  Ejemplos de Uso

### Crear Perfil Personal
```bash
Usuario: /beauty create_profile

Sistema:  CREACIÓN DE PERFIL DE BELLEZA
=========================================
 ID de usuario: maria_123
 Nombre completo: María García
 Tono de piel: 
  1. clara
  2. media  
  3. oscura
Selección: 2

[Continúa recopilando datos...]
```

### Generar Paleta de Ropa
```bash
Usuario: /palette ropa maria_123 trabajo

Sistema:  PREFERENCIAS PARA PALETA DE ROPA
Evento: Trabajo
 Estación del año:
  1. primavera
  2. verano
  3. otoño
  4. invierno
Selección: 2

[Genera paleta personalizada...]
```

### Conversación Natural
```bash
Usuario: ¿Qué colores me quedan bien para una entrevista de trabajo?

Claude: Para una entrevista de trabajo, te recomiendo colores que proyecten 
profesionalismo y confianza. ¿Tienes un perfil creado? Esto me ayudaría 
a darte recomendaciones más precisas basadas en tu tono de piel y 
características personales.

Para recomendaciones generales:
- Azul marino: transmite confianza y estabilidad
- Gris carbón: elegante y profesional
- Blanco o crema: limpio y sofisticado

¿Te gustaría crear un perfil personal con /beauty create_profile para 
obtener recomendaciones más específicas?
```

##  Desarrollo

### Estructura de Clases Principales

#### BeautyService
- `generate_advanced_palette()`: Generación de paletas con algoritmos avanzados
- `ColorTheoryEngine`: Motor de teoría del color
- `PaletteGenerator`: Generador específico por categoría

#### ClaudeService
- `send_message()`: Comunicación con Claude API
- `send_beauty_context_message()`: Mensajes con contexto de belleza
- `analyze_color_compatibility()`: Análisis de compatibilidad de colores

#### BeautyModel
- `BeautyProfile`: Dataclass para perfiles de usuario
- `ColorPalette`: Dataclass para paletas generadas
- Base de datos de colores y características

### Testing
```bash
# Ejecutar tests individuales
python src/models/beauty_model.py
python src/services/claude_service.py
python src/controllers/beauty_controller.py

# Tests con pytest (si está instalado)
pytest tests/
```

## 🌐 Servidor Remoto

El sistema se conecta a un servidor MCP remoto para citas inspiracionales:
- **Link**: https://web-production-de5ff.up.railway.app
- **Funcionalidad**: Citas, consejos de bienestar, sabiduría diaria
- **Fallback**: Si no está disponible, usa citas locales

## 📊 Monitoreo y Logs

### Tipos de Logs
- **Interacciones generales**: `logs/interactions.log`
- **Interacciones MCP**: `logs/mcp_interactions.json`
- **Sistema de belleza**: `logs/beauty_interactions.json`
- **Errores**: `logs/errors.log`

### Estadísticas Disponibles
- Número de perfiles creados
- Paletas generadas por tipo y evento
- Tasa de éxito de operaciones MCP
- Tiempo de sesión y mensajes procesados

##  Solución de Problemas

### Errores Comunes

**Error: ANTHROPIC_API_KEY no encontrada**
```bash
# Verifica que el archivo .env existe y contiene la API key
cat .env
# Debe mostrar: ANTHROPIC_API_KEY=tu_api_key_aqui
```

**Error: Servidor remoto no disponible**
```bash
# El sistema funciona en modo fallback con citas locales
# Verifica conexión a internet y estado del servidor con:
/quotes status
```

**Error: Git no disponible**
```bash
# Instala Git en tu sistema:
# Windows: https://git-scm.com/download/win
# macOS: brew install git
# Linux: apt-get install git
```

### Logging de Depuración
```bash
# Activar logging detallado
export LOG_LEVEL=DEBUG
python main.py

# Ver logs en tiempo real
tail -f logs/interactions.log
```
