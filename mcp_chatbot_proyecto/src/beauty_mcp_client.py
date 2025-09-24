#!/usr/bin/env python3
"""
Cliente MCP para Beauty Palette Server Local
Se conecta al servidor MCP de belleza via stdio
"""

import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# Agregar src al path para imports de vistas (si existen)
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))
    try:
        from views.chat_view import ChatView
        from views.beauty_view import BeautyView
        VIEWS_AVAILABLE = True
    except ImportError:
        VIEWS_AVAILABLE = False
else:
    VIEWS_AVAILABLE = False

class BeautyMCPClient:
    def __init__(self, server_script: str = "beauty_mcp_server_local.py"):
        """Inicializar cliente MCP de belleza"""
        self.server_script = server_script
        self.session_id = f"beauty_client_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.server_process = None
        self.message_id = 0
        self.conversation_history = []
        
        # Usar vistas si están disponibles, sino usar versiones simples
        if VIEWS_AVAILABLE:
            self.chat_view = ChatView()
            self.beauty_view = BeautyView()
        else:
            self.chat_view = SimpleConsoleView()
            self.beauty_view = SimpleBeautyView()
    
    async def initialize(self) -> bool:
        """Inicializar conexión con servidor MCP de belleza"""
        try:
            # Verificar que el script del servidor existe
            if not Path(self.server_script).exists():
                print(f"❌ No se encuentra el servidor: {self.server_script}")
                return False
            
            # Iniciar proceso del servidor
            self.server_process = subprocess.Popen(
                [sys.executable, self.server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Inicializar conexión MCP
            if await self._initialize_mcp():
                print("✅ Conectado al Beauty Palette MCP Server")
                return True
            else:
                print("❌ Error inicializando protocolo MCP")
                return False
                
        except Exception as e:
            print(f"❌ Error conectando al servidor: {str(e)}")
            return False
    
    async def _initialize_mcp(self) -> bool:
        """Inicializar protocolo MCP con el servidor"""
        try:
            # Enviar mensaje de inicialización
            init_message = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "BeautyMCP-Client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self._send_mcp_request(init_message)
            
            if response and "result" in response:
                # Enviar notificación initialized
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                await self._send_mcp_notification(initialized_notification)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error en inicialización MCP: {e}")
            return False
    
    def _next_id(self) -> int:
        """Generar siguiente ID de mensaje"""
        self.message_id += 1
        return self.message_id
    
    async def _send_mcp_request(self, message: Dict) -> Optional[Dict]:
        """Enviar request MCP y obtener respuesta"""
        try:
            if not self.server_process:
                return None
            
            # Enviar mensaje
            message_str = json.dumps(message) + "\n"
            self.server_process.stdin.write(message_str)
            self.server_process.stdin.flush()
            
            # Leer respuesta
            response_line = self.server_process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            
            return None
            
        except Exception as e:
            print(f"Error enviando request MCP: {e}")
            return None
    
    async def _send_mcp_notification(self, message: Dict) -> None:
        """Enviar notificación MCP (sin respuesta esperada)"""
        try:
            if not self.server_process:
                return
            
            message_str = json.dumps(message) + "\n"
            self.server_process.stdin.write(message_str)
            self.server_process.stdin.flush()
            
        except Exception as e:
            print(f"Error enviando notification MCP: {e}")
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict) -> Optional[str]:
        """Llamar herramienta MCP del servidor de belleza"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await self._send_mcp_request(request)
            
            if response and "result" in response:
                content = response["result"]["content"]
                if content and len(content) > 0:
                    return content[0]["text"]
            
            return "No se recibió respuesta del servidor"
            
        except Exception as e:
            return f"Error llamando herramienta MCP: {str(e)}"
    
    async def run_interactive_mode(self):
        """Ejecutar modo interactivo conectado al servidor MCP de belleza"""
        # Mostrar mensaje de bienvenida
        self.show_welcome()
        
        while True:
            try:
                # Obtener entrada del usuario
                user_input = input("\n🎨 Beauty MCP > ").strip()
                
                # Procesar salida
                if user_input.lower() == '/quit':
                    break
                elif not user_input:
                    continue
                
                # Procesar comando o mensaje
                response = await self.process_user_input(user_input)
                
                # Mostrar respuesta
                if response:
                    print("\n" + response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error procesando entrada: {str(e)}")
        
        # Limpiar recursos
        await self.cleanup()
        print("\n👋 Cliente MCP desconectado. ¡Hasta pronto!")
    
    async def process_user_input(self, user_input: str) -> str:
        """Procesar entrada del usuario"""
        try:
            # Agregar al historial
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Verificar comandos especiales
            if user_input.startswith('/'):
                return await self.process_special_command(user_input)
            
            # Mensaje normal - intentar obtener cita inspiracional relacionada
            if any(word in user_input.lower() for word in ["belleza", "estilo", "moda", "color"]):
                quote = await self._call_mcp_tool("get_inspirational_quote", {"category": "estilo"})
                return f"💭 {quote}\n\n💡 Tip: Usa comandos como /beauty o /palette para funciones específicas"
            else:
                return "🎨 ¡Hola! Soy tu asistente de belleza MCP. Usa /help para ver comandos disponibles."
            
        except Exception as e:
            return f"❌ Error procesando mensaje: {str(e)}"
    
    async def process_special_command(self, command: str) -> str:
        """Procesar comandos especiales del sistema de belleza"""
        command_lower = command.lower().strip()
        
        # Comandos locales
        if command_lower == '/help':
            return self.get_help_message()
        elif command_lower == '/quit':
            return "👋 Cerrando cliente..."
        elif command_lower == '/context':
            return self._show_context_summary()
        elif command_lower == '/clear':
            self.conversation_history = []
            return "🧹 Contexto limpiado"
        elif command_lower == '/stats':
            return self._get_local_stats()
        
        # Comandos del servidor de belleza MCP
        elif command_lower.startswith('/beauty'):
            return await self.handle_beauty_command(command)
        elif command_lower.startswith('/palette'):
            return await self.handle_palette_command(command)
        elif command_lower.startswith('/quote'):
            return await self.handle_quote_command(command)
        elif command_lower.startswith('/harmony'):
            return await self.handle_harmony_command(command)
        else:
            return f"❌ Comando desconocido: {command}. Usa /help para ver comandos disponibles"
    
    async def handle_beauty_command(self, command: str) -> str:
        """Manejar comandos de belleza via MCP"""
        try:
            parts = command.strip().split()
            if len(parts) < 2:
                return self.get_beauty_help()
            
            action = parts[1].lower()
            
            if action == "help":
                return self.get_beauty_help()
            
            elif action == "create":
                return await self.create_profile_interactive()
            
            elif action == "list":
                return await self._call_mcp_tool("list_beauty_profiles", {})
            
            elif action == "profile":
                if len(parts) < 3:
                    return "❌ Especifica user_id. Uso: /beauty profile <user_id>"
                user_id = parts[2]
                return await self._call_mcp_tool("get_beauty_profile", {"user_id": user_id})
            
            elif action == "history":
                if len(parts) < 3:
                    return "❌ Especifica user_id. Uso: /beauty history <user_id>"
                user_id = parts[2]
                return await self._call_mcp_tool("get_user_palette_history", {"user_id": user_id})
            
            else:
                return f"❌ Acción no válida: {action}. Usa /beauty help"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def create_profile_interactive(self) -> str:
        """Crear perfil de forma interactiva usando MCP"""
        try:
            print("\n🎨 CREACIÓN DE PERFIL DE BELLEZA")
            print("=" * 50)
            
            # Recopilar datos del perfil
            user_id = input("👤 ID de usuario (único): ").strip()
            if not user_id:
                return "❌ ID de usuario es requerido"
                
            name = input("📝 Nombre completo: ").strip()
            if not name:
                return "❌ Nombre es requerido"
            
            # Características físicas
            print("\n🌈 CARACTERÍSTICAS FÍSICAS:")
            
            print("Tono de piel:")
            print("  1. clara")
            print("  2. media") 
            print("  3. oscura")
            skin_choice = input("Selección (1-3): ").strip()
            skin_tones = ["clara", "media", "oscura"]
            skin_tone = skin_tones[int(skin_choice)-1] if skin_choice.isdigit() and 1 <= int(skin_choice) <= 3 else "media"
            
            print("\nSubtono de piel:")
            print("  1. frio")
            print("  2. calido")
            print("  3. neutro")
            under_choice = input("Selección (1-3): ").strip()
            undertones = ["frio", "calido", "neutro"]
            undertone = undertones[int(under_choice)-1] if under_choice.isdigit() and 1 <= int(under_choice) <= 3 else "neutro"
            
            print("\nColor de ojos:")
            print("  1. azul")
            print("  2. verde") 
            print("  3. cafe")
            print("  4. gris")
            print("  5. negro")
            eye_choice = input("Selección (1-5): ").strip()
            eye_colors = ["azul", "verde", "cafe", "gris", "negro"]
            eye_color = eye_colors[int(eye_choice)-1] if eye_choice.isdigit() and 1 <= int(eye_choice) <= 5 else "cafe"
            
            print("\nColor de cabello:")
            print("  1. rubio")
            print("  2. castano")
            print("  3. negro")
            print("  4. rojo")
            print("  5. gris")
            hair_choice = input("Selección (1-5): ").strip()
            hair_colors = ["rubio", "castano", "negro", "rojo", "gris"]
            hair_color = hair_colors[int(hair_choice)-1] if hair_choice.isdigit() and 1 <= int(hair_choice) <= 5 else "castano"
            
            print("\nTipo de cabello:")
            print("  1. liso")
            print("  2. ondulado")
            print("  3. rizado")
            hair_type_choice = input("Selección (1-3): ").strip()
            hair_types = ["liso", "ondulado", "rizado"]
            hair_type = hair_types[int(hair_type_choice)-1] if hair_type_choice.isdigit() and 1 <= int(hair_type_choice) <= 3 else "liso"
            
            print("\nEstilo preferido:")
            print("  1. moderno")
            print("  2. clasico")
            print("  3. bohemio")
            print("  4. minimalista")
            print("  5. romantico")
            print("  6. edgy")
            style_choice = input("Selección (1-6): ").strip()
            styles = ["moderno", "clasico", "bohemio", "minimalista", "romantico", "edgy"]
            style_preference = styles[int(style_choice)-1] if style_choice.isdigit() and 1 <= int(style_choice) <= 6 else "moderno"
            
            # Crear perfil usando MCP
            profile_data = {
                "user_id": user_id,
                "name": name,
                "skin_tone": skin_tone,
                "undertone": undertone,
                "eye_color": eye_color,
                "hair_color": hair_color,
                "hair_type": hair_type,
                "style_preference": style_preference
            }
            
            response = await self._call_mcp_tool("create_beauty_profile", profile_data)
            
            return f"{response}\n\n💄 ¡Ahora puedes generar paletas con /palette!"
                
        except (KeyboardInterrupt, ValueError):
            return "❌ Creación de perfil cancelada"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_palette_command(self, command: str) -> str:
        """Manejar generación de paletas via MCP"""
        try:
            parts = command.strip().split()
            
            if len(parts) < 4:
                return """❌ Uso: /palette <tipo> <user_id> <evento>

TIPOS: ropa, maquillaje, accesorios
EVENTOS: casual, trabajo, formal, fiesta, cita

EJEMPLO: /palette ropa maria_123 trabajo"""
            
            palette_type = parts[1].lower()
            user_id = parts[2]
            event_type = parts[3].lower()
            
            if palette_type not in ["ropa", "maquillaje", "accesorios"]:
                return "❌ Tipo no válido. Opciones: ropa, maquillaje, accesorios"
            
            if event_type not in ["casual", "trabajo", "formal", "fiesta", "cita"]:
                return "❌ Evento no válido. Opciones: casual, trabajo, formal, fiesta, cita"
            
            print(f"🎨 Generando paleta {palette_type} para {event_type}...")
            
            # Llamar al servidor MCP
            response = await self._call_mcp_tool("generate_color_palette", {
                "user_id": user_id,
                "palette_type": palette_type,
                "event_type": event_type
            })
            
            return response or "❌ No se pudo generar la paleta"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_quote_command(self, command: str) -> str:
        """Manejar comandos de citas inspiracionales"""
        try:
            parts = command.strip().split()
            
            if len(parts) < 2:
                return "❌ Uso: /quote [categoria]"
            
            category = parts[1] if len(parts) > 1 else None
            
            if category and category not in ["confianza", "estilo", "elegancia", "cuidado", "autenticidad", "maquillaje"]:
                return "❌ Categoría no válida. Opciones: confianza, estilo, elegancia, cuidado, autenticidad, maquillaje"
            
            response = await self._call_mcp_tool("get_inspirational_quote", {"category": category} if category else {})
            
            return response or "❌ No se pudo obtener cita"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_harmony_command(self, command: str) -> str:
        """Manejar análisis de armonía de colores"""
        try:
            parts = command.strip().split()
            
            if len(parts) < 2:
                return """❌ Uso: /harmony <color1> [color2] [color3] ...

EJEMPLO: /harmony #FF6347 #4169E1 #32CD32

Los colores deben estar en formato hexadecimal (#RRGGBB)"""
            
            colors = parts[1:]
            
            # Validar formato hexadecimal
            for color in colors:
                if not color.startswith('#') or len(color) != 7:
                    return f"❌ Color inválido: {color}. Use formato #RRGGBB"
            
            if len(colors) < 2:
                return "❌ Se requieren al menos 2 colores para análisis"
            
            response = await self._call_mcp_tool("analyze_color_harmony", {"colors": colors})
            
            return response or "❌ No se pudo analizar armonía"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _show_context_summary(self) -> str:
        """Mostrar resumen del contexto local"""
        if not self.conversation_history:
            return "ℹ️ No hay mensajes en el contexto actual"
        
        summary = "\n📋 RESUMEN DEL CONTEXTO ACTUAL:\n"
        summary += "-" * 40 + "\n"
        
        recent_messages = self.conversation_history[-5:]
        for i, msg in enumerate(recent_messages, 1):
            role_icon = "👤" if msg["role"] == "user" else "🎨"
            content_preview = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
            summary += f"{i}. {role_icon} {content_preview}\n"
        
        total_messages = len(self.conversation_history)
        user_messages = len([m for m in self.conversation_history if m["role"] == "user"])
        
        summary += f"\n📊 Total: {total_messages} mensajes | Usuario: {user_messages}"
        
        return summary
    
    def _get_local_stats(self) -> str:
        """Obtener estadísticas locales"""
        total_messages = len(self.conversation_history)
        user_messages = len([m for m in self.conversation_history if m["role"] == "user"])
        
        return f"""📊 ESTADÍSTICAS DE SESIÓN:
💬 Total mensajes: {total_messages}
👤 Mensajes usuario: {user_messages}
🆔 ID de sesión: {self.session_id}
🔗 Servidor: {self.server_script}"""
    
    def get_help_message(self) -> str:
        """Mostrar mensaje de ayuda"""
        return """🎨 BEAUTY PALETTE MCP CLIENT - AYUDA

COMANDOS DE BELLEZA:
  /beauty help                 - Ayuda del sistema de belleza
  /beauty create               - Crear perfil personalizado
  /beauty list                 - Listar perfiles disponibles  
  /beauty profile <user_id>    - Ver perfil específico
  /beauty history <user_id>    - Ver historial de paletas

GENERACIÓN DE PALETAS:
  /palette <tipo> <user_id> <evento>
  
  Tipos: ropa, maquillaje, accesorios
  Eventos: casual, trabajo, formal, fiesta, cita
  
  Ejemplo: /palette ropa maria_123 trabajo

CITAS INSPIRACIONALES:
  /quote [categoria]           - Obtener cita inspiracional
  
  Categorías: confianza, estilo, elegancia, cuidado, autenticidad, maquillaje

ANÁLISIS DE COLORES:
  /harmony <color1> <color2>   - Analizar armonía de colores
  
  Ejemplo: /harmony #FF6347 #4169E1

COMANDOS DE SISTEMA:
  /help                        - Esta ayuda
  /stats                       - Estadísticas de sesión
  /context                     - Ver contexto actual
  /clear                       - Limpiar contexto
  /quit                        - Salir

FLUJO RECOMENDADO:
1. Crear perfil: /beauty create
2. Generar paleta: /palette ropa tu_id trabajo
3. Analizar colores: /harmony #color1 #color2
4. Obtener inspiración: /quote confianza"""
    
    def get_beauty_help(self) -> str:
        """Ayuda específica de belleza"""
        return """🎨 SISTEMA DE BELLEZA MCP

GESTIÓN DE PERFILES:
  /beauty create               - Crear perfil personalizado
  /beauty list                 - Ver todos los perfiles
  /beauty profile <user_id>    - Detalles de un perfil
  /beauty history <user_id>    - Historial de paletas

CARACTERÍSTICAS DE PERFIL:
  • Tono de piel: clara, media, oscura
  • Subtono: frío, cálido, neutro
  • Color de ojos: azul, verde, café, gris, negro
  • Color de cabello: rubio, castaño, negro, rojo, gris
  • Tipo de cabello: liso, ondulado, rizado
  • Estilo: moderno, clásico, bohemio, minimalista, romántico, edgy

TIPOS DE PALETAS:
  • Ropa: Combinaciones para vestir según el evento
  • Maquillaje: Colores para ojos, labios y mejillas
  • Accesorios: Joyería, bolsos y calzado coordinados

EVENTOS DISPONIBLES:
  • Casual: Uso diario relajado
  • Trabajo: Look profesional
  • Formal: Eventos elegantes
  • Fiesta: Para destacar y brillar
  • Cita: Romántico y favorecedor

EJEMPLO COMPLETO:
1. /beauty create (crear perfil "ana_123")
2. /palette maquillaje ana_123 cita
3. /harmony #FF69B4 #DC143C (analizar colores de la paleta)
4. /quote confianza (inspiración final)"""
    
    def show_welcome(self):
        """Mostrar mensaje de bienvenida"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                Beauty Palette MCP Client                     ║
║            🎨 Tu Asistente Personal de Belleza 🎨            ║
╠══════════════════════════════════════════════════════════════╣
║  ✨ Perfiles Personalizados de Belleza                       ║
║  🌈 Generación Inteligente de Paletas                        ║
║  💄 Recomendaciones de Maquillaje                            ║
║  👗 Coordinación de Ropa y Accesorios                        ║
║  🎯 Análisis de Armonía de Colores                           ║
║  💭 Citas Inspiracionales de Belleza                         ║
╚══════════════════════════════════════════════════════════════╝

🚀 Conectado al Beauty Palette MCP Server Local
📋 Usa /help para ver todos los comandos disponibles
🎨 ¡Comienza creando tu perfil con /beauty create!
"""
        print(banner)
    
    async def cleanup(self):
        """Limpiar recursos del cliente"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            except Exception:
                pass
        
        print("🧹 Cliente MCP desconectado")

# Clases simples para cuando las vistas no están disponibles
class SimpleConsoleView:
    def show_welcome_message(self):
        print("🎨 Beauty MCP Client - Bienvenido")
    
    def get_user_input(self):
        return input("\n> ").strip()
    
    def show_response(self, response):
        print(f"\n{response}")
    
    def show_error(self, error):
        print(f"\n❌ {error}")
    
    def show_goodbye(self):
        print("\n👋 ¡Hasta pronto!")

class SimpleBeautyView:
    def show_beauty_help(self):
        return "🎨 Sistema de Belleza - Usa /beauty help para más información"
    
    def collect_profile_data(self):
        # Implementación simple si no hay vista avanzada
        return None

async def main():
    """Función principal del cliente MCP de belleza"""
    print("🎨 Iniciando Beauty Palette MCP Client...")
    
    try:
        # Inicializar cliente MCP
        client = BeautyMCPClient()
        
        if await client.initialize():
            await client.run_interactive_mode()
        else:
            print("\n❌ No se pudo conectar al servidor MCP")
            print("💡 Asegúrate de que beauty_mcp_server_local.py esté disponible")
            
    except KeyboardInterrupt:
        print("\n👋 Cliente interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())