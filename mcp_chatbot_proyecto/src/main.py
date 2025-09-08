import os
import json
from datetime import datetime
from typing import List, Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class MCPChatbot:
    def __init__(self):
        """Inicializar el chatbot con conexión a Claude API"""
        # Configurar cliente de Anthropic
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada en variables de entorno")
        
        self.client = Anthropic(api_key=api_key)
        
        # Historial de conversación para mantener contexto
        self.conversation_history: List[Dict[str, str]] = []
        
        # Log de interacciones MCP
        self.mcp_log: List[Dict[str, Any]] = []
        
        print("MCPChatbot inicializado correctamente")
        print("Conectado a Claude API")
        print("Sistema de logging MCP activado")
    
    def log_mcp_interaction(self, interaction_type: str, server_name: str, 
                           request: Any, response: Any):
        """Registrar interacciones con servidores MCP"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "server": server_name,
            "request": request,
            "response": response
        }
        self.mcp_log.append(log_entry)
        print(f"📝 [MCP LOG] {interaction_type} con {server_name}")
    
    def add_to_conversation(self, role: str, content: str):
        """Agregar mensaje al historial de conversación"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def send_message(self, user_message: str) -> str:
        """Enviar mensaje a Claude manteniendo contexto"""
        try:
            # Agregar mensaje del usuario al historial
            self.add_to_conversation("user", user_message)
            
            # Enviar a Claude con system prompt separado
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Modelo más económico para desarrollo
                max_tokens=1024,
                system="Eres un asistente útil especializado en belleza y moda. Mantén el contexto de la conversación y responde de manera clara y concisa.",
                messages=self.conversation_history
            )
            
            # Extraer respuesta
            assistant_response = response.content[0].text
            
            # Agregar respuesta al historial
            self.add_to_conversation("assistant", assistant_response)
            
            return assistant_response
            
        except Exception as e:
            return f"❌ Error al comunicarse con Claude: {str(e)}"
    
    def show_mcp_log(self):
        """Mostrar log de interacciones MCP"""
        if not self.mcp_log:
            print("No hay interacciones MCP registradas aún")
            return
        
        print("\n" + "="*50)
        print("LOG DE INTERACCIONES MCP")
        print("="*50)
        
        for i, entry in enumerate(self.mcp_log, 1):
            print(f"\n{i}. [{entry['timestamp']}]")
            print(f"   Tipo: {entry['type']}")
            print(f"   Servidor: {entry['server']}")
            print(f"   Request: {entry['request']}")
            print(f"   Response: {entry['response']}")
    
    def clear_context(self):
        """Limpiar contexto de conversación"""
        self.conversation_history.clear()
        print("🔄 Contexto de conversación limpiado")
    
    def run_interactive_mode(self):
        """Ejecutar modo interactivo del chatbot"""
        print("\nMCPChatbot - Modo Interactivo")
        print("Comandos especiales:")
        print("  /log - Mostrar log de interacciones MCP")
        print("  /clear - Limpiar contexto")
        print("  /quit - Salir")
        print("-" * 40)
        
        while True:
            try:
                user_input = input("\nTú: ").strip()
                
                if user_input.lower() == '/quit':
                    print("¡Hasta luego!")
                    break
                elif user_input.lower() == '/log':
                    self.show_mcp_log()
                    continue
                elif user_input.lower() == '/clear':
                    self.clear_context()
                    continue
                elif not user_input:
                    continue
                
                # Enviar mensaje a Claude
                response = self.send_message(user_input)
                print(f"\nClaude: {response}")
                
            except KeyboardInterrupt:
                print("\n¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    # Crear archivo .env si no existe
    if not os.path.exists('.env'):
        print("Creando archivo .env...")
        with open('.env', 'w') as f:
            f.write("ANTHROPIC_API_KEY=tu_api_key_aqui\n")
        print("Por favor, edita el archivo .env y agrega tu API key de Anthropic")
        exit(1)
    
    try:
        chatbot = MCPChatbot()
        chatbot.run_interactive_mode()
    except Exception as e:
        print(f"Error al inicializar: {e}")
        print("Asegúrate de que tu API key esté configurada en el archivo .env")