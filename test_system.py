#!/usr/bin/env python3
"""
Sistema de pruebas para el proyecto de belleza MCP
Versión actualizada para la nueva estructura de archivos
"""

import asyncio
import sys
import os
import json
import subprocess
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_file_structure():
    """Verificar estructura de archivos"""
    print("📂 Verificando estructura de archivos...")
    
    required_structure = {
        "directorios": [
            "Data",
            "Servidores", 
            "Servidores/Local",
            "Clientes"
        ],
        "archivos": [
            "Servidores/Local/beauty_server.py",
            "Servidores/Local/metodos_server.py",
            "Clientes/beauty_client.py", 
            "Clientes/beauty_client_hybrid.py",
            "Data/beauty_context.json",
            "beauty_servers.yaml",
            "requirements.txt",
            ".env"
        ]
    }
    
    missing = []
    
    # Verificar directorios
    for directory in required_structure["directorios"]:
        if os.path.exists(directory):
            print(f"✅ Directorio: {directory}")
        else:
            print(f"❌ FALTA: {directory}")
            missing.append(directory)
    
    # Verificar archivos
    for archivo in required_structure["archivos"]:
        if os.path.exists(archivo):
            print(f"✅ Archivo: {archivo}")
        else:
            print(f"❌ FALTA: {archivo}")
            missing.append(archivo)
    
    return len(missing) == 0

def test_imports():
    """Probar imports y dependencias"""
    print("📦 Verificando dependencias...")
    
    required_modules = [
        ("mcp.server", "mcp"),
        ("anthropic", "anthropic"),
        ("dotenv", "python-dotenv"),
        ("prompt_toolkit", "prompt-toolkit"),
        ("yaml", "PyYAML"),
        ("colorsys", "built-in"),
        ("json", "built-in"),
        ("os", "built-in")
    ]
    
    missing_modules = []
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            if package_name != "built-in":
                print(f"❌ FALTA: {package_name}")
                missing_modules.append(package_name)
            else:
                print(f"❌ PROBLEMA: {module_name}")
    
    if missing_modules:
        print(f"\n Instala módulos faltantes:")
        print(f"   pip install {' '.join(missing_modules)}")
        return False
    
    return True

async def test_metodos_server():
    """Probar que metodos_server funcione correctamente"""
    print("🔬 Probando sistema de colorimetría...")
    
    try:
        # Import con nueva estructura
        sys.path.insert(0, "Servidores/Local")
        import metodos_server
        
        # Inicializar almacenamiento
        metodos_server.init_data_storage()
        print("✅ metodos_server.py importado correctamente")
        
        # Probar análisis de subtono
        undertone_analysis = metodos_server.ColorAnalyzer.analyze_undertone(
            vein_color="azul",
            jewelry_preference="plata",
            sun_reaction="se_quema", 
            natural_lip_color="rosado"
        )
        
        if undertone_analysis.get("undertone") == "frio":
            print("✅ Análisis de subtono funciona")
        else:
            print(f"❌ Error en análisis de subtono: {undertone_analysis}")
            return False
        
        # Probar determinación de estación
        season_analysis = metodos_server.ColorAnalyzer.determine_season(
            skin_tone="clara",
            undertone="frio",
            eye_color="azul", 
            hair_color="rubio",
            contrast_level="bajo"
        )
        
        if "season" in season_analysis:
            print(f"✅ Análisis de estación: {season_analysis['season_info']['name']}")
        else:
            print(f"❌ Error en análisis de estación")
            return False
        
        # Probar perfil completo
        test_profile = {
            "user_id": "test_advanced",
            "name": "Usuario de Prueba",
            "skin_tone": "clara",
            "vein_color": "azul",
            "jewelry_preference": "plata",
            "sun_reaction": "se_quema",
            "eye_color": "azul",
            "hair_color": "rubio", 
            "natural_lip_color": "rosado",
            "contrast_level": "bajo"
        }
        
        result = metodos_server.tool_create_profile(test_profile)
        if result.get("success"):
            print("✅ Creación de perfil funciona")
            print(f"   Estación: {result['color_analysis_summary']['estacion']}")
            print(f"   Subtono: {result['color_analysis_summary']['subtono']}")
            
            # Limpiar datos de prueba
            metodos_server.tool_delete_profile({"user_id": "test_advanced"})
        else:
            print(f"❌ Error creando perfil: {result.get('error', 'Desconocido')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando metodos_server: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_config():
    """Verificar configuración de .env"""
    print("  Verificando configuración...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            print("❌ ANTHROPIC_API_KEY no encontrada en .env")
            return False
        elif not api_key.startswith("sk-ant-"):
            print("❌ ANTHROPIC_API_KEY parece inválida")
            return False
        else:
            print("✅ ANTHROPIC_API_KEY configurada")
            return True
            
    except Exception as e:
        print(f"❌ Error verificando .env: {e}")
        return False

async def test_server_startup():
    """Probar que el servidor MCP se pueda iniciar"""
    print("  Probando inicio de servidor MCP...")
    
    try:
        # Intentar iniciar el servidor brevemente
        process = await asyncio.create_subprocess_exec(
            sys.executable, "Servidores/Local/beauty_server.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Esperar un momento para ver si se inicia
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print("✅ Servidor MCP se inició correctamente")
                return True
            else:
                print(f"❌ Servidor falló con código: {process.returncode}")
                if stderr:
                    print(f"   Error: {stderr.decode()}")
                return False
                
        except asyncio.TimeoutError:
            # El servidor sigue corriendo, eso es bueno
            process.terminate()
            await process.wait()
            print("✅ Servidor MCP se inició (terminado manualmente)")
            return True
            
    except Exception as e:
        print(f"❌ Error probando servidor: {e}")
        return False

async def main():
    """Función principal de pruebas"""
    print("🧪 SISTEMA DE PRUEBAS - BELLEZA MCP")
    print("=" * 60)
    print("Verificando que todos los componentes funcionen correctamente")
    print("=" * 60)
    
    tests = [
        ("Estructura de Archivos", test_file_structure),
        ("Dependencias", test_imports), 
        ("Configuración .env", test_env_config),
        ("Sistema de Colorimetría", test_metodos_server),
        ("Servidor MCP", test_server_startup)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n {test_name}:")
        print("-" * 30)
        
        if asyncio.iscoroutinefunction(test_func):
            passed = await test_func()
        else:
            passed = test_func()
        
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("\n🚀 Sistema listo para usar:")
        print("   • Análisis científico de subtono")
        print("   • Sistema de 8 estaciones de color")
        print("   • Generación de paletas avanzadas")
        print("   • Servidor MCP funcional")
        print("\n Para empezar:")
        print("   python Clientes/beauty_client.py")
        print("   python Clientes/beauty_client_hybrid.py")
        
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("\n Soluciones sugeridas:")
        print("   1. Ejecutar: python setup_project.py")
        print("   2. Instalar dependencias: pip install -r requirements.txt") 
        print("   3. Verificar archivo .env con tu API key")
        print("   4. Volver a ejecutar: python test_system.py")

if __name__ == "__main__":
    asyncio.run(main())