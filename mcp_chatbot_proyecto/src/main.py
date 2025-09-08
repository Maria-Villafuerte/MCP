import os
import json
import asyncio
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from dotenv import load_dotenv
import tempfile
import shutil

# Cargar variables de entorno
load_dotenv()

class MCPChatbot:
    def __init__(self):
        """Inicializar el chatbot con conexión a Claude API y servidores MCP"""
        # Configurar cliente de Anthropic
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada en variables de entorno")
        
        self.client = Anthropic(api_key=api_key)
        
        # Historial de conversación para mantener contexto
        self.conversation_history: List[Dict[str, str]] = []
        
        # Log de interacciones MCP
        self.mcp_log: List[Dict[str, Any]] = []
        
        # Configurar directorio de trabajo
        self.working_dir = os.path.join(os.getcwd(), "mcp_workspace")
        os.makedirs(self.working_dir, exist_ok=True)
        
        print("✅ MCPChatbot inicializado correctamente")
        print("📱 Conectado a Claude API")
        print("💾 Sistema de logging MCP activado")
        print(f"📁 Directorio de trabajo: {self.working_dir}")
    
    def log_mcp_interaction(self, interaction_type: str, server_name: str, 
                           request: Any, response: Any):
        """Registrar interacciones con servidores MCP"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "server": server_name,
            "request": str(request),
            "response": str(response)
        }
        self.mcp_log.append(log_entry)
        print(f"📝 [MCP LOG] {interaction_type} con {server_name}")
    
    def add_to_conversation(self, role: str, content: str):
        """Agregar mensaje al historial de conversación"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    # ============= FILESYSTEM MCP FUNCTIONS =============
    
    def mcp_read_file(self, file_path: str) -> str:
       
    
    def mcp_write_file(self, file_path: str, content: str) -> str:
        
    def mcp_list_directory(self, dir_path: str = ".") -> str:
       

    def send_message(self, user_message: str) -> str:
        """Enviar mensaje a Claude con capacidades MCP"""
        try:
            # Detectar si el usuario quiere usar funciones MCP
            response_text = self._process_mcp_commands(user_message)
            
            if response_text:
                return response_text
            
            # Si no es un comando MCP, enviar a Claude normalmente
            self.add_to_conversation("user", user_message)
            
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system="""Eres un asistente especializado en belleza, moda y tecnología. Tienes acceso a herramientas MCP para:
                - Gestionar archivos (leer, escribir, listar)
                - Usar Git (init, add, commit)
                - Generar paletas de colores personalizadas

                Cuando el usuario mencione archivos, repositorios o paletas de colores, sugiere usar las funciones MCP correspondientes.""",
                messages=self.conversation_history
            )
            
            assistant_response = response.content[0].text
            self.add_to_conversation("assistant", assistant_response)
            
            return assistant_response
            
        except Exception as e:
            return f"❌ Error al comunicarse con Claude: {str(e)}"
    
    def _process_mcp_commands(self, message: str) -> Optional[str]:
        """Procesar comandos MCP específicos"""
        msg_lower = message.lower()
        
        # Comando para generar paleta
        if "paleta" in msg_lower or "colores" in msg_lower:
            if "generar" in msg_lower or "crear" in msg_lower:
                return """🎨 Para generar una paleta personalizada, usa el comando:

/palette [tono_piel] [color_ojos] [color_cabello] [tono_labios] [evento] [estacion] [estilo]

Ejemplo:
/palette clara azul rubio rosa casual verano elegante

Opciones disponibles:
- Tono de piel: clara, media, oscura
- Color de ojos: azul, verde, cafe, gris
- Color de cabello: rubio, castano, negro, rojo
- Evento: casual, formal, fiesta, trabajo
- Estación: primavera, verano, otoño, invierno
"""
        
        # Comando específico de paleta
        if message.startswith("/palette "):
            params = message[9:].split()
            if len(params) >= 7:
                return self.mcp_generate_color_palette(params[0], params[1], params[2], 
                                                     params[3], params[4], params[5], params[6])
            else:
                return "❌ Faltan parámetros. Usa: /palette [tono_piel] [color_ojos] [color_cabello] [tono_labios] [evento] [estacion] [estilo]"
        
        # Comandos de archivos
        if message.startswith("/read "):
            file_path = message[6:]
            return self.mcp_read_file(file_path)
        
        if message.startswith("/write "):
            parts = message[7:].split(" ", 1)
            if len(parts) >= 2:
                return self.mcp_write_file(parts[0], parts[1])
            else:
                return "❌ Uso: /write [archivo] [contenido]"
        
        if message.startswith("/ls"):
            path = message[3:].strip() or "."
            return self.mcp_list_directory(path)
        
        # Comandos Git
        if message.startswith("/git_init "):
            repo_name = message[10:]
            return self.mcp_git_init(repo_name)
        
        if message.startswith("/git_add "):
            parts = message[9:].split(" ", 1)
            if len(parts) >= 2:
                return self.mcp_git_add(parts[0], parts[1])
            else:
                return "❌ Uso: /git_add [repo] [archivo]"
        
        if message.startswith("/git_commit "):
            parts = message[12:].split(" ", 1)
            if len(parts) >= 2:
                return self.mcp_git_commit(parts[0], parts[1])
            else:
                return "❌ Uso: /git_commit [repo] [mensaje]"
        
        return None
    
    def show_mcp_log(self):
        """Mostrar log de interacciones MCP"""
        if not self.mcp_log:
            print("📋 No hay interacciones MCP registradas aún")
            return
        
        print("\n" + "="*50)
        print("📋 LOG DE INTERACCIONES MCP")
        print("="*50)
        
        for i, entry in enumerate(self.mcp_log, 1):
            print(f"\n{i}. [{entry['timestamp']}]")
            print(f"   Tipo: {entry['type']}")
            print(f"   Servidor: {entry['server']}")
            print(f"   Request: {entry['request']}")
            print(f"   Response: {entry['response'][:100]}..." if len(entry['response']) > 100 else f"   Response: {entry['response']}")
    
    def show_help(self):
        """Mostrar comandos disponibles"""
        help_text = """
🤖 COMANDOS MCP DISPONIBLES:

📁 FILESYSTEM:
  /read [archivo]              - Leer archivo
  /write [archivo] [contenido] - Escribir archivo
  /ls [directorio]            - Listar directorio

🔧 GIT:
  /git_init [repo]            - Inicializar repositorio
  /git_add [repo] [archivo]   - Agregar archivo
  /git_commit [repo] [msg]    - Hacer commit

🎨 PALETAS DE COLORES:
  /palette [tono_piel] [color_ojos] [color_cabello] [tono_labios] [evento] [estacion] [estilo]

📋 SISTEMA:
  /log    - Ver log MCP
  /help   - Mostrar esta ayuda
  /clear  - Limpiar contexto
  /quit   - Salir

💡 EJEMPLO COMPLETO:
  /git_init mi_proyecto
  /write mi_proyecto/README.md "# Mi Proyecto"
  /git_add mi_proyecto README.md
  /git_commit mi_proyecto "Primer commit"
  /palette clara azul rubio rosa casual verano elegante
"""
        print(help_text)
    
    def clear_context(self):
        """Limpiar contexto de conversación"""
        self.conversation_history.clear()
        print("🔄 Contexto de conversación limpiado")
    
    def run_interactive_mode(self):
        """Ejecutar modo interactivo del chatbot"""
        print("\n🤖 MCPChatbot - Modo Interactivo con MCP")
        print("Escribe /help para ver todos los comandos disponibles")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n👤 Tú: ").strip()
                
                if user_input.lower() == '/quit':
                    print("👋 ¡Hasta luego!")
                    break
                elif user_input.lower() == '/log':
                    self.show_mcp_log()
                    continue
                elif user_input.lower() == '/help':
                    self.show_help()
                    continue
                elif user_input.lower() == '/clear':
                    self.clear_context()
                    continue
                elif not user_input:
                    continue
                
                # Procesar mensaje
                response = self.send_message(user_input)
                print(f"\n🤖 Claude: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    if not os.path.exists('.env'):
        print("📝 Creando archivo .env...")
        with open('.env', 'w') as f:
            f.write("ANTHROPIC_API_KEY=tu_api_key_aqui\n")
        print("⚠️  Por favor, edita el archivo .env y agrega tu API key de Anthropic")
        exit(1)
    
    try:
        chatbot = MCPChatbot()
        chatbot.run_interactive_mode()
    except Exception as e:
        print(f"❌ Error al inicializar: {e}")
        print("💡 Asegúrate de que tu API key esté configurada en el archivo .env")