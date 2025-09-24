#!/usr/bin/env python3
"""
Cliente MCP que se conecta al servidor local via stdio
"""

import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# Agregar src al path para imports de vistas
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from views.chat_view import ChatView
from views.beauty_view import BeautyView

class MCPClient:
    def __init__(self, server_script: str = "beauty_server_local.py"):
        """Inicializar cliente MCP"""
        self.server_script = server_script
        self.session_id = f"client_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.chat_view = ChatView()
        self.beauty_view = BeautyView()
        self.server_process = None
        self.message_id = 0
        self.conversation_history = []
    
    async def initialize(self) -> bool:
        """Inicializar conexión con servidor MCP"""
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
                print("✅ Conectado al servidor MCP local")
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
                        "name": "MCPChatbot-Client",
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
        """Llamar herramienta MCP"""
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
        """Ejecutar modo interactivo conectado al servidor MCP"""
        # Mostrar mensaje de bienvenida
        self.chat_view.show_welcome_message()
        print(f"🔗 Conectado a servidor MCP: {self.server_script}")
        print(f"🆔 ID de sesión: {self.session_id}\n")
        
        while True:
            try:
                # Obtener entrada del usuario
                user_input = self.chat_view.get_user_input()
                
                # Procesar salida
                if user_input.lower() == '/quit':
                    break
                elif not user_input.strip():
                    continue
                
                # Procesar comando o mensaje
                response = await self.process_user_input(user_input)
                
                # Mostrar respuesta
                if response:
                    self.chat_view.show_response(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.chat_view.show_error(f"Error procesando entrada: {str(e)}")
        
        # Limpiar recursos
        await self.cleanup()
        self.chat_view.show_goodbye()
    
    async def process_user_input(self, user_input: str) -> str:
        """Procesar entrada del usuario"""
        try:
            # Agregar al historial
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Verificar comandos especiales
            if user_input.startswith('/'):
                return await self.process_special_command(user_input)
            
            # Procesar mensaje normal con Claude via MCP
            response = await self._call_mcp_tool("chat", {"message": user_input})
            
            if response:
                self.conversation_history.append({"role": "assistant", "content": response})
            
            return response or "No se pudo obtener respuesta"
            
        except Exception as e:
            return f"❌ Error procesando mensaje: {str(e)}"
    
    async def process_special_command(self, command: str) -> str:
        """Procesar comandos especiales"""
        command_lower = command.lower().strip()
        
        # Comandos locales (no requieren servidor)
        if command_lower == '/help':
            return self.chat_view.get_help_message()
        elif command_lower == '/quit':
            return "👋 Cerrando cliente..."
        elif command_lower == '/context':
            return self._show_context_summary()
        elif command_lower == '/clear':
            self.conversation_history = []
            return "🧹 Contexto limpiado"
        
        # Comandos que requieren servidor MCP
        elif command_lower.startswith('/beauty') or command_lower.startswith('/palette'):
            return await self.handle_beauty_command(command)
        elif command_lower.startswith('/quotes'):
            return await self.handle_quotes_command(command)
        elif command_lower.startswith('/git') or command_lower.startswith('/fs'):
            return await self.handle_git_command(command)
        elif command_lower == '/stats':
            return self._get_local_stats()
        else:
            return f"❌ Comando desconocido: {command}. Usa /help para ver comandos disponibles"
    
    def _show_context_summary(self) -> str:
        """Mostrar resumen del contexto local"""
        if not self.conversation_history:
            return "ℹ️ No hay mensajes en el contexto actual"
        
        summary = "\n📋 RESUMEN DEL CONTEXTO ACTUAL:\n"
        summary += "-" * 40 + "\n"
        
        # Mostrar últimos 5 mensajes
        recent_messages = self.conversation_history[-5:]
        for i, msg in enumerate(recent_messages, 1):
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            content_preview = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
            summary += f"{i}. {role_icon} {content_preview}\n"
        
        total_messages = len(self.conversation_history)
        user_messages = len([m for m in self.conversation_history if m["role"] == "user"])
        assistant_messages = len([m for m in self.conversation_history if m["role"] == "assistant"])
        
        summary += f"\n📊 Total: {total_messages} mensajes | Usuario: {user_messages} | Asistente: {assistant_messages}"
        
        return summary
    
    def _get_local_stats(self) -> str:
        """Obtener estadísticas locales"""
        total_messages = len(self.conversation_history)
        user_messages = len([m for m in self.conversation_history if m["role"] == "user"])
        assistant_messages = len([m for m in self.conversation_history if m["role"] == "assistant"])
        
        return f"""📊 ESTADÍSTICAS DE SESIÓN:
💬 Total mensajes: {total_messages}
👤 Mensajes usuario: {user_messages}  
🤖 Mensajes asistente: {assistant_messages}
🆔 ID de sesión: {self.session_id}
🔗 Servidor: {self.server_script}"""
    
    async def handle_beauty_command(self, command: str) -> str:
        """Manejar comandos de belleza via MCP"""
        try:
            parts = command.strip().split()
            if len(parts) < 2:
                return self.beauty_view.show_beauty_help()
            
            action = parts[1].lower()
            
            if action == "help":
                return self.beauty_view.show_beauty_help()
            
            elif action == "create_profile":
                return await self.create_profile_interactive()
            
            elif action == "list_profiles":
                # Usar git_command para ejecutar comando beauty
                return await self._call_mcp_tool("git_command", {"command": "/beauty list_profiles"})
            
            elif action == "profile":
                if len(parts) < 3:
                    return "❌ Especifica user_id. Uso: /beauty profile <user_id>"
                
                full_command = " ".join(parts)
                return await self._call_mcp_tool("git_command", {"command": full_command})
            
            elif action == "history":
                if len(parts) < 3:
                    return "❌ Especifica user_id. Uso: /beauty history <user_id>"
                
                full_command = " ".join(parts)
                return await self._call_mcp_tool("git_command", {"command": full_command})
            
            # Comandos de paleta
            elif command.startswith("/palette"):
                return await self.handle_palette_command(command)
            
            else:
                # Pasar comando completo al servidor
                return await self._call_mcp_tool("git_command", {"command": command})
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def create_profile_interactive(self) -> str:
        """Crear perfil de forma interactiva usando MCP"""
        try:
            # Recopilar datos usando la vista existente
            profile_data = self.beauty_view.collect_profile_data()
            
            if not profile_data:
                return "ℹ️ Creación de perfil cancelada"
            
            # Usar la herramienta MCP create_profile
            response = await self._call_mcp_tool("create_profile", profile_data)
            
            if response and "creado" in response.lower():
                return f"✅ {response}\n\n💄 Ahora puedes generar paletas con /palette"
            else:
                return f"❌ Error creando perfil: {response}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_palette_command(self, command: str) -> str:
        """Manejar generación de paletas via MCP"""
        try:
            parts = command.strip().split()
            
            if len(parts) < 4:
                return "❌ Uso: /palette <tipo> <user_id> <evento>\nTipos: ropa, maquillaje, accesorios"
            
            palette_type = parts[1].lower()
            user_id = parts[2]
            event_type = parts[3] if len(parts) > 3 else "casual"
            
            if palette_type not in ["ropa", "maquillaje", "accesorios"]:
                return "❌ Tipo no válido. Opciones: ropa, maquillaje, accesorios"
            
            # Recopilar preferencias adicionales
            self.chat_view.show_info(f"Generando paleta {palette_type} para {event_type}...")
            preferences = self.beauty_view.collect_palette_preferences(palette_type, event_type)
            
            # Construir comando completo
            full_command = f"/palette {palette_type} {user_id} {event_type}"
            
            # Usar git_command para ejecutar el comando de paleta
            response = await self._call_mcp_tool("git_command", {"command": full_command})
            
            return response or "❌ No se pudo generar la paleta"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_quotes_command(self, command: str) -> str:
        """Manejar comandos de citas via MCP"""
        try:
            parts = command.strip().split()
            if len(parts) < 2:
                return "❌ Uso: /quotes <acción> [parámetros]"
            
            action = parts[1].lower()
            
            if action == "get":
                category = parts[2] if len(parts) > 2 else None
                return await self._call_mcp_tool("get_quote", {"category": category} if category else {})
            
            elif action == "search":
                if len(parts) < 3:
                    return "❌ Uso: /quotes search <término>"
                
                # Usar git_command para comandos complejos
                return await self._call_mcp_tool("git_command", {"command": command})
            
            elif action == "wisdom":
                return await self._call_mcp_tool("git_command", {"command": "/quotes wisdom"})
            
            elif action == "help":
                return """SISTEMA DE CITAS INSPIRACIONALES

COMANDOS DISPONIBLES:
  /quotes help                 - Mostrar esta ayuda
  /quotes get [categoría]      - Obtener cita inspiracional
  /quotes search <palabra>     - Buscar citas por palabra clave
  /quotes wisdom               - Obtener sabiduría diaria

CATEGORÍAS DISPONIBLES:
  motivacion, belleza, confianza, éxito, amor, vida, inspiracion

EJEMPLOS DE USO:
  /quotes get motivacion
  /quotes search belleza
  /quotes wisdom"""
            
            else:
                return "❌ Acciones disponibles: get, search, wisdom, help"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_git_command(self, command: str) -> str:
        """Manejar comandos de git/filesystem via MCP"""
        try:
            return await self._call_mcp_tool("git_command", {"command": command})
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
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

def show_banner():
    """Mostrar banner del cliente MCP"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                     MCPChatbot Cliente                       ║
║              Conectando a Servidor MCP Local                 ║
╠══════════════════════════════════════════════════════════════╣
║  🔗 Protocolo MCP via stdio                                  ║
║  🤖 Claude API via Servidor MCP                              ║
║  💄 Sistema de Belleza Remoto                                ║
║  🌟 Citas Inspiracionales                                    ║
║  📁 Gestión de Archivos                                      ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

async def main():
    """Función principal del cliente MCP"""
    show_banner()
    
    try:
        # Inicializar cliente MCP
        client = MCPClient()
        
        if await client.initialize():
            await client.run_interactive_mode()
        else:
            print("\n❌ No se pudo conectar al servidor MCP")
            print("💡 Asegúrate de que server_local.py esté disponible")
            
    except KeyboardInterrupt:
        print("\n👋 Cliente interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())