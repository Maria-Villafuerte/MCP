import os
import json
import asyncio
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
        """Leer archivo usando MCP Filesystem"""
        try:
            full_path = os.path.join(self.working_dir, file_path)
            
            if not os.path.exists(full_path):
                result = f"❌ Archivo no encontrado: {file_path}"
            else:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                result = f"✅ Contenido de {file_path}:\n{content}"
            
            self.log_mcp_interaction("READ_FILE", "filesystem", file_path, result)
            return result
            
        except Exception as e:
            error_msg = f"❌ Error leyendo archivo: {e}"
            self.log_mcp_interaction("READ_FILE", "filesystem", file_path, error_msg)
            return error_msg
    
    def mcp_write_file(self, file_path: str, content: str) -> str:
        """Escribir archivo usando MCP Filesystem"""
        try:
            full_path = os.path.join(self.working_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result = f"✅ Archivo creado/actualizado: {file_path}"
            self.log_mcp_interaction("WRITE_FILE", "filesystem", 
                                   {"path": file_path, "content_length": len(content)}, result)
            return result
            
        except Exception as e:
            error_msg = f"❌ Error escribiendo archivo: {e}"
            self.log_mcp_interaction("WRITE_FILE", "filesystem", file_path, error_msg)
            return error_msg
    
    def mcp_list_directory(self, dir_path: str = ".") -> str:
        """Listar directorio usando MCP Filesystem"""
        try:
            full_path = os.path.join(self.working_dir, dir_path)
            
            if not os.path.exists(full_path):
                result = f"❌ Directorio no encontrado: {dir_path}"
            else:
                items = os.listdir(full_path)
                result = f"✅ Contenido de {dir_path}:\n" + "\n".join(f"  - {item}" for item in items)
            
            self.log_mcp_interaction("LIST_DIR", "filesystem", dir_path, result)
            return result
            
        except Exception as e:
            error_msg = f"❌ Error listando directorio: {e}"
            self.log_mcp_interaction("LIST_DIR", "filesystem", dir_path, error_msg)
            return error_msg

    # ============= COLOR PALETTE MCP FUNCTIONS =============
    
    def mcp_generate_color_palette(self, skin_tone: str, eye_color: str, hair_color: str,
                                 lip_tone: str, event_type: str, season: str, style: str) -> str:
        """Generar paleta de colores personalizada para belleza"""
        try:
            # Base de datos de colores para diferentes características
            color_database = {
                "skin_tone": {
                    "clara": ["#F5E6D3", "#E8D4C2", "#F2E7D5"],
                    "media": ["#D4B896", "#C1A882", "#B8956A"],
                    "oscura": ["#8B5A3C", "#6B4423", "#4A2C17"]
                },
                "eye_color": {
                    "azul": ["#4A90E2", "#2E5BBA", "#1E3A8A"],
                    "verde": ["#10B981", "#059669", "#047857"],
                    "cafe": ["#92400E", "#B45309", "#D97706"],
                    "gris": ["#6B7280", "#4B5563", "#374151"]
                },
                "hair_color": {
                    "rubio": ["#F59E0B", "#EAB308", "#CA8A04"],
                    "castano": ["#92400E", "#B45309", "#D97706"],
                    "negro": ["#1F2937", "#111827", "#000000"],
                    "rojo": ["#DC2626", "#B91C1C", "#991B1B"]
                },
                "event_colors": {
                    "casual": ["#3B82F6", "#EF4444", "#10B981", "#F59E0B"],
                    "formal": ["#1F2937", "#374151", "#6B7280", "#9CA3AF"],
                    "fiesta": ["#EC4899", "#8B5CF6", "#06B6D4", "#F59E0B"],
                    "trabajo": ["#1E40AF", "#7C2D12", "#064E3B", "#92400E"]
                }
            }
            
            # Algoritmo de selección de colores
            selected_colors = []
            
            # Agregar colores base según características físicas
            if skin_tone.lower() in color_database["skin_tone"]:
                selected_colors.extend(color_database["skin_tone"][skin_tone.lower()][:1])
            
            if eye_color.lower() in color_database["eye_color"]:
                selected_colors.extend(color_database["eye_color"][eye_color.lower()][:1])
            
            # Agregar colores según el evento
            if event_type.lower() in color_database["event_colors"]:
                selected_colors.extend(color_database["event_colors"][event_type.lower()][:2])
            
            # Colores complementarios para pantalón y blusa
            pants_colors = ["#1F2937", "#374151", "#92400E", "#1E40AF"]  # Tonos neutros para pantalón
            blouse_colors = selected_colors + ["#F3F4F6", "#FEF3C7", "#DBEAFE"]  # Colores seleccionados + neutros
            
            # Crear resultado estructurado
            palette_result = {
                "input_parameters": {
                    "skin_tone": skin_tone,
                    "eye_color": eye_color,
                    "hair_color": hair_color,
                    "lip_tone": lip_tone,
                    "event_type": event_type,
                    "season": season,
                    "style": style
                },
                "recommended_pants": [
                    {"hex": pants_colors[0], "name": "Gris Carbón"},
                    {"hex": pants_colors[1], "name": "Gris Medio"},
                    {"hex": pants_colors[2], "name": "Café Chocolate"}
                ],
                "recommended_blouses": [
                    {"hex": blouse_colors[0], "name": "Color Principal"},
                    {"hex": blouse_colors[1] if len(blouse_colors) > 1 else "#F3F4F6", "name": "Color Complementario"},
                    {"hex": blouse_colors[2] if len(blouse_colors) > 2 else "#FEF3C7", "name": "Color Acento"}
                ]
            }
            
            result = f"""✅ PALETA DE COLORES GENERADA:

📋 Parámetros de entrada:
   👤 Tono de piel: {skin_tone}
   👁️  Color de ojos: {eye_color}
   💇 Color de cabello: {hair_color}
   💋 Tono de labios: {lip_tone}
   🎭 Tipo de evento: {event_type}
   🌞 Estación: {season}
   ✨ Estilo: {style}

👖 RECOMENDACIONES PARA PANTALÓN:
   1. {palette_result['recommended_pants'][0]['name']}: {palette_result['recommended_pants'][0]['hex']}
   2. {palette_result['recommended_pants'][1]['name']}: {palette_result['recommended_pants'][1]['hex']}
   3. {palette_result['recommended_pants'][2]['name']}: {palette_result['recommended_pants'][2]['hex']}

👚 RECOMENDACIONES PARA BLUSA:
   1. {palette_result['recommended_blouses'][0]['name']}: {palette_result['recommended_blouses'][0]['hex']}
   2. {palette_result['recommended_blouses'][1]['name']}: {palette_result['recommended_blouses'][1]['hex']}
   3. {palette_result['recommended_blouses'][2]['name']}: {palette_result['recommended_blouses'][2]['hex']}
"""
            
            self.log_mcp_interaction("GENERATE_PALETTE", "color_palette", palette_result["input_parameters"], result)
            return result
            
        except Exception as e:
            error_msg = f"❌ Error generando paleta: {e}"
            self.log_mcp_interaction("GENERATE_PALETTE", "color_palette", "error", error_msg)
            return error_msg
    
    # ============= CLAUDE INTEGRATION =============

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
                system="""Eres un asistente especializado en belleza, moda y gestión de archivos. Tienes acceso a herramientas MCP para:
                - Gestionar archivos (leer, escribir, listar)
                - Generar paletas de colores personalizadas

                Cuando el usuario mencione archivos o paletas de colores, sugiere usar las funciones MCP correspondientes.""",
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

🎨 PALETAS DE COLORES:
  /palette [tono_piel] [color_ojos] [color_cabello] [tono_labios] [evento] [estacion] [estilo]

📋 SISTEMA:
  /log    - Ver log MCP
  /help   - Mostrar esta ayuda
  /clear  - Limpiar contexto
  /quit   - Salir

💡 EJEMPLO COMPLETO:
  /write mi_archivo.txt "Contenido del archivo"
  /read mi_archivo.txt
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