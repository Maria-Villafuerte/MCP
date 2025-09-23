#!/usr/bin/env python3
"""
Cliente Multi-MCP - Conecta a múltiples servidores MCP (local, sleep coach, movies)
"""

import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple

# Agregar src al path para imports de vistas
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from views.chat_view import ChatView
from views.beauty_view import BeautyView

class MCPConnection:
    """Maneja una conexión individual a un servidor MCP"""
    
    def __init__(self, server_script: str, server_name: str):
        self.server_script = server_script
        self.server_name = server_name
        self.server_process = None
        self.message_id = 0
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Inicializar conexión con el servidor MCP"""
        try:
            # Verificar que el script existe
            if not Path(self.server_script).exists():
                print(f"No se encuentra {self.server_name}: {self.server_script}")
                return False
            
            # Iniciar proceso del servidor
            self.server_process = subprocess.Popen(
                [sys.executable, self.server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Inicializar protocolo MCP
            if await self._initialize_mcp():
                self.is_initialized = True
                return True
            else:
                self._cleanup_process()
                return False
                
        except Exception as e:
            print(f"Error conectando a {self.server_name}: {e}")
            self._cleanup_process()
            return False
    
    async def _initialize_mcp(self) -> bool:
        """Inicializar protocolo MCP"""
        try:
            init_message = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {
                        "name": f"MCPChatbot-MultiClient-{self.server_name}",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self._send_mcp_request(init_message)
            
            if response and "result" in response:
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                await self._send_mcp_notification(initialized_notification)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error inicializando protocolo MCP para {self.server_name}: {e}")
            return False
    
    def _next_id(self) -> int:
        self.message_id += 1
        return self.message_id
    
    async def _send_mcp_request(self, message: Dict) -> Optional[Dict]:
        """Enviar request MCP y obtener respuesta"""
        try:
            if not self.server_process:
                return None
            
            message_str = json.dumps(message) + "\n"
            self.server_process.stdin.write(message_str)
            self.server_process.stdin.flush()
            
            response_line = self.server_process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            
            return None
            
        except Exception as e:
            print(f"Error enviando request a {self.server_name}: {e}")
            return None
    
    async def _send_mcp_notification(self, message: Dict) -> None:
        """Enviar notificación MCP"""
        try:
            if not self.server_process:
                return
            
            message_str = json.dumps(message) + "\n"
            self.server_process.stdin.write(message_str)
            self.server_process.stdin.flush()
            
        except Exception as e:
            print(f"Error enviando notification a {self.server_name}: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Optional[str]:
        """Llamar herramienta MCP"""
        try:
            if not self.is_initialized:
                return f"Servidor {self.server_name} no inicializado"
            
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
            return f"Error llamando herramienta en {self.server_name}: {str(e)}"
    
    def is_connected(self) -> bool:
        """Verificar si la conexión está activa"""
        return (self.is_initialized and 
                self.server_process and 
                self.server_process.poll() is None)
    
    async def reconnect(self) -> bool:
        """Intentar reconectar"""
        self._cleanup_process()
        self.is_initialized = False
        return await self.initialize()
    
    def _cleanup_process(self):
        """Limpiar proceso del servidor"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            except Exception:
                pass
            self.server_process = None
    
    def cleanup(self):
        """Limpiar recursos"""
        self._cleanup_process()
        self.is_initialized = False

