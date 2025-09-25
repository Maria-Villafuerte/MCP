#!/usr/bin/env python3
"""
Script de configuración inicial para el Sistema de Belleza MCP
Corrige automáticamente la estructura de archivos y configuraciones
"""

import os
import json
import yaml
from datetime import datetime

def create_directory_structure():
    """Crear estructura de directorios necesaria"""
    directories = [
        "Data",
        "Servidores",
        "Servidores/Local",
        "Clientes", 
        "Remotos",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directorio: {directory}")

def create_init_files():
    """Crear archivos __init__.py para paquetes Python"""
    init_files = {
        "Servidores/__init__.py": '"""Paquete de servidores MCP"""',
        "Servidores/Local/__init__.py": '"""Servidores MCP locales"""',
        "Clientes/__init__.py": '"""Clientes del sistema de belleza"""',
        "Data/__init__.py": '"""Almacenamiento de datos"""',
    }
    
    for file_path, content in init_files.items():
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content + '\n')
        print(f"✅ Creado: {file_path}")

def initialize_beauty_context():
    """Inicializar archivo de contexto de belleza"""
    context_file = "Data/beauty_context.json"
    
    context_data = {
        "server": "beauty_server",
        "mode": "auto",
        "history": [],
        "last_tool_memory": {},
        "last_list": None,
        "session_info": {
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "total_interactions": 0
        },
        "user_preferences": {
            "language": "es",
            "verbose_output": True,
            "auto_save": True
        }
    }
    
    with open(context_file, 'w', encoding='utf-8') as f:
        json.dump(context_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Contexto inicializado: {context_file}")

def create_beauty_servers_config():
    """Crear configuración actualizada de servidores"""
    config = {
        "connection_mode": "auto",
        "servers": {
            "beauty_server": {
                "command": "python",
                "args": ["Servidores/Local/beauty_server.py"],
                "env": {},
                "cwd": "."
            }
        },
        "remote_server": {
            "url": "https://beauty-pallet-server.railway.app",
            "timeout": 30,
            "backup_url": "http://localhost:8000"
        },
        "client_settings": {
            "max_retries": 3,
            "auto_switch_on_error": True,
            "preferred_mode": "auto"
        },
        "logging": {
            "enabled": True,
            "file": "Data/beauty_log.txt",
            "level": "info"
        },
        "context": {
            "file": "Data/beauty_context.json",
            "max_history": 100,
            "save_conversations": True
        }
    }
    
    with open("beauty_servers.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    print("✅ Configuración de servidores actualizada")

def check_env_file():
    """Verificar archivo .env"""
    if not os.path.exists('.env'):
        print("⚠️  Archivo .env no encontrado")
        print("   Crea un archivo .env con:")
        print("   ANTHROPIC_API_KEY=tu_api_key_aqui")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
        if 'ANTHROPIC_API_KEY' not in content:
            print("⚠️  ANTHROPIC_API_KEY no encontrada en .env")
            return False
    
    print("✅ Archivo .env configurado correctamente")
    return True

def verify_main_files():
    """Verificar que los archivos principales existan"""
    required_files = [
        "Servidores/Local/beauty_server.py",
        "Servidores/Local/metodos_server.py",
        "Clientes/beauty_client.py",
        "Clientes/beauty_client_hybrid.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ FALTA: {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def main():
    """Función principal de configuración"""
    print(" CONFIGURACIÓN INICIAL - SISTEMA DE BELLEZA MCP")
    print("=" * 60)
    
    print("\n1. Creando estructura de directorios...")
    create_directory_structure()
    
    print("\n2. Creando archivos __init__.py...")
    create_init_files()
    
    print("\n3. Inicializando contexto de belleza...")
    initialize_beauty_context()
    
    print("\n4. Creando configuración de servidores...")
    create_beauty_servers_config()
    
    print("\n5. Verificando archivo .env...")
    env_ok = check_env_file()
    
    print("\n6. Verificando archivos principales...")
    files_ok = verify_main_files()
    
    print("\n" + "=" * 60)
    if env_ok and files_ok:
        print("🎉 ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!")
        print("\n📋 Próximos pasos:")
        print("   1. python -m pip install -r requirements.txt")
        print("   2. python Clientes/beauty_client.py")
        print("   3. O usa: python Clientes/beauty_client_hybrid.py")
    else:
        print("⚠️  Configuración completada con advertencias")
        print("   Revisa los archivos faltantes o la configuración de .env")
    
    print("\n Para probar el sistema:")
    print("   python test_system.py")

if __name__ == "__main__":
    main()