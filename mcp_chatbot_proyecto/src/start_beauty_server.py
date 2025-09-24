#!/usr/bin/env python3
"""
Startup script para Beauty Palette MCP Server Local
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    server_script = script_dir / "beauty_mcp_server_local.py"
    
    if not server_script.exists():
        print("❌ No se encuentra beauty_mcp_server_local.py")
        return
    
    print(" Iniciando Beauty Palette MCP Server Local...")
    
    try:
        subprocess.run([sys.executable, str(server_script)], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando servidor: {e}")

if __name__ == "__main__":
    main()
