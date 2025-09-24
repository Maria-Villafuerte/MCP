#!/usr/bin/env python3
"""
Cliente MCP Multi-Servidor
Se conecta a múltiples servidores MCP: Beauty, Movies y Sleep Coach
"""

import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, List

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

class MCPServerConnection:
    """Conexión a un servidor MCP específico"""
    def __init__(self, name: str, script: str, display_name: str):
        self.name = name
        self.script = script
        self.display_name = display_name
        self.process = None
        self.msg_id = 0
        self.active = False
    
    async def start(self) -> bool:
        """Iniciar servidor MCP"""
        if not Path(self.script).exists():
            print(f"❌ No se encuentra: {self.script}")
            return False
        
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.script],
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
                    "clientInfo": {"name": "MultiMCPClient", "version": "1.0"}
                }
            }
            
            response = await self.send_request(init_msg)
            if response and "result" in response:
                # Enviar initialized notification
                await self.send_notification({
                    "jsonrpc": "2.0", 
                    "method": "notifications/initialized"
                })
                self.active = True
                return True
            
            return False
            
        except Exception as e:
            print(f"Error iniciando {self.display_name}: {e}")
            return False
    
    def _next_id(self) -> int:
        self.msg_id += 1
        return self.msg_id
    
    async def send_request(self, message: Dict) -> Optional[Dict]:
        """Enviar request y esperar respuesta"""
        try:
            if not self.process:
                return None
            
            msg_str = json.dumps(message) + "\n"
            self.process.stdin.write(msg_str)
            self.process.stdin.flush()
            
            response_line = self.process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            return None
            
        except Exception:
            return None
    
    async def send_notification(self, message: Dict) -> None:
        """Enviar notificación"""
        try:
            if self.process:
                msg_str = json.dumps(message) + "\n"
                self.process.stdin.write(msg_str)
                self.process.stdin.flush()
        except Exception:
            pass
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Optional[str]:
        """Llamar herramienta MCP"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }
        
        response = await self.send_request(request)
        if response and "result" in response:
            content = response["result"]["content"]
            if content and len(content) > 0:
                return content[0]["text"]
        
        return "Sin respuesta del servidor"
    
    def stop(self):
        """Detener servidor"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                self.process.kill()
            self.process = None
        self.active = False

