#!/usr/bin/env python3
"""
Cliente MCP Simple - Conecta a múltiples servidores MCP
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from views.chat_view import ChatView

class SimpleConnection:
    def __init__(self, script_name, display_name):
        self.script = script_name
        self.name = display_name
        self.process = None
        self.msg_id = 0
        self.active = False
    
    async def start(self):
        """Iniciar servidor"""
        if not Path(self.script).exists():
            print(f"No se encuentra: {self.script}")
            return False
        
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Inicializar MCP
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "SimpleClient", "version": "1.0"}
                }
            }
            
            response = await self.send_request(init_msg)
            if response and "result" in response:
                # Enviar initialized
                await self.send_notification({"jsonrpc": "2.0", "method": "notifications/initialized"})
                self.active = True
                return True
            
            return False
            
        except Exception as e:
            print(f"Error iniciando {self.name}: {e}")
            return False
    
    async def send_request(self, message):
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
    
    async def send_notification(self, message):
        """Enviar notificación"""
        try:
            if self.process:
                msg_str = json.dumps(message) + "\n"
                self.process.stdin.write(msg_str)
                self.process.stdin.flush()
        except Exception:
            pass
    
    async def call_tool(self, tool_name, args):
        """Llamar herramienta"""
        self.msg_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": args}
        }
        
        response = await self.send_request(request)
        if response and "result" in response:
            content = response["result"]["content"]
            if content and len(content) > 0:
                return content[0]["text"]
        
        return "Sin respuesta"
    
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
        self.connections = {
            'local': SimpleConnection('server_local.py', 'Belleza/Citas'),
            'sleep': SimpleConnection('sleep_coach.py', 'Sleep Coach'),
            'movies': SimpleConnection('movie_server.py', 'Movies')
        }
        self.chat_view = ChatView()
        self.history = []
    
    async def start(self):
        """Iniciar todos los servidores"""
        print("Iniciando servidores MCP...")
        
        results = {}
        for name, conn in self.connections.items():
            print(f"Conectando a {conn.name}...")
            results[name] = await conn.start()
            status = "✅" if results[name] else "❌"
            print(f"  {conn.name}: {status}")
        
        connected = sum(1 for r in results.values() if r)
        print(f"\n{connected}/{len(self.connections)} servidores conectados\n")
        
        return results.get('local', False)  # Al menos local debe funcionar
    
    async def run(self):
        """Ejecutar cliente"""
        self.chat_view.show_welcome_message()
        self.show_status()
        
        while True:
            try:
                user_input = self.chat_view.get_user_input()
                
                if user_input.lower() == '/quit':
                    break
                elif not user_input.strip():
                    continue
                
                response = await self.process_input(user_input)
                if response:
                    self.chat_view.show_response(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.chat_view.show_error(f"Error: {e}")
        
        await self.cleanup()
        self.chat_view.show_goodbye()
    
    def show_status(self):
        """Mostrar estado de conexiones"""
        print("🔗 SERVIDORES CONECTADOS:")
        for name, conn in self.connections.items():
            status = "✅" if conn.active else "❌"
            print(f"  {status} {conn.name}")
        print()
    
    async def process_input(self, user_input):
        """Procesar entrada del usuario"""
        self.history.append({"role": "user", "content": user_input})
        
        if user_input.startswith('/'):
            return await self.handle_command(user_input)
        
        # Mensaje normal - enviar a servidor local
        if self.connections['local'].active:
            response = await self.connections['local'].call_tool("chat", {"message": user_input})
            self.history.append({"role": "assistant", "content": response})
            return response
        else:
            return "Servidor local no disponible"
    
    async def handle_command(self, command):
        """Manejar comandos especiales"""
        parts = command.strip().split()
        if len(parts) < 2:
            return self.get_help()
        
        cmd = parts[0].lower()
        action = parts[1].lower()
        
        # Comandos locales
        if cmd == '/help':
            return self.get_help()
        elif cmd == '/status':
            self.show_status()
            return None
        elif cmd == '/clear':
            self.history = []
            return "Historial limpiado"
        elif cmd == '/context':
            return self._show_context_summary()
        
        # Comandos de belleza completos
        elif cmd == '/beauty':
            return await self.handle_beauty_command(command)
        
        elif cmd == '/palette':
            return await self.handle_palette_command(command)
        
        # Comandos de citas
        elif cmd == '/quotes':
            if not self.connections['local'].active:
                return "Servidor de citas no disponible"
            
            if action == 'get':
                category = parts[2] if len(parts) > 2 else None
                return await self.connections['local'].call_tool("get_quote", {"category": category} if category else {})
            else:
                return await self.connections['local'].call_tool("git_command", {"command": command})
        
        # Comandos de sueño
        elif cmd == '/sleep':
            if not self.connections['sleep'].active:
                return "Sleep Coach no disponible"
            
            if action == 'profile':
                return await self.handle_sleep_profile()
            elif action == 'analyze':
                user_id = parts[2] if len(parts) > 2 else 'default'
                return await self.connections['sleep'].call_tool("analyze_sleep_pattern", {"user_id": user_id})
            elif action == 'recommend':
                user_id = parts[2] if len(parts) > 2 else 'default'
                return await self.connections['sleep'].call_tool("get_personalized_recommendations", {"user_id": user_id})
            elif action == 'schedule':
                user_id = parts[2] if len(parts) > 2 else 'default'
                return await self.connections['sleep'].call_tool("create_weekly_schedule", {"user_id": user_id})
            else:
                query = ' '.join(parts[1:])
                return await self.connections['sleep'].call_tool("quick_sleep_advice", {"query": query})
        
        # Comandos de películas
        elif cmd == '/movie':
            if not self.connections['movies'].active:
                return "Servidor de películas no disponible"
            
            if action == 'search':
                if len(parts) < 3:
                    return "Uso: /movie search <título>"
                query = ' '.join(parts[2:])
                return await self.connections['movies'].call_tool("search_movie", {"query": query, "limit": 10})
            
            elif action == 'details':
                if len(parts) < 3:
                    return "Uso: /movie details <título>"
                title = ' '.join(parts[2:])
                return await self.connections['movies'].call_tool("movie_details", {"title": title})
            
            elif action == 'actor':
                if len(parts) < 3:
                    return "Uso: /movie actor <nombre>"
                actor = ' '.join(parts[2:])
                return await self.connections['movies'].call_tool("top_movies_by_actor_tool", {"actor": actor, "limit": 10})
            
            elif action == 'similar':
                if len(parts) < 3:
                    return "Uso: /movie similar <título>"
                title = ' '.join(parts[2:])
                return await self.connections['movies'].call_tool("similar_movies_tool", {"title": title, "limit": 10})
            
            elif action == 'recommend':
                return await self.connections['movies'].call_tool("recommend_movies_tool", {
                    "genres": None, "min_vote": 0.0, "from_year": None, "to_year": None,
                    "language": None, "include_cast": None, "limit": 15
                })
            
            else:
                return "Comandos: search, details, actor, similar, recommend"
        
        else:
            return f"Comando desconocido: {cmd}"
    
    def _show_context_summary(self):
        """Mostrar resumen del contexto"""
        if not self.history:
            return "No hay mensajes en el contexto actual"
        
        summary = "\n📋 RESUMEN DEL CONTEXTO ACTUAL:\n"
        summary += "-" * 40 + "\n"
        
        # Mostrar últimos 5 mensajes
        recent = self.history[-5:]
        for i, msg in enumerate(recent, 1):
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            content_preview = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
            summary += f"{i}. {role_icon} {content_preview}\n"
        
        total = len(self.history)
        user_msgs = len([m for m in self.history if m["role"] == "user"])
        assistant_msgs = len([m for m in self.history if m["role"] == "assistant"])
        
        summary += f"\n📊 Total: {total} | Usuario: {user_msgs} | Asistente: {assistant_msgs}"
        return summary
    
    async def handle_beauty_command(self, command):
        """Manejar comandos de belleza completos"""
        if not self.connections['local'].active:
            return "Servidor de belleza no disponible"
        
        try:
            parts = command.strip().split()
            if len(parts) < 2:
                return self.get_beauty_help()
            
            action = parts[1].lower()
            
            if action == "help":
                return self.get_beauty_help()
            
            elif action == "create_profile":
                return await self.create_profile_interactive()
            
            elif action == "list_profiles":
                return await self.connections['local'].call_tool("git_command", {"command": "/beauty list_profiles"})
            
            elif action == "profile":
                if len(parts) < 3:
                    return "❌ Especifica user_id. Uso: /beauty profile <user_id>"
                full_command = " ".join(parts)
                return await self.connections['local'].call_tool("git_command", {"command": full_command})
            
            elif action == "history":
                if len(parts) < 3:
                    return "❌ Especifica user_id. Uso: /beauty history <user_id>"
                full_command = " ".join(parts)
                return await self.connections['local'].call_tool("git_command", {"command": full_command})
            
            else:
                # Pasar comando completo al servidor
                return await self.connections['local'].call_tool("git_command", {"command": command})
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def create_profile_interactive(self):
        """Crear perfil de forma interactiva usando MCP"""
        try:
            # Recopilar datos usando la vista de belleza
            profile_data = self.collect_profile_data()
            
            if not profile_data:
                return "Creación de perfil cancelada"
            
            # Usar la herramienta MCP create_profile
            response = await self.connections['local'].call_tool("create_profile", profile_data)
            
            if response and "creado" in response.lower():
                return f"✅ {response}\n\n💄 Ahora puedes generar paletas con /palette"
            else:
                return f"❌ Error creando perfil: {response}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def collect_profile_data(self):
        """Recopilar datos para crear perfil (simplificado pero completo)"""
        print("\n🎨 CREACIÓN DE PERFIL DE BELLEZA")
        print("=" * 50)
        
        try:
            # Información básica
            user_id = input("👤 ID de usuario (único): ").strip()
            if not user_id:
                return None
                
            name = input("📝 Nombre completo: ").strip()
            if not name:
                return None
            
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
            print("  1. frío")
            print("  2. cálido")
            print("  3. neutro")
            under_choice = input("Selección (1-3): ").strip()
            undertones = ["frio", "calido", "neutro"]
            undertone = undertones[int(under_choice)-1] if under_choice.isdigit() and 1 <= int(under_choice) <= 3 else "neutro"
            
            print("\nColor de ojos:")
            print("  1. azul")
            print("  2. verde") 
            print("  3. café")
            print("  4. gris")
            print("  5. negro")
            eye_choice = input("Selección (1-5): ").strip()
            eye_colors = ["azul", "verde", "cafe", "gris", "negro"]
            eye_color = eye_colors[int(eye_choice)-1] if eye_choice.isdigit() and 1 <= int(eye_choice) <= 5 else "cafe"
            
            print("\nColor de cabello:")
            print("  1. rubio")
            print("  2. castaño")
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
            print("  1. clásico")
            print("  2. moderno")
            print("  3. bohemio")
            print("  4. minimalista")
            print("  5. romántico")
            print("  6. edgy")
            style_choice = input("Selección (1-6): ").strip()
            styles = ["clasico", "moderno", "bohemio", "minimalista", "romantico", "edgy"]
            style_preference = styles[int(style_choice)-1] if style_choice.isdigit() and 1 <= int(style_choice) <= 6 else "moderno"
            
            # Compilar datos
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
            
            # Confirmación
            print(f"\n✅ PERFIL CREADO:")
            print(f"   Nombre: {name}")
            print(f"   ID: {user_id}")
            print(f"   Tono de piel: {skin_tone} ({undertone})")
            print(f"   Ojos: {eye_color}")
            print(f"   Cabello: {hair_color} ({hair_type})")
            print(f"   Estilo: {style_preference}")
            
            confirm = input("\n¿Guardar este perfil? (s/n): ").strip().lower()
            if confirm in ['s', 'si', 'yes', 'y']:
                return profile_data
            else:
                print("Perfil cancelado")
                return None
                
        except (KeyboardInterrupt, ValueError):
            print("\nCreación de perfil cancelada")
            return None
        except Exception as e:
            print(f"\nError: {e}")
            return None
    
    async def handle_palette_command(self, command):
        """Manejar generación de paletas completa"""
        if not self.connections['local'].active:
            return "Servidor de belleza no disponible"
        
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
            print(f"🎨 Generando paleta {palette_type} para {event_type}...")
            preferences = self.collect_palette_preferences(palette_type, event_type)
            
            # Construir comando completo
            full_command = f"/palette {palette_type} {user_id} {event_type}"
            
            # Usar git_command para ejecutar el comando de paleta
            response = await self.connections['local'].call_tool("git_command", {"command": full_command})
            
            return response or "❌ No se pudo generar la paleta"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def collect_palette_preferences(self, palette_type, event_type):
        """Recopilar preferencias para paleta"""
        print(f"\n🎨 PREFERENCIAS PARA PALETA DE {palette_type.upper()}")
        print(f"   Evento: {event_type.title()}")
        
        preferences = {
            "palette_type": palette_type,
            "event_type": event_type
        }
        
        try:
            # Preferencias según tipo
            if palette_type == "ropa":
                print("\nEstación del año:")
                print("  1. primavera")
                print("  2. verano") 
                print("  3. otoño")
                print("  4. invierno")
                season_choice = input("Selección (1-4, Enter para omitir): ").strip()
                seasons = ["primavera", "verano", "otono", "invierno"]
                if season_choice.isdigit() and 1 <= int(season_choice) <= 4:
                    preferences["season"] = seasons[int(season_choice)-1]
                
                print("\nIntensidad de colores:")
                print("  1. suave")
                print("  2. medio")
                print("  3. vibrante") 
                intensity_choice = input("Selección (1-3, Enter para omitir): ").strip()
                intensities = ["suave", "medio", "vibrante"]
                if intensity_choice.isdigit() and 1 <= int(intensity_choice) <= 3:
                    preferences["color_intensity"] = intensities[int(intensity_choice)-1]
            
            elif palette_type == "maquillaje":
                print("\nIntensidad del look:")
                print("  1. natural")
                print("  2. medio")
                print("  3. dramático")
                look_choice = input("Selección (1-3, Enter para omitir): ").strip()
                looks = ["natural", "medio", "dramatico"]
                if look_choice.isdigit() and 1 <= int(look_choice) <= 3:
                    preferences["look_intensity"] = looks[int(look_choice)-1]
                
                print("\nÁrea de enfoque:")
                print("  1. ojos")
                print("  2. labios")
                print("  3. equilibrado")
                focus_choice = input("Selección (1-3, Enter para omitir): ").strip()
                focuses = ["ojos", "labios", "equilibrado"]
                if focus_choice.isdigit() and 1 <= int(focus_choice) <= 3:
                    preferences["focus_area"] = focuses[int(focus_choice)-1]
            
            elif palette_type == "accesorios":
                print("\nPreferencia de metales:")
                print("  1. oro")
                print("  2. plata")
                print("  3. oro rosa")
                print("  4. mixto")
                metal_choice = input("Selección (1-4, Enter para omitir): ").strip()
                metals = ["oro", "plata", "oro_rosa", "mixto"]
                if metal_choice.isdigit() and 1 <= int(metal_choice) <= 4:
                    preferences["metal_preference"] = metals[int(metal_choice)-1]
        
        except (KeyboardInterrupt, ValueError):
            print("Usando preferencias por defecto...")
        
        return preferences
    
    async def handle_sleep_profile(self):
        """Crear perfil de sueño simplificado"""
        profile_data = {
            "user_id": f"user_{len(self.history)}",
            "name": "Usuario Demo",
            "age": 30,
            "chronotype": "intermediate",
            "current_bedtime": "23:00",
            "current_wake_time": "07:00",
            "sleep_duration_hours": 8.0,
            "goals": ["better_quality", "more_energy"],
            "work_schedule": "9-17"
        }
        
        return await self.connections['sleep'].call_tool("create_user_profile", profile_data)
    
    def get_help(self):
        """Mostrar ayuda"""
        return """CLIENTE MCP MULTI-SERVIDOR