class SleepCommandAdapter:
    """Adaptador para comandos del servidor sleep coach"""
    
    @staticmethod
    def parse_sleep_command(command: str) -> Tuple[str, Dict]:
        """Convierte comandos de usuario a llamadas MCP para sleep coach"""
        parts = command.strip().split()
        
        if len(parts) < 2:
            return ('quick_sleep_advice', {'query': 'ayuda general para dormir mejor'})
        
        action = parts[1].lower()
        
        if action == 'help':
            return ('quick_sleep_advice', {'query': 'comandos disponibles'})
        
        elif action == 'profile':
            # /sleep profile - crear perfil interactivo
            profile_data = SleepCommandAdapter._get_interactive_profile()
            return ('create_user_profile', profile_data)
        
        elif action == 'analyze':
            # /sleep analyze <user_id>
            user_id = parts[2] if len(parts) > 2 else 'default_user'
            return ('analyze_sleep_pattern', {'user_id': user_id})
        
        elif action == 'recommend':
            # /sleep recommend <user_id>
            user_id = parts[2] if len(parts) > 2 else 'default_user'
            return ('get_personalized_recommendations', {'user_id': user_id})
        
        elif action == 'schedule':
            # /sleep schedule <user_id>
            user_id = parts[2] if len(parts) > 2 else 'default_user'
            return ('create_weekly_schedule', {'user_id': user_id})
        
        else:
            # Cualquier otra cosa es consejo rápido
            query = ' '.join(parts[1:])
            return ('quick_sleep_advice', {'query': query})
    
    @staticmethod
    def _get_interactive_profile() -> Dict:
        """Crear perfil de sueño de forma interactiva (simplificado)"""
        from datetime import datetime
        
        # Por ahora uso un perfil demo, pero podría extenderse para ser interactivo
        user_id = f"user_{datetime.now().strftime('%m%d_%H%M')}"
        
        return {
            "user_id": user_id,
            "name": "Usuario Demo",
            "age": 30,
            "chronotype": "intermediate",  # morning_lark, night_owl, intermediate
            "current_bedtime": "23:00",
            "current_wake_time": "07:00",
            "sleep_duration_hours": 8.0,
            "goals": ["better_quality", "more_energy"],
            "work_schedule": "9-17",
            "screen_time_before_bed": 60,
            "stress_level": 5,
            "sleep_quality_rating": 6
        }

class MovieCommandAdapter:
    """Adaptador para comandos del servidor de películas"""
    
    @staticmethod
    def parse_movie_command(command: str) -> Tuple[str, Dict]:
        """Convierte comandos de usuario a llamadas MCP para movies"""
        parts = command.strip().split()
        
        if len(parts) < 2:
            return ('search_movie', {'params': {'query': 'popular movies', 'limit': 10}})
        
        action = parts[1].lower()
        
        if action == 'search':
            # /movie search <título>
            if len(parts) < 3:
                return ('search_movie', {'params': {'query': 'popular movies', 'limit': 10}})
            query = ' '.join(parts[2:])
            return ('search_movie', {'params': {'query': query, 'limit': 10}})
        
        elif action == 'details':
            # /movie details <título>
            if len(parts) < 3:
                return ('search_movie', {'params': {'query': 'popular movies', 'limit': 5}})
            title = ' '.join(parts[2:])
            return ('movie_details', {'params': {'title': title}})
        
        elif action == 'recommend':
            # /movie recommend [géneros] [años]
            return MovieCommandAdapter._parse_recommend_args(parts[2:])
        
        elif action == 'actor':
            # /movie actor <nombre>
            if len(parts) < 3:
                return ('search_movie', {'params': {'query': 'popular actors', 'limit': 5}})
            actor = ' '.join(parts[2:])
            return ('top_movies_by_actor_tool', {'params': {'actor': actor, 'limit': 15}})
        
        elif action == 'similar':
            # /movie similar <título>
            if len(parts) < 3:
                return ('search_movie', {'params': {'query': 'popular movies', 'limit': 5}})
            title = ' '.join(parts[2:])
            return ('similar_movies_tool', {'params': {'title': title, 'limit': 15}})
        
        elif action == 'playlist':
            # /movie playlist <minutos> [géneros]
            return MovieCommandAdapter._parse_playlist_args(parts[2:])
        
        elif action == 'help':
            # Mostrar ayuda específica de películas
            return ('search_movie', {'params': {'query': 'help comandos disponibles', 'limit': 1}})
        
        else:
            # Si no es un comando conocido, buscar como título
            query = ' '.join(parts[1:])
            return ('search_movie', {'params': {'query': query, 'limit': 10}})
    
    @staticmethod
    def _parse_recommend_args(args: List[str]) -> Tuple[str, Dict]:
        """Parsear argumentos para recomendaciones"""
        params = {
            'genres': None,
            'min_vote': 0.0,
            'from_year': None,
            'to_year': None,
            'language': None,
            'limit': 15
        }
        
        # Parsear géneros y años
        for arg in args:
            if '-' in arg and arg.replace('-', '').isdigit():
                # Rango de años: 2020-2023
                try:
                    start, end = arg.split('-')
                    params['from_year'] = int(start)
                    params['to_year'] = int(end)
                except ValueError:
                    pass
            elif arg.isdigit():
                # Año específico
                year = int(arg)
                params['from_year'] = year
                params['to_year'] = year
            elif arg.lower() in ['action', 'comedy', 'drama', 'horror', 'romance', 'sci-fi', 'thriller', 'adventure', 'animation']:
                # Género
                if params['genres'] is None:
                    params['genres'] = []
                params['genres'].append(arg.lower())
        
        return ('recommend_movies_tool', {'params': params})
    
    @staticmethod
    def _parse_playlist_args(args: List[str]) -> Tuple[str, Dict]:
        """Parsear argumentos para playlist"""
        params = {
            'target_minutes': 480,  # 8 horas por defecto
            'prefer_high_rating': True,
            'genres': None,
            'language': None
        }
        
        for arg in args:
            if arg.isdigit():
                params['target_minutes'] = int(arg)
            elif arg.lower() in ['action', 'comedy', 'drama', 'horror', 'romance']:
                if params['genres'] is None:
                    params['genres'] = []
                params['genres'].append(arg.lower())
        
        return ('build_playlist_tool', {'params': params})

