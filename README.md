# 🌟 Sistema MCP Completo - Proyecto Redes CC3067

**Universidad del Valle de Guatemala - Proyecto 1**  
*Sistema completo de chatbots MCP con análisis de belleza, sueño y videojuegos*

## 🎯 Descripción General

Este proyecto implementa un sistema completo de chatbots usando **Model Context Protocol (MCP)** con múltiples servidores especializados. El sistema incluye análisis de belleza y colorimetría profesional, coaching de sueño, análisis de videojuegos, y manejo de archivos/Git.

## 🏗️ Arquitectura del Sistema

```
MCP Sistema/
├── 📱 Clientes/                    # Diferentes interfaces de usuario
│   ├── beauty_client.py           # Cliente especializado en belleza
│   ├── Cliente_universal.py       # Cliente para múltiples servidores  
│   └── beauty_client_hybrid.py    # Cliente local + remoto
├── 🖥️ Servidores/
│   ├── Local/                     # Servidores propios
│   │   ├── beauty_server.py       # Análisis de belleza y colorimetría
│   │   └── metodos_server.py      # Motor de colorimetría avanzado
│   ├── Externos/                  # Servidores de compañeros
│   │   ├── Fabi/                  # Sleep Coaching Server
│   │   └── JP/                    # Game Analysis Server
│   ├── Remoto/                    # Servidor deployed en Railway
│   └── GitHub&files/              # Manejo de archivos y Git
└── 📊 Data/                       # Almacenamiento de datos
```

## 🚀 Funcionalidades Principales

### 💄 **Beauty & Color Analysis Server**
- **Análisis colorimétrico científico** basado en 8 estaciones de color
- **Determinación de subtono** usando múltiples indicadores físicos
- **Generación de paletas personalizadas** para ropa, maquillaje y accesorios
- **Sistema de perfiles completos** con recomendaciones profesionales

### 😴 **Sleep Coaching Server** 
- **Análisis de patrones de sueño** personalizados
- **Recomendaciones basadas en cronotipos** (alondra, búho, intermedio)
- **Creación de rutinas de sueño** optimizadas
- **Seguimiento y consejos rápidos** de higiene del sueño

### 🎮 **Game Analysis Server**
- **Análisis completo de videojuegos** con datos de ventas
- **Rankings por género, plataforma y región**
- **Estadísticas de publishers** y tendencias del mercado
- **Búsqueda avanzada** con múltiples filtros

### 📁 **File & Git Management**
- **Operaciones completas de archivos** (crear, leer, modificar, buscar)
- **Control de versiones Git** integrado
- **Manejo seguro de repositorios** locales y remotos

## 🔧 Instalación y Configuración

### Prerrequisitos
```bash
# Python 3.8+
# Git instalado
# Conexión a internet (para servidor remoto)
```

### Instalación
```bash
# 1. Clonar el repositorio
git clone https://github.com/Maria-Villafuerte/MCP.git 
cd MCP

# 2. Crear entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API Key
# Crear archivo .env en la raíz:
echo "ANTHROPIC_API_KEY=tu_api_key_aqui" > .env
```

## 🎮 Guías de Uso

### 🌸 **Para Análisis de Belleza Personal**
```bash
# Usar el cliente especializado en belleza
python Clientes/beauty_client.py
```

**Comandos principales:**
- `"crear perfil"` - Análisis colorimétrico completo
- `"generar paleta de maquillaje"` - Paletas personalizadas
- `"paleta para trabajo"` - Colores profesionales
- `"mostrar mi perfil"` - Ver análisis completo

### 🌐 **Para Usar Múltiples Servidores**
```bash
# Cliente universal (belleza + sueño + videojuegos)
python Clientes/Cliente_universal.py
```

**Ejemplos de comandos:**
- `"crear perfil de belleza con ojos verdes y piel clara"`
- `"necesito consejos para dormir mejor"`
- `"cuáles son los mejores juegos de RPG"`
- `"crear rutina de sueño para despertar a las 6 AM"`

### ☁️ **Para Servidor Remoto**
```bash
# Cliente híbrido (local + Railway)
python Clientes/beauty_client_hybrid.py
```

### 📁 **Para Archivos y Git**
```bash
# Cliente de archivos y Git
cd Servidores/GitHub&files/
python chat_simple.py
```

**Comandos Git:**
- `"inicializar repositorio git"`
- `"crear archivo README.md"`
- `"hacer commit con mensaje 'inicial'"`
- `"subir cambios a GitHub"`

## 💡 Ejemplos de Conversaciones

### 🎨 **Sesión de Análisis de Belleza**
```
Usuario: Quiero crear mi perfil de belleza
Sistema: ¡Perfecto! Para crear tu análisis colorimétrico necesito algunos datos...

Usuario: Soy María, piel media, venas azules, prefiero joyería de plata
Sistema: ✅ Creando perfil... Tu análisis indica:
- Subtono: FRÍO (85% confianza)
- Estación: Verano Frío
- Colores recomendados: Azules, rosas, morados...

Usuario: Genera paleta de maquillaje para una boda
Sistema: 🎨 Paleta "Elegancia de Verano":
- Ojos: Azul real + Lavanda suave
- Labios: Rosa frambuesa
- Técnica: Maquillaje con difuminado natural...
```


## 🌐 Servidor Remoto

**URL del servidor desplegado:** https://beauty-pallet-server.railway.app

**Endpoints disponibles:**
- `GET /` - Página principal
- `GET /health` - Estado del servidor
- `POST /mcp/create-profile` - Crear perfil MCP
- `POST /api/generate-palette` - Generar paletas
- `GET /docs` - Documentación Swagger

## 📊 Especificaciones Técnicas

### **Beauty Server (Propio)**
- **Análisis científico** de subtono con 4 indicadores
- **8 estaciones de color** (Primavera Cálida/Clara, Verano Suave/Frío, etc.)
- **Teoría de armonías cromáticas** para paletas optimizadas
- **Almacenamiento JSON** con historial completo

### **Sleep Coach Server (Fabi)**
- **Algoritmo de cronotipos** para personalización
- **Análisis de patrones** con recomendaciones científicas
- **Rutinas semanales** optimizadas por perfil
- **Base de conocimientos** de higiene del sueño

### **Game Server (JP)**
- **Dataset de +16,000 videojuegos** con análisis pandas
- **Múltiples filtros** (género, plataforma, año, región)
- **Rankings dinámicos** de publishers y ventas
- **API RESTful** para consultas complejas

## 📈 Logs y Monitoreo

Todos los clientes generan logs detallados:
- `Data/beauty_log.txt` - Interacciones de belleza
- `Data/universal_log.txt` - Cliente universal
- `Data/beauty_context.json` - Contexto y memoria