COMANDOS DISPONIBLES:

🎨 BELLEZA:
  /beauty help                 - Ayuda de belleza
  /palette ropa <user> <evento> - Generar paleta

💫 CITAS:
  /quotes get [categoría]      - Obtener cita
  /quotes search <término>     - Buscar citas

😴 SUEÑO:
  /sleep profile              - Crear perfil
  /sleep analyze <user>       - Analizar patrón
  /sleep recommend <user>     - Recomendaciones
  /sleep <consulta>           - Consejo rápido

🎬 PELÍCULAS:
  /movie search <título>      - Buscar películas
  /movie details <título>     - Detalles de película
  /movie actor <nombre>       - Películas de actor
  /movie similar <título>     - Películas similares
  /movie recommend            - Recomendar películas

⚙️ SISTEMA:
  /help                       - Esta ayuda
  /status                     - Estado servidores
  /clear                      - Limpiar historial
  /quit                       - Salir

💬 Los mensajes normales van a Claude API"""
    
    def get_beauty_help(self):
        """Ayuda específica de belleza"""
        return """SISTEMA DE BELLEZA

COMANDOS:
  /beauty create_profile       - Crear perfil
  /beauty list_profiles        - Listar perfiles
  /beauty profile <user_id>    - Ver perfil
  /palette ropa <user> <evento>     - Paleta de ropa
  /palette maquillaje <user> <evento> - Paleta maquillaje

EVENTOS: casual, formal, fiesta, trabajo, cita

EJEMPLO:
  /beauty create_profile
  /palette ropa maria_123 trabajo"""
    
    async def cleanup(self):
        """Limpiar conexiones"""
        for conn in self.connections.values():
            conn.stop()
        print("Servidores desconectados")

def show_banner():
    """Banner de inicio"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                 MCPChatbot Multi-Servidor                    ║
║              Conectando a Múltiples Servidores              ║
╠══════════════════════════════════════════════════════════════╣
║  🎨 Sistema de Belleza                                       ║
║  😴 Sleep Coach                                              ║
║  🎬 Base de Películas                                        ║
║  💫 Citas Inspiracionales                                    ║
╚══════════════════════════════════════════════════════════════╝
""")

async def main():
    """Función principal"""
    show_banner()
    
    try:
        client = MultiMCPClient()
        
        if await client.start():
            await client.run()
        else:
            print("No se pudo conectar al servidor principal")
            
    except KeyboardInterrupt:
        print("\nCliente interrumpido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())