class MultiMCPClient:
    """Cliente que maneja conexiones a múltiples servidores MCP"""
    
    def __init__(self):
        self.connections = {
            'local': MCPConnection('server_local.py', 'Local (Belleza/Citas)'),
            'sleep': MCPConnection('sleep_coach.py', 'Sleep Coach'),
            'movies': MCPConnection('movie_server.py', 'Movies')
        }
        self.session_id = f"multi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.chat_view = ChatView()
        self.beauty_view = BeautyView()
        self.conversation_history = []
    
    async def initialize(self) -> bool:
        """Inicializar todas las conexiones MCP"""
        results = {}
        print("Iniciando conexiones a servidores MCP...")
        
        for name, conn in self.connections.items():
            try:
                print(f"Conectando a {conn.server_name}...")
                results[name] = await conn.initialize()
                status = "Conectado" if results[name] else "Error"
                print(f"  {conn.server_name}: {status}")
            except Exception as e:
                print(f"  {conn.server_name}: Error - {e}")
                results[name] = False
        
        # Verificar que al menos el servidor local esté disponible
        if not results.get('local', False):
            print("Error: Servidor local no disponible. No se puede continuar.")
            return False
        
        # Mostrar resumen de conexiones
        connected_count = sum(1 for connected in results.values() if connected)
        print(f"\n{connected_count}/{len(self.connections)} servidores conectados")
        
        return True
    
    async def run_interactive_mode(self):
        """Ejecutar modo interactivo multi-servidor"""
        # Mostrar mensaje de bienvenida personalizado
        self._show_multi_welcome()
        
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
    
    def _show_multi_welcome(self):
        """Mostrar mensaje de bienvenida multi-servidor"""
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                 MCPChatbot Multi-Servidor v2.0              ║
║             Chat Inteligente con Múltiples Servicios        ║
╠══════════════════════════════════════════════════════════════╣
║  🔗 Protocolo MCP Distribuido                               ║
║  {'✅' if self.connections['local'].is_connected() else '❌'} Servidor Local (Belleza, Citas)                         ║
║  {'✅' if self.connections['sleep'].is_connected() else '❌'} Sleep Coach (Rutinas de Sueño)                         ║
║  {'✅' if self.connections['movies'].is_connected() else '❌'} Movies Database (Recomendaciones)                      ║
╚══════════════════════════════════════════════════════════════╝

💬 Usa /help para ver todos los comandos disponibles
🆔 Sesión: {self.session_id}

