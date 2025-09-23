#!/usr/bin/env python3
"""
Cliente MCP que se conecta al servidor local
"""

import asyncio
import httpx
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Agregar src al path para imports de vistas
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from views.chat_view import ChatView
from views.beauty_view import BeautyView

class RemoteClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        """Inicializar cliente remoto"""
        self.server_url = server_url
        self.session_id = f"client_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.chat_view = ChatView()
        self.beauty_view = BeautyView()
        self.client = None
    
    async def initialize(self) -> bool:
        """Verificar conexión con servidor"""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            
            # Test de conexión
            response = await self.client.get(f"{self.server_url}/health")
            health = response.json()
            
            if health["status"] == "healthy":
                print("✅ Conectado al servidor local")
                return True
            else:
                print("⚠️ Servidor local no saludable")
                return False
                
        except Exception as e:
            print(f" No se pudo conectar al servidor local: {str(e)}")
            print("💡 Asegúrate de que el servidor esté corriendo con: python3 server_local.py")
            return False
    
    async def run_interactive_mode(self):
        """Ejecutar modo interactivo conectado al servidor"""
        # Mostrar mensaje de bienvenida
        self.chat_view.show_welcome_message()
        print(f"🔗 Conectado a servidor: {self.server_url}")
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
            # Verificar comandos especiales
            if user_input.startswith('/'):
                return await self.process_special_command(user_input)
            
            # Procesar mensaje normal
            return await self.send_chat_message(user_input)
            
        except Exception as e:
            return f" Error procesando mensaje: {str(e)}"
    
    async def send_chat_message(self, message: str) -> str:
        """Enviar mensaje de chat al servidor"""
        try:
            response = await self.client.post(
                f"{self.server_url}/chat",
                json={
                    "message": message,
                    "session_id": self.session_id
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["response"]
            
        except httpx.RequestError as e:
            return f" Error de conexión: {str(e)}"
        except httpx.HTTPStatusError as e:
            return f" Error del servidor: {e.response.status_code}"
        except Exception as e:
            return f" Error: {str(e)}"
    
    async def process_special_command(self, command: str) -> str:
        """Procesar comandos especiales"""
        command_lower = command.lower().strip()
        
        # Comandos locales (no requieren servidor)
        if command_lower == '/help':
            return self.chat_view.get_help_message()
        elif command_lower == '/quit':
            return "👋 Cerrando cliente..."
        
        # Comandos que requieren servidor
        elif command_lower.startswith('/beauty') or command_lower.startswith('/palette'):
            return await self.handle_beauty_command(command)
        elif command_lower.startswith('/quotes'):
            return await self.handle_quotes_command(command)
        elif command_lower.startswith('/git') or command_lower.startswith('/fs'):
            return await self.handle_git_command(command)
        elif command_lower == '/stats':
            return await self.get_session_stats()
        elif command_lower == '/clear':
            return await self.clear_session()
        else:
            return f" Comando desconocido: {command}. Usa /help para ver comandos disponibles"
    
    async def handle_beauty_command(self, command: str) -> str:
        """Manejar comandos de belleza"""
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
                response = await self.client.get(f"{self.server_url}/beauty/profiles")
                response.raise_for_status()
                data = response.json()
                return self.beauty_view.show_profile_list(data["profiles"])
            
            elif action == "profile":
                if len(parts) < 3:
                    return " Especifica user_id. Uso: /beauty profile <user_id>"
                
                user_id = parts[2]
                response = await self.client.get(f"{self.server_url}/beauty/profile/{user_id}")
                if response.status_code == 404:
                    return f" Perfil '{user_id}' no encontrado"
                response.raise_for_status()
                
                profile_data = response.json()
                # Convertir a formato de perfil para la vista
                from models.beauty_model import BeautyProfile
                profile = BeautyProfile(**profile_data)
                return self.beauty_view.show_profile(profile)
            
            elif action == "history":
                if len(parts) < 3:
                    return " Especifica user_id. Uso: /beauty history <user_id>"
                
                user_id = parts[2]
                response = await self.client.get(f"{self.server_url}/beauty/history/{user_id}")
                response.raise_for_status()
                data = response.json()
                
                return f"📊 HISTORIAL DE {user_id.upper()}:\n\n" + \
                       f"Total de paletas: {data['total_palettes']}\n\n" + \
                       "\n".join([f"{i+1}. {p['palette_type']} - {p['event_type']} ({p['created_at'][:10]})" 
                                 for i, p in enumerate(data['palettes'][:10])])
            
            # Comandos de paleta
            elif command.startswith("/palette"):
                return await self.handle_palette_command(command)
            
            else:
                return f" Acción desconocida: {action}"
                
        except httpx.RequestError as e:
            return f" Error de conexión: {str(e)}"
        except httpx.HTTPStatusError as e:
            return f" Error del servidor: {e.response.status_code}"
        except Exception as e:
            return f" Error: {str(e)}"
    
    async def create_profile_interactive(self) -> str:
        """Crear perfil de forma interactiva"""
        try:
            # Recopilar datos usando la vista existente
            profile_data = self.beauty_view.collect_profile_data()
            
            if not profile_data:
                return " Creación de perfil cancelada"
            
            # Enviar al servidor
            response = await self.client.post(
                f"{self.server_url}/beauty/profile",
                json=profile_data
            )
            response.raise_for_status()
            
            result = response.json()
            if result["success"]:
                return f"✅ Perfil creado exitosamente!\n\n" + \
                       f"🆔 User ID: {result['profile']['user_id']}\n" + \
                       f"👤 Nombre: {result['profile']['name']}\n" + \
                       f"📅 Creado: {result['profile']['created_at'][:19]}\n\n" + \
                       "💄 Ahora puedes generar paletas con /palette"
            else:
                return f" Error creando perfil: {result.get('error', 'Error desconocido')}"
                
        except Exception as e:
            return f" Error: {str(e)}"
    
    async def handle_palette_command(self, command: str) -> str:
        """Manejar generación de paletas"""
        try:
            parts = command.strip().split()
            
            if len(parts) < 4:
                return " Uso: /palette <tipo> <user_id> <evento>\nTipos: ropa, maquillaje, accesorios"
            
            palette_type = parts[1].lower()
            user_id = parts[2]
            event_type = parts[3] if len(parts) > 3 else "casual"
            
            if palette_type not in ["ropa", "maquillaje", "accesorios"]:
                return " Tipo no válido. Opciones: ropa, maquillaje, accesorios"
            
            # Recopilar preferencias adicionales
            preferences = self.beauty_view.collect_palette_preferences(palette_type, event_type)
            
            # Enviar al servidor
            response = await self.client.post(
                f"{self.server_url}/beauty/palette",
                json={
                    "user_id": user_id,
                    "palette_type": palette_type,
                    "event_type": event_type,
                    "preferences": preferences
                }
            )
            
            if response.status_code == 404:
                return f" Perfil '{user_id}' no encontrado"
            
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                # Mostrar paleta usando la vista existente
                from models.beauty_model import ColorPalette
                palette = ColorPalette(**result["palette"])
                return self.beauty_view.show_palette(palette)
            else:
                return f" Error generando paleta: {result.get('error', 'Error desconocido')}"
                
        except Exception as e:
            return f" Error: {str(e)}"
    
    async def handle_quotes_command(self, command: str) -> str:
        """Manejar comandos de citas"""
        try:
            parts = command.strip().split()
            if len(parts) < 2:
                return " Uso: /quotes <acción> [parámetros]"
            
            action = parts[1].lower()
            
            if action == "get":
                category = parts[2] if len(parts) > 2 else None
                params = {"category": category} if category else {}
                
                response = await self.client.get(f"{self.server_url}/quotes/get", params=params)
                response.raise_for_status()
                data = response.json()
                return data["quote"]
            
            elif action == "search":
                if len(parts) < 3:
                    return " Uso: /quotes search <término>"
                
                query = " ".join(parts[2:])
                response = await self.client.get(f"{self.server_url}/quotes/search/{query}")
                response.raise_for_status()
                data = response.json()
                return data["results"]
            
            elif action == "wisdom":
                response = await self.client.get(f"{self.server_url}/quotes/wisdom")
                response.raise_for_status()
                data = response.json()
                return data["wisdom"]
            
            else:
                return " Acciones disponibles: get, search, wisdom"
                
        except Exception as e:
            return f" Error: {str(e)}"
    
    async def handle_git_command(self, command: str) -> str:
        """Manejar comandos de git"""
        try:
            response = await self.client.post(
                f"{self.server_url}/git/command",
                json={"command": command}
            )
            response.raise_for_status()
            data = response.json()
            return data["result"]
            
        except Exception as e:
            return f" Error: {str(e)}"
    
    async def get_session_stats(self) -> str:
        """Obtener estadísticas de sesión"""
        try:
            response = await self.client.get(f"{self.server_url}/sessions/{self.session_id}/stats")
            if response.status_code == 404:
                return " No hay estadísticas de sesión disponibles"
            
            response.raise_for_status()
            stats = response.json()
            
            return f"""📊 ESTADÍSTICAS DE SESIÓN:
💬 Total mensajes: {stats['total_messages']}
👤 Mensajes usuario: {stats['user_messages']}  
🤖 Mensajes asistente: {stats['assistant_messages']}
⏱️ Duración: {stats['session_duration']}
🧠 Mensajes en contexto: {stats['messages_in_context']}"""
            
        except Exception as e:
            return f" Error obteniendo estadísticas: {str(e)}"
    
    async def clear_session(self) -> str:
        """Limpiar contexto de sesión"""
        try:
            response = await self.client.post(f"{self.server_url}/sessions/{self.session_id}/clear")
            response.raise_for_status()
            return "🧹 Contexto de sesión limpiado"
            
        except Exception as e:
            return f" Error limpiando sesión: {str(e)}"
    
    async def cleanup(self):
        """Limpiar recursos del cliente"""
        if self.client:
            await self.client.aclose()
        print("🧹 Cliente desconectado")

def show_banner():
    """Mostrar banner del cliente"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                     MCPChatbot Cliente                       ║
║              Conectando a Servidor Local                     ║
╠══════════════════════════════════════════════════════════════╣
║  🔗 Modo Cliente-Servidor                                    ║
║  🤖 Claude API via Servidor                                  ║
║  💄 Sistema de Belleza Remoto                                ║
║  🌐 Citas Inspiracionales                                    ║
║  📁 Gestión de Archivos                                      ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

async def main():
    """Función principal del cliente"""
    show_banner()
    
    try:
        # Inicializar cliente
        client = RemoteClient()
        
        if await client.initialize():
            await client.run_interactive_mode()
        else:
            print("\n No se pudo conectar al servidor")
            print("💡 Primero ejecuta: python3 server_local.py")
            
    except KeyboardInterrupt:
        print("\n👋 Cliente interrumpido por el usuario")
    except Exception as e:
        print(f" Error inesperado: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())