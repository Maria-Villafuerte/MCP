#!/usr/bin/env python3
"""
MCPChatbot - Sistema de Chat con MCP, Claude API y Belleza
Punto de entrada principal
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Agregar src al path para imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from controllers.main_controller import MainController

def check_environment():
    """Verificar configuración del entorno"""
    load_dotenv()
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print(" ANTHROPIC_API_KEY no encontrada")
        print(" Creando archivo .env...")
        
        with open('.env', 'w') as f:
            f.write("# Configuración de MCPChatbot\n")
            f.write("ANTHROPIC_API_KEY=tu_api_key_aqui\n")
            f.write("# Opcional: configurar modelo de Claude\n")
            f.write("CLAUDE_MODEL=claude-3-haiku-20240307\n")
        
        print("  Por favor, edita el archivo .env con tu API key de Anthropic")
        return False
    
    return True

def show_banner():
    """Mostrar banner de inicio"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                        MCPChatbot v2.0                      ║
║              Chat Inteligente con Sistema de Belleza        ║
╠══════════════════════════════════════════════════════════════╣
║   Claude API Integration                                   ║
║   Sistema de Paletas de Colores Avanzado                  ║
║   Recomendaciones de Belleza Personalizadas               ║
║   Gestión de Perfiles y Historial                         ║
║   Gestión de Archivos y Git                               ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

async def main():
    """Función principal"""
    show_banner()
    
    # Verificar entorno
    if not check_environment():
        return
    
    try:
        # Inicializar controlador principal
        print(" Inicializando sistema...")
        controller = MainController()
        
        if await controller.initialize():
            print(" Sistema inicializado correctamente")
            await controller.run_interactive_mode()
        else:
            print(" Error en la inicialización")
            
    except KeyboardInterrupt:
        print("\n Chatbot interrumpido por el usuario")
    except Exception as e:
        print(f" Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())