═══════════════════════════════════════════════════════════════
"""
        print(banner)
    
    async def process_user_input(self, user_input: str) -> str:
        """Procesar entrada del usuario y rutear al servidor apropiado"""
        try:
            # Agregar al historial
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Verificar comandos especiales locales
            if user_input.startswith('/'):
                return await self.process_special_command(user_input)
            
            # Mensajes normales van al servidor local (Claude)
            response = await self._route_to_server('local', 'chat', {"message": user_input})
            
            if response and not response.startswith("❌"):
                self.conversation_history.append({"role": "assistant", "content": response})
            
            return response or "No se pudo obtener respuesta"
            
        except Exception as e:
            return f"❌ Error procesando mensaje: {str(e)}"
    
    async def process_special_command(self, command: str) -> str:
        """Procesar comandos especiales y rutear a servidores"""
        command_lower = command.lower().strip()
        
        # Comandos locales (no requieren servidor)
        if command_lower == '/help':
            return self._get_integrated_help()
        elif command_lower == '/quit':
            return "Cerrando cliente multi-servidor..."
        elif command_lower == '/status':
            return self._get_servers_status()
        elif command_lower == '/context':
            return self._show_context_summary()
        elif command_lower == '/clear':
            self.conversation_history = []
            return "🧹 Contexto limpiado"
        
        # Comandos de Sleep Coach
        elif command_lower.startswith('/sleep'):
            tool_name, arguments = SleepCommandAdapter.parse_sleep_command(command)
            return await self._route_to_server('sleep', tool_name, arguments)
        
        # Comandos de Movies
        elif command_lower.startswith('/movie') or command_lower.startswith('/film'):
            tool_name, arguments = MovieCommandAdapter.parse_movie_command(command)
            return await self._route_to_server('movies', tool_name, arguments)
        
        # Comandos del servidor local
        elif command_lower.startswith('/beauty'):
            # Rutear comandos beauty directamente según el tipo
            if 'create_profile' in command_lower:
                return await self._route_to_server('local', 'create_profile', self._get_demo_beauty_profile())
            else:
                return await self._route_to_server('local', 'git_command', {"command": command})
        
        elif command_lower.startswith('/palette'):
            return await self._route_to_server('local', 'git_command', {"command": command})
        
        elif command_lower.startswith('/quotes'):
            category = command.split()[2] if len(command.split()) > 2 else None
            return await self._route_to_server('local', 'get_quote', {"category": category} if category else {})
        
        else:
            return f"❌ Comando desconocido: {command}. Usa /help para ver comandos disponibles"
    
    async def _route_to_server(self, server: str, tool_name: str, arguments: Dict) -> str:
        """Rutear llamada al servidor apropiado con manejo de errores"""
        if server not in self.connections:
            return f"❌ Servidor {server} no disponible"
        
        conn = self.connections[server]
        
        try:
            if not conn.is_connected():
                # Intentar reconectar
                print(f"🔄 Intentando reconectar {conn.server_name}...")
                if await conn.reconnect():
                    print(f"✅ {conn.server_name} reconectado")
                else:
                    return f"❌ No se pudo reconectar a {conn.server_name}"
            
            result = await conn.call_tool(tool_name, arguments)
            return result or f"❌ Sin respuesta de {conn.server_name}"
            
        except Exception as e:
            # Fallback para algunos comandos críticos
            if server == 'sleep':
                return self._sleep_fallback(tool_name, arguments)
            elif server == 'movies':
                return "❌ Servidor de películas temporalmente no disponible"
            else:
                return f"❌ Error en {conn.server_name}: {str(e)}"
    
    def _sleep_fallback(self, tool_name: str, arguments: Dict) -> str:
        """Fallback local para comandos de sueño básicos"""
        if tool_name == 'quick_sleep_advice':
            return """💤 CONSEJOS RÁPIDOS DE SUEÑO (Modo Offline):

• Mantén horarios consistentes todos los días
• Apaga pantallas 1-2 horas antes de dormir  
• Temperatura ideal: 18-20°C en el dormitorio
• Evita cafeína 6-8 horas antes de acostarte
• Crea una rutina relajante pre-sueño
• Haz ejercicio regularmente, pero no antes de dormir

🔗 Servidor Sleep Coach no disponible. Consejos básicos mostrados."""
        return "❌ Sleep Coach no disponible y sin fallback para este comando"
    
    def _get_integrated_help(self) -> str:
        """Help integrado que muestra comandos de todos los servidores"""
        return f"""🔧 SISTEMA MULTICHAT MCP - AYUDA COMPLETA

🌟 SERVIDORES DISPONIBLES:
{'✅' if self.connections['local'].is_connected() else '❌'} Local (Belleza, Citas)
{'✅' if self.connections['sleep'].is_connected() else '❌'} Sleep Coach  
{'✅' if self.connections['movies'].is_connected() else '❌'} Movies Database

💄 SISTEMA DE BELLEZA:
  /beauty create_profile      - Crear perfil personalizado
  /beauty list_profiles       - Listar perfiles disponibles
  /beauty profile <user_id>   - Ver perfil específico
  /beauty history <user_id>   - Ver historial de paletas
  /palette ropa <user> <evento> - Generar paleta de ropa
  /palette maquillaje <user> <evento> - Paleta maquillaje
  /palette accesorios <user> <evento> - Paleta accesorios
  /quotes get [categoría]     - Cita inspiracional

