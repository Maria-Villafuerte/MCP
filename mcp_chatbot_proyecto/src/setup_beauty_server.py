#!/usr/bin/env python3
"""
Setup del Beauty Palette MCP Server Local
Instalador automático y configurador
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Verificar versión de Python"""
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_dependencies():
    """Instalar dependencias necesarias"""
    print("\n📦 Instalando dependencias...")
    
    dependencies = [
        "mcp>=1.0.0",
        "asyncio",
        "typing-extensions"
    ]
    
    try:
        for dep in dependencies:
            print(f"   Instalando {dep}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", dep
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ Dependencias instaladas correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def create_startup_script():
    """Crear script de inicio"""
    startup_content = '''#!/usr/bin/env python3
"""
Startup script para Beauty Palette MCP Server Local
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    server_script = script_dir / "beauty_mcp_server_local.py"
    
    if not server_script.exists():
        print("❌ No se encuentra beauty_mcp_server_local.py")
        return
    
    print(" Iniciando Beauty Palette MCP Server Local...")
    
    try:
        subprocess.run([sys.executable, str(server_script)], check=True)
    except KeyboardInterrupt:
        print("\\n⏹️  Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando servidor: {e}")

if __name__ == "__main__":
    main()
'''
    
    with open("start_beauty_server.py", "w", encoding="utf-8") as f:
        f.write(startup_content)
    
    # Hacer ejecutable en sistemas Unix
    if os.name != 'nt':
        os.chmod("start_beauty_server.py", 0o755)
    
    print("✅ Script de inicio creado: start_beauty_server.py")

def create_client_example():
    """Crear ejemplo de cliente para probar el servidor"""
    client_content = '''#!/usr/bin/env python3
"""
Cliente de prueba para Beauty Palette MCP Server Local
"""

import asyncio
import subprocess
import json
import sys

class BeautyMCPClient:
    def __init__(self):
        self.server_process = None
        self.msg_id = 0
    
    async def start_server(self):
        """Iniciar servidor MCP"""
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "beauty_mcp_server_local.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Inicializar protocolo MCP
            init_msg = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "BeautyTestClient", "version": "1.0"}
                }
            }
            
            response = await self._send_request(init_msg)
            if response and "result" in response:
                # Enviar initialized notification
                await self._send_notification({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                })
                print("✅ Conectado al servidor MCP")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False
    
    def _next_id(self):
        self.msg_id += 1
        return self.msg_id
    
    async def _send_request(self, message):
        """Enviar request y obtener respuesta"""
        try:
            msg_str = json.dumps(message) + "\\n"
            self.server_process.stdin.write(msg_str)
            self.server_process.stdin.flush()
            
            response_line = self.server_process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            return None
        except Exception:
            return None
    
    async def _send_notification(self, message):
        """Enviar notificación"""
        try:
            msg_str = json.dumps(message) + "\\n"
            self.server_process.stdin.write(msg_str)
            self.server_process.stdin.flush()
        except Exception:
            pass
    
    async def call_tool(self, tool_name, arguments):
        """Llamar herramienta MCP"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await self._send_request(request)
        if response and "result" in response:
            content = response["result"]["content"]
            if content and len(content) > 0:
                return content[0]["text"]
        
        return "Sin respuesta"
    
    async def demo(self):
        """Ejecutar demo del sistema"""
        print(" Demo del Beauty Palette MCP Server")
        print("=" * 50)
        
        # Crear perfil de prueba
        print("\\n1. Creando perfil de prueba...")
        profile_result = await self.call_tool("create_beauty_profile", {
            "user_id": "demo_user",
            "name": "Usuario Demo",
            "skin_tone": "media",
            "undertone": "calido",
            "eye_color": "cafe",
            "hair_color": "castano",
            "style_preference": "moderno"
        })
        print(profile_result)
        
        # Generar paleta de ropa
        print("\\n2. Generando paleta de ropa para trabajo...")
        palette_result = await self.call_tool("generate_color_palette", {
            "user_id": "demo_user",
            "palette_type": "ropa",
            "event_type": "trabajo"
        })
        print(palette_result)
        
        # Obtener cita inspiracional
        print("\\n3. Obteniendo cita inspiracional...")
        quote_result = await self.call_tool("get_inspirational_quote", {
            "category": "confianza"
        })
        print(quote_result)
        
        # Listar perfiles
        print("\\n4. Listando perfiles...")
        list_result = await self.call_tool("list_beauty_profiles", {})
        print(list_result)
    
    def cleanup(self):
        """Limpiar recursos"""
        if self.server_process:
            self.server_process.terminate()

async def main():
    client = BeautyMCPClient()
    
    try:
        if await client.start_server():
            await client.demo()
        else:
            print("❌ No se pudo conectar al servidor")
    except KeyboardInterrupt:
        print("\\n⏹️  Demo interrumpido")
    finally:
        client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open("test_beauty_client.py", "w", encoding="utf-8") as f:
        f.write(client_content)
    
    print("✅ Cliente de prueba creado: test_beauty_client.py")

def create_readme():
    """Crear archivo README"""
    readme_content = '''# Beauty Palette MCP Server Local

Servidor MCP local especializado en paletas de colores y sistema de belleza personalizado.

##  Características

- **Perfiles Personalizados**: Crea perfiles basados en tono de piel, color de ojos, cabello y estilo
- **Paletas Inteligentes**: Genera paletas para ropa, maquillaje y accesorios
- **Análisis de Armonía**: Analiza la compatibilidad entre colores
- **Citas Inspiracionales**: Base de datos de citas de belleza y estilo
- **Protocolo MCP**: Compatible con clientes MCP estándar

##  Requisitos

- Python 3.8 o superior
- Biblioteca `mcp` instalada

##  Instalación

1. **Ejecutar el instalador:**
   ```bash
   python setup_beauty_server.py
   ```

2. **O instalar manualmente:**
   ```bash
   pip install mcp>=1.0.0
   ```

##  Uso

### Iniciar el Servidor

```bash
# Opción 1: Script de inicio
python start_beauty_server.py

# Opción 2: Directamente
python beauty_mcp_server_local.py
```

### Probar el Servidor

```bash
# Ejecutar cliente de prueba
python test_beauty_client.py
```

## 🛠️ Herramientas MCP Disponibles

### `create_beauty_profile`
Crear un perfil de belleza personalizado.

**Parámetros:**
- `user_id` (string): ID único del usuario
- `name` (string): Nombre completo
- `skin_tone` (enum): clara, media, oscura
- `undertone` (enum): frio, calido, neutro
- `eye_color` (enum): azul, verde, cafe, gris, negro
- `hair_color` (enum): rubio, castano, negro, rojo, gris
- `hair_type` (enum): liso, ondulado, rizado
- `style_preference` (enum): moderno, clasico, bohemio, minimalista, romantico, edgy

### `generate_color_palette`
Generar paleta de colores personalizada.

**Parámetros:**
- `user_id` (string): ID del usuario
- `palette_type` (enum): ropa, maquillaje, accesorios
- `event_type` (enum): casual, trabajo, formal, fiesta, cita
- `season` (enum): primavera, verano, otono, invierno

### `get_beauty_profile`
Obtener perfil de belleza existente.

### `list_beauty_profiles`
Listar todos los perfiles disponibles.

### `get_user_palette_history`
Ver historial de paletas de un usuario.

### `get_inspirational_quote`
Obtener cita inspiracional de belleza.

### `analyze_color_harmony`
Analizar armonía entre colores.

## 📝 Ejemplos

### Crear Perfil
```python
await call_tool("create_beauty_profile", {
    "user_id": "maria_123",
    "name": "María García",
    "skin_tone": "media",
    "undertone": "calido",
    "eye_color": "cafe",
    "hair_color": "castano",
    "style_preference": "moderno"
})
```

### Generar Paleta
```python
await call_tool("generate_color_palette", {
    "user_id": "maria_123",
    "palette_type": "ropa",
    "event_type": "trabajo"
})
```

## 🔧 Integración con Otros Sistemas

Este servidor MCP puede integrarse con:
- Clientes MCP estándar
- Sistemas de chat con Claude
- Aplicaciones de moda y belleza
- Sistemas de recomendación personalizados

##  Almacenamiento

- **Perfiles**: Almacenados en memoria durante la sesión
- **Paletas**: Historial en memoria por usuario
- **Persistencia**: Para uso productivo, considera implementar almacenamiento en archivo

## 🛡️ Limitaciones

- Almacenamiento en memoria (se pierde al reiniciar)
- Un servidor por instancia
- Análisis de color básico

## 🤝 Contribuciones

Para mejoras o nuevas características:
1. Agrega nuevos colores a la base de datos
2. Mejora los algoritmos de armonía
3. Implementa persistencia en archivo
4. Añade más tipos de eventos

## 📄 Licencia

MIT License - Uso libre para proyectos personales y comerciales.
'''
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ Documentación creada: README.md")

def main():
    """Función principal del setup"""
    print(" Beauty Palette MCP Server - Setup Local")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        return
    
    # Instalar dependencias
    if not install_dependencies():
        return
    
    # Crear archivos adicionales
    create_startup_script()
    create_client_example()
    create_readme()
    
    print("\n✅ Setup completado exitosamente!")
    print("\n Para iniciar el servidor:")
    print("   python start_beauty_server.py")
    print("\n🧪 Para probar el servidor:")
    print("   python test_beauty_client.py")
    print("\n📚 Consulta README.md para más información")

if __name__ == "__main__":
    main()