class MultiMCPClient:
    def __init__(self):
        """Inicializar cliente multi-MCP"""
        self.session_id = f"multi_client_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history = []
        
        # Configurar servidores MCP disponibles
        self.servers = {
            'beauty': MCPServerConnection(
                'beauty', 
                'beauty_mcp_server_local.py', 
                'Beauty Palette Server'
            ),
            'movies': MCPServerConnection(
                'movies', 
                'movie_server.py', 
                'Movies Server'
            ),
            'sleep': MCPServerConnection(
                'sleep', 
                'sleep_coach.py', 
                'Sleep Coach Server'
            )
        }
        
        # Usar vistas si están disponibles
        if VIEWS_AVAILABLE:
            self.chat_view = ChatView()
            self.beauty_view = BeautyView()
        else:
            self.chat_view = SimpleConsoleView()
            self.beauty_view = SimpleBeautyView()
    
    async def start(self) -> bool:
        """Iniciar todos los servidores MCP disponibles"""
        print(" Iniciando servidores MCP...")
        
        results = {}
        for name, server in self.servers.items():
            print(f"   Conectando a {server.display_name}...")
            results[name] = await server.start()
            status = "✅" if results[name] else "❌"
            print(f"   {server.display_name}: {status}")
        
        connected = sum(1 for r in results.values() if r)
        print(f"\n {connected}/{len(self.servers)} servidores conectados")
        
        return connected > 0  # Al menos un servidor debe funcionar
    
    async def run(self):
        """Ejecutar cliente interactivo"""
        self.show_welcome()
        self.show_server_status()
        
        while True:
            try:
                user_input = input("\n Multi MCP > ").strip()
                
                if user_input.lower() == '/quit':
                    break
                elif not user_input:
                    continue
                
                response = await self.process_input(user_input)
                if response:
                    print(f"\n{response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        await self.cleanup()
        print("\n Cliente multi-MCP desconectado. ¡Hasta pronto!")
    
    async def process_input(self, user_input: str) -> Optional[str]:
        """Procesar entrada del usuario"""
        self.conversation_history.append({"role": "user", "content": user_input})
        
        if user_input.startswith('/'):
            return await self.handle_command(user_input)
        else:
            # Mensaje normal - mostrar ayuda
            return self.get_quick_help()
    
    async def handle_command(self, command: str) -> str:
        """Manejar comandos del sistema"""
        parts = command.strip().split()
        if len(parts) < 1:
            return self.get_help_message()
        
        cmd = parts[0].lower()
        
        # Comandos del sistema
        if cmd == '/help':
            return self.get_help_message()
        elif cmd == '/status':
            self.show_server_status()
            return None
        elif cmd == '/clear':
            self.conversation_history = []
            return " Historial limpiado"
        elif cmd == '/stats':
            return self.get_session_stats()
        
        # Comandos de Beauty Palette Server
        elif cmd == '/beauty':
            return await self.handle_beauty_command(command)
        elif cmd == '/palette':
            return await self.handle_palette_command(command)
        elif cmd == '/quote':
            return await self.handle_quote_command(command)
        elif cmd == '/harmony':
            return await self.handle_harmony_command(command)
        
        # Comandos de Movies Server
        elif cmd == '/movie':
            return await self.handle_movie_command(command)
        
        # Comandos de Sleep Coach Server
        elif cmd == '/sleep':
            return await self.handle_sleep_command(command)
        
        else:
            return f"❌ Comando desconocido: {cmd}. Usa /help para ver comandos disponibles"
    
    # === COMANDOS DE BEAUTY PALETTE SERVER ===
    
    async def handle_beauty_command(self, command: str) -> str:
        """Manejar comandos de belleza"""
        if not self.servers['beauty'].active:
            return "❌ Beauty Server no disponible"
        
        parts = command.strip().split()
        if len(parts) < 2:
            return self.get_beauty_help()
        
        action = parts[1].lower()
        
        try:
            if action == "help":
                return self.get_beauty_help()
            elif action == "create":
                return await self.create_beauty_profile()
            elif action == "list":
                return await self.servers['beauty'].call_tool("list_beauty_profiles", {})
            elif action == "profile":
                if len(parts) < 3:
                    return "❌ Uso: /beauty profile <user_id>"
                return await self.servers['beauty'].call_tool("get_beauty_profile", {"user_id": parts[2]})
            elif action == "history":
                if len(parts) < 3:
                    return "❌ Uso: /beauty history <user_id>"
                return await self.servers['beauty'].call_tool("get_user_palette_history", {"user_id": parts[2]})
            else:
                return f"❌ Acción no válida: {action}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_palette_command(self, command: str) -> str:
        """Generar paleta de colores"""
        if not self.servers['beauty'].active:
            return "❌ Beauty Server no disponible"
        
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
        
        try:
            return await self.servers['beauty'].call_tool("generate_color_palette", {
                "user_id": user_id,
                "palette_type": palette_type,
                "event_type": event_type
            })
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_quote_command(self, command: str) -> str:
        """Obtener cita inspiracional"""
        if not self.servers['beauty'].active:
            return "❌ Beauty Server no disponible"
        
        parts = command.strip().split()
        category = parts[1] if len(parts) > 1 else None
        
        try:
            return await self.servers['beauty'].call_tool("get_inspirational_quote", 
                {"category": category} if category else {})
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_harmony_command(self, command: str) -> str:
        """Analizar armonía de colores"""
        if not self.servers['beauty'].active:
            return "❌ Beauty Server no disponible"
        
        parts = command.strip().split()
        if len(parts) < 2:
            return """❌ Uso: /harmony <color1> [color2] [color3] ...

EJEMPLO: /harmony #FF6347 #4169E1 #32CD32"""
        
        colors = parts[1:]
        
        # Validar formato hexadecimal
        for color in colors:
            if not color.startswith('#') or len(color) != 7:
                return f"❌ Color inválido: {color}. Use formato #RRGGBB"
        
        try:
            return await self.servers['beauty'].call_tool("analyze_color_harmony", {"colors": colors})
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    # === COMANDOS DE MOVIES SERVER ===
    
    async def handle_movie_command(self, command: str) -> str:
        """Manejar comandos de películas"""
        if not self.servers['movies'].active:
            return "❌ Movies Server no disponible"
        
        parts = command.strip().split()
        if len(parts) < 2:
            return self.get_movies_help()
        
        action = parts[1].lower()
        
        try:
            if action == "help":
                return self.get_movies_help()
            
            elif action == "search":
                if len(parts) < 3:
                    return "❌ Uso: /movie search <título>"
                query = ' '.join(parts[2:])
                return await self.servers['movies'].call_tool("search_movie", {
                    "query": query, "limit": 10
                })
            
            elif action == "details":
                if len(parts) < 3:
                    return "❌ Uso: /movie details <título>"
                title = ' '.join(parts[2:])
                return await self.servers['movies'].call_tool("movie_details", {"title": title})
            
            elif action == "actor":
                if len(parts) < 3:
                    return "❌ Uso: /movie actor <nombre>"
                actor = ' '.join(parts[2:])
                return await self.servers['movies'].call_tool("top_movies_by_actor_tool", {
                    "actor": actor, "limit": 10
                })
            
            elif action == "similar":
                if len(parts) < 3:
                    return "❌ Uso: /movie similar <título>"
                title = ' '.join(parts[2:])
                return await self.servers['movies'].call_tool("similar_movies_tool", {
                    "title": title, "limit": 10
                })
            
            elif action == "recommend":
                return await self.servers['movies'].call_tool("recommend_movies_tool", {
                    "genres": None, "min_vote": 0.0, "limit": 15
                })
            
            elif action == "playlist":
                target_minutes = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 480
                return await self.servers['movies'].call_tool("build_playlist_tool", {
                    "target_minutes": target_minutes, "prefer_high_rating": True
                })
            
            else:
                return f"❌ Acción no válida: {action}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    # === COMANDOS DE SLEEP COACH SERVER ===
    
    async def handle_sleep_command(self, command: str) -> str:
        """Manejar comandos de sleep coach"""
        if not self.servers['sleep'].active:
            return "❌ Sleep Coach Server no disponible"
        
        parts = command.strip().split()
        if len(parts) < 2:
            return self.get_sleep_help()
        
        action = parts[1].lower()
        
        try:
            if action == "help":
                return self.get_sleep_help()
            
            elif action == "profile":
                return await self.create_sleep_profile()
            
            elif action == "analyze":
                if len(parts) < 3:
                    return "❌ Uso: /sleep analyze <user_id>"
                return await self.servers['sleep'].call_tool("analyze_sleep_pattern", {"user_id": parts[2]})
            
            elif action == "recommend":
                if len(parts) < 3:
                    return "❌ Uso: /sleep recommend <user_id>"
                return await self.servers['sleep'].call_tool("get_personalized_recommendations", {"user_id": parts[2]})
            
            elif action == "schedule":
                if len(parts) < 3:
                    return "❌ Uso: /sleep schedule <user_id>"
                return await self.servers['sleep'].call_tool("create_weekly_schedule", {"user_id": parts[2]})
            
            elif action == "advice":
                if len(parts) < 3:
                    return "❌ Uso: /sleep advice <consulta>"
                query = ' '.join(parts[2:])
                return await self.servers['sleep'].call_tool("quick_sleep_advice", {"query": query})
            
            else:
                return f"❌ Acción no válida: {action}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    # === FUNCIONES INTERACTIVAS ===
    
    async def create_beauty_profile(self) -> str:
        """Crear perfil de belleza interactivo"""
        print("\n CREACIÓN DE PERFIL DE BELLEZA")
        print("=" * 50)
        
        try:
            user_id = input("👤 ID de usuario: ").strip()
            if not user_id: return "❌ ID requerido"
            
            name = input("📝 Nombre completo: ").strip()
            if not name: return "❌ Nombre requerido"
            
            # Características físicas con menús
            skin_tone = self.select_option("Tono de piel", ["clara", "media", "oscura"])
            undertone = self.select_option("Subtono", ["frio", "calido", "neutro"])
            eye_color = self.select_option("Color de ojos", ["azul", "verde", "cafe", "gris", "negro"])
            hair_color = self.select_option("Color de cabello", ["rubio", "castano", "negro", "rojo", "gris"])
            hair_type = self.select_option("Tipo de cabello", ["liso", "ondulado", "rizado"])
            style_preference = self.select_option("Estilo preferido", 
                ["moderno", "clasico", "bohemio", "minimalista", "romantico", "edgy"])
            
            profile_data = {
                "user_id": user_id, "name": name, "skin_tone": skin_tone,
                "undertone": undertone, "eye_color": eye_color, "hair_color": hair_color,
                "hair_type": hair_type, "style_preference": style_preference
            }
            
            return await self.servers['beauty'].call_tool("create_beauty_profile", profile_data)
            
        except (KeyboardInterrupt, ValueError):
            return "❌ Creación cancelada"
    
    async def create_sleep_profile(self) -> str:
        """Crear perfil de sueño interactivo"""
        print("\n😴 CREACIÓN DE PERFIL DE SUEÑO")
        print("=" * 50)
        
        try:
            user_id = input("👤 ID de usuario: ").strip()
            if not user_id: return "❌ ID requerido"
            
            name = input("📝 Nombre: ").strip()
            if not name: return "❌ Nombre requerido"
            
            age = int(input("🎂 Edad: ").strip())
            
            chronotype = self.select_option("Cronotipo", ["morning_lark", "night_owl", "intermediate"])
            
            current_bedtime = input("🌙 Hora actual de dormir (HH:MM): ").strip()
            current_wake_time = input("🌅 Hora actual de despertar (HH:MM): ").strip()
            sleep_duration_hours = float(input("⏰ Horas de sueño promedio: ").strip())
            
            print("\nObjetivos (selecciona números separados por comas):")
            goals_options = ["better_quality", "more_energy", "weight_loss", "stress_reduction", "athletic_performance", "cognitive_performance"]
            for i, goal in enumerate(goals_options, 1):
                print(f"  {i}. {goal.replace('_', ' ').title()}")
            
            goals_input = input("Selecciones: ").strip()
            goals = [goals_options[int(i)-1] for i in goals_input.split(',') if i.isdigit() and 1 <= int(i) <= len(goals_options)]
            
            work_schedule = input("📅 Horario de trabajo (ej: 9-17): ").strip()
            
            profile_data = {
                "user_id": user_id, "name": name, "age": age, "chronotype": chronotype,
                "current_bedtime": current_bedtime, "current_wake_time": current_wake_time,
                "sleep_duration_hours": sleep_duration_hours, "goals": goals, "work_schedule": work_schedule
            }
            
            return await self.servers['sleep'].call_tool("create_user_profile", profile_data)
            
        except (KeyboardInterrupt, ValueError) as e:
            return f"❌ Error en creación: {str(e)}"
    
    def select_option(self, prompt: str, options: List[str]) -> str:
        """Seleccionar opción de una lista"""
        print(f"\n{prompt}:")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        
        while True:
            try:
                choice = input("Selección: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(options):
                    return options[int(choice)-1]
                else:
                    print("Selección inválida")
            except (ValueError, KeyboardInterrupt):
                return options[0]  # Valor por defecto
    
    # === FUNCIONES DE AYUDA ===
    
    def get_help_message(self) -> str:
        """Mensaje de ayuda completo"""
        return """ MULTI MCP CLIENT - AYUDA COMPLETA

 BEAUTY PALETTE SERVER:
  /beauty create               - Crear perfil de belleza
  /beauty list                 - Listar perfiles
  /beauty profile <user_id>    - Ver perfil específico
  /beauty history <user_id>    - Historial de paletas
  
  /palette <tipo> <user_id> <evento>  - Generar paleta
    Tipos: ropa, maquillaje, accesorios
    Eventos: casual, trabajo, formal, fiesta, cita
  
  /quote [categoria]           - Cita inspiracional
  /harmony <color1> <color2>   - Análisis de armonía

🎬 MOVIES SERVER:
  /movie search <título>       - Buscar películas
  /movie details <título>      - Detalles de película
  /movie actor <nombre>        - Películas por actor
  /movie similar <título>      - Películas similares
  /movie recommend             - Recomendaciones
  /movie playlist [minutos]    - Crear playlist

😴 SLEEP COACH SERVER:
  /sleep profile               - Crear perfil de sueño
  /sleep analyze <user_id>     - Analizar patrón
  /sleep recommend <user_id>   - Recomendaciones
  /sleep schedule <user_id>    - Horario semanal
  /sleep advice <consulta>     - Consejo rápido

⚙️ SISTEMA:
  /help                        - Esta ayuda
  /status                      - Estado de servidores
  /stats                       - Estadísticas de sesión
  /clear                       - Limpiar historial
  /quit                        - Salir

FLUJO RECOMENDADO:
1. Crear perfiles: /beauty create, /sleep profile
2. Usar servicios: /palette, /movie search, /sleep analyze
3. Obtener recomendaciones y análisis personalizados"""
    
    def get_beauty_help(self) -> str:
        return """ BEAUTY PALETTE SERVER

GESTIÓN:
  /beauty create    - Crear perfil completo
  /beauty list      - Ver todos los perfiles
  /beauty profile <id> - Detalles de perfil
  /beauty history <id> - Historial de paletas

PALETAS:
  /palette ropa <user_id> <evento>
  /palette maquillaje <user_id> <evento>
  /palette accesorios <user_id> <evento>

OTROS:
  /quote [categoria] - Cita inspiracional
  /harmony #color1 #color2 - Análisis de colores"""
    
    def get_movies_help(self) -> str:
        return """🎬 MOVIES SERVER

BÚSQUEDA:
  /movie search <título>    - Buscar películas
  /movie details <título>   - Información detallada
  /movie actor <nombre>     - Películas por actor
  /movie similar <título>   - Películas similares

RECOMENDACIONES:
  /movie recommend          - Recomendaciones generales
  /movie playlist [minutos] - Crear playlist (default: 480 min)

EJEMPLO: /movie search "The Matrix" """
    
    def get_sleep_help(self) -> str:
        return """😴 SLEEP COACH SERVER

PERFIL:
  /sleep profile           - Crear perfil de sueño

ANÁLISIS:
  /sleep analyze <user_id>   - Analizar patrón actual
  /sleep recommend <user_id> - Recomendaciones personalizadas
  /sleep schedule <user_id>  - Horario semanal optimizado

CONSEJOS:
  /sleep advice <consulta>   - Consejo rápido
  
EJEMPLO: /sleep advice "no puedo dormir" """
    
    def get_quick_help(self) -> str:
        return """ Multi MCP Client - Usa /help para ayuda completa

 Beauty: /beauty create, /palette ropa user_id trabajo
🎬 Movies: /movie search título, /movie recommend  
😴 Sleep: /sleep profile, /sleep advice consulta
⚙️ Sistema: /status, /help, /quit"""
    
    def show_welcome(self):
        """Mostrar mensaje de bienvenida"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Multi MCP Client                          ║
║         Beauty • 🎬 Movies • 😴 Sleep Coach               ║
╠══════════════════════════════════════════════════════════════╣
║   Perfiles y Paletas de Belleza Personalizadas             ║
║  🎬 Base de Datos de Películas y Recomendaciones             ║
║  😴 Coach Personal de Sueño y Rutinas                        ║
║   Integración Multi-Servidor MCP                           ║
╚══════════════════════════════════════════════════════════════╝

 Cliente Multi-MCP iniciado
 Usa /help para ver todos los comandos disponibles
"""
        print(banner)
    
    def show_server_status(self):
        """Mostrar estado de los servidores"""
        print("🔗 ESTADO DE SERVIDORES MCP:")
        for name, server in self.servers.items():
            status = "✅ Conectado" if server.active else "❌ Desconectado"
            print(f"   {server.display_name}: {status}")
        print()
    
    def get_session_stats(self) -> str:
        """Obtener estadísticas de sesión"""
        total_messages = len(self.conversation_history)
        connected_servers = sum(1 for s in self.servers.values() if s.active)
        
        return f""" ESTADÍSTICAS DE SESIÓN:
💬 Total mensajes: {total_messages}
🔗 Servidores conectados: {connected_servers}/{len(self.servers)}
 ID de sesión: {self.session_id}
⚙️ Servidores activos: {', '.join(s.display_name for s in self.servers.values() if s.active)}"""
    
    async def cleanup(self):
        """Limpiar recursos"""
        for server in self.servers.values():
            server.stop()
        print(" Todos los servidores desconectados")

# Clases simples para cuando las vistas no están disponibles
class SimpleConsoleView:
    def show_welcome_message(self): pass
    def get_user_input(self): return input("> ").strip()
    def show_response(self, response): print(f"\n{response}")
    def show_error(self, error): print(f"\n❌ {error}")

class SimpleBeautyView:
    def show_beauty_help(self): return " Beauty System"
    def collect_profile_data(self): return None

async def main():
    """Función principal del cliente multi-MCP"""
    try:
        client = MultiMCPClient()
        
        if await client.start():
            await client.run()
        else:
            print("❌ No se pudieron conectar servidores MCP")
            print("💡 Asegúrate de que los archivos de servidor estén disponibles")
            
    except KeyboardInterrupt:
        print("\n Cliente interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())