😴 SLEEP COACH:
  /sleep profile              - Crear perfil de sueño
  /sleep analyze <user>       - Analizar patrón de sueño  
  /sleep recommend <user>     - Recomendaciones personalizadas
  /sleep schedule <user>      - Crear horario semanal optimizado
  /sleep <consulta>           - Consejo rápido sobre sueño

🎬 PELÍCULAS:
  /movie search <título>      - Buscar películas
  /movie details <título>     - Detalles completos de película
  /movie recommend [géneros] [años] - Recomendar películas
  /movie actor <nombre>       - Top películas de actor/actriz
  /movie similar <título>     - Películas similares
  /movie playlist <minutos> [géneros] - Crear lista de reproducción

📋 SISTEMA:
  /help       - Esta ayuda completa
  /status     - Estado de todos los servidores
  /context    - Ver contexto de conversación
  /clear      - Limpiar contexto
  /quit       - Salir del sistema

🔗 Sesión: {self.session_id}
💡 Los mensajes normales (sin /) van a Claude API a través del servidor local

📝 EJEMPLOS DE USO:
• /beauty create_profile
• /palette ropa maria_123 trabajo
• /sleep insomnio me cuesta dormir
• /movie search batman
• /movie recommend action 2020-2023"""

    def _get_servers_status(self) -> str:
        """Estado detallado de todos los servidores"""
        status_text = "🔍 ESTADO DE SERVIDORES MCP:\n\n"
        
        for name, conn in self.connections.items():
            status = "🟢 Conectado" if conn.is_connected() else "🔴 Desconectado"
            status_text += f"{conn.server_name}: {status}\n"
            status_text += f"   Script: {conn.server_script}\n"
            status_text += f"   Inicializado: {'Sí' if conn.is_initialized else 'No'}\n\n"
        
        connected_count = sum(1 for conn in self.connections.values() if conn.is_connected())
        status_text += f"Total conectados: {connected_count}/{len(self.connections)}"
        
        return status_text
    
    def _show_context_summary(self) -> str:
        """Mostrar resumen del contexto de conversación"""
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
        
        summary += f"\n📊 Total: {total_messages} | Usuario: {user_messages} | Asistente: {assistant_messages}"
        
        return summary
    
    def _get_demo_beauty_profile(self) -> Dict:
        """Perfil demo para beauty create_profile"""
        from datetime import datetime
        
        return {
            "user_id": f"beauty_{datetime.now().strftime('%m%d_%H%M')}",
            "name": "Usuario Demo Belleza",
            "skin_tone": "media",
            "eye_color": "cafe", 
            "hair_color": "castano",
            "undertone": "calido",
            "hair_type": "ondulado",
            "style_preference": "moderno"
        }
    
    async def cleanup(self):
        """Limpiar todas las conexiones"""
        print("🧹 Cerrando conexiones MCP...")
        
        for name, conn in self.connections.items():
            try:
                conn.cleanup()
                print(f"  {conn.server_name}: Desconectado")
            except Exception as e:
                print(f"  {conn.server_name}: Error al desconectar - {e}")
        
        print("✅ Cliente Multi-MCP desconectado")

def show_banner():
    """Banner de inicio del cliente multi-servidor"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                 MCPChatbot Cliente Multi-Servidor           ║
║              Conectando a Múltiples Servidores MCP          ║
╠══════════════════════════════════════════════════════════════╣
║  🔗 Protocolo MCP via stdio distribuido                     ║
║  🤖 Claude API + Sistema de Belleza                         ║
║  😴 Sleep Coach + Rutinas de Sueño                          ║
║  🎬 Base de Datos de Películas                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

async def main():
    """Función principal del cliente multi-servidor"""
    show_banner()
    
    try:
        # Inicializar cliente multi-MCP
        client = MultiMCPClient()
        
        if await client.initialize():
            await client.run_interactive_mode()
        else:
            print("\n❌ No se pudieron establecer las conexiones mínimas necesarias")
            print("💡 Asegúrate de que server_local.py esté disponible")
            
    except KeyboardInterrupt:
        print("\n👋 Cliente multi-servidor interrumpido")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())