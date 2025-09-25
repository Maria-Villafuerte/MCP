#!/usr/bin/env python3
"""
Script de prueba para verificar que el servidor avanzado de belleza funcione correctamente
Incluye pruebas para el sistema de colorimetría profesional
Version sin caracteres especiales para Windows
"""

import asyncio
import subprocess
import sys
import os
import json

async def test_metodos_server():
    """Probar que metodos_server.py funcione correctamente con análisis avanzado"""
    print("Probando sistema avanzado de colorimetría...")
    
    try:
        # Importar metodos_server
        from Servidores.Local import metodos_server
        
        # Inicializar almacenamiento
        metodos_server.init_data_storage()
        print("OK metodos_server.py importado correctamente")
        
        # Probar análisis de subtono
        undertone_analysis = metodos_server.ColorAnalyzer.analyze_undertone(
            vein_color="azul",
            jewelry_preference="plata", 
            sun_reaction="se_quema",
            natural_lip_color="rosado"
        )
        
        if undertone_analysis.get("undertone") == "frio":
            print("OK Análisis de subtono funciona correctamente")
        else:
            print(f"ERROR Análisis de subtono: {undertone_analysis}")
        
        # Probar determinación de estación
        season_analysis = metodos_server.ColorAnalyzer.determine_season(
            skin_tone="clara",
            undertone="frio",
            eye_color="azul",
            hair_color="rubio",
            contrast_level="bajo"
        )
        
        if "season" in season_analysis:
            print(f"OK Análisis de estación: {season_analysis['season_info']['name']}")
        else:
            print(f"ERROR Análisis de estación: {season_analysis}")
        
        # Probar crear perfil avanzado
        test_profile = {
            "user_id": "test_advanced",
            "name": "Usuario de Prueba Avanzado",
            "skin_tone": "clara",
            "vein_color": "azul",
            "jewelry_preference": "plata",
            "sun_reaction": "se_quema",
            "eye_color": "azul",
            "hair_color": "rubio",
            "natural_lip_color": "rosado",
            "contrast_level": "bajo",
            "style_preference": "clasico"
        }
        
        result = metodos_server.tool_create_profile(test_profile)
        if result.get("success"):
            print("OK Función create_profile avanzada funciona correctamente")
            print(f"   Estación detectada: {result['color_analysis_summary']['estacion']}")
            print(f"   Subtono: {result['color_analysis_summary']['subtono']}")
            print(f"   Confianza: {result['color_analysis_summary']['confianza_subtono']}")
        else:
            print(f"ERROR en create_profile avanzado: {result.get('error', 'Desconocido')}")
            
        # Probar generación de paleta
        palette_result = metodos_server.tool_generate_palette({
            "user_id": "test_advanced",
            "palette_type": "maquillaje",
            "event_type": "formal"
        })
        
        if palette_result.get("success"):
            print("OK Generación de paleta avanzada funciona correctamente")
        else:
            print(f"ERROR en generación de paleta: {palette_result.get('error', 'Desconocido')}")
            
        # Limpiar datos de prueba
        metodos_server.tool_delete_profile({"user_id": "test_advanced"})
        
        return True
        
    except Exception as e:
        print(f"ERROR probando metodos_server.py avanzado: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Probar que todas las importaciones funcionen incluyendo nuevas dependencias"""
    print("Verificando dependencias del sistema avanzado...")
    
    required_modules = [
        ("mcp.server", "mcp"),
        ("anthropic", "anthropic"),
        ("dotenv", "python-dotenv"),
        ("prompt_toolkit", "prompt-toolkit"),
        ("yaml", "PyYAML"),
        ("colorsys", "built-in"),  # Biblioteca estándar de Python
        ("math", "built-in")       # Biblioteca estándar de Python
    ]
    
    missing_modules = []
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"OK {package_name}")
        except ImportError:
            if package_name != "built-in":
                print(f"ERROR {package_name} - FALTANTE")
                missing_modules.append(package_name)
            else:
                print(f"ERROR {module_name} - PROBLEMA CON BIBLIOTECA ESTÁNDAR")
    
    if missing_modules:
        print(f"\nInstala los módulos faltantes con:")
        print(f"   pip install {' '.join(missing_modules)}")
        return False
    
    return True

def test_files():
    """Verificar que todos los archivos necesarios existan"""
    print("Verificando archivos del sistema avanzado...")
    
    required_files = [
        "./Servidores/Local/beauty_server.py",
        "./Servidores/Local/metodos_server.py",
        "./Clientes/beauty_client.py",
        ".env"
    ]
    
    missing_files = []
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"OK {file_name}")
        else:
            print(f"ERROR {file_name} - FALTANTE")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\nArchivos faltantes:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    return True

def test_env():
    """Verificar configuración del .env"""
    print("Verificando configuración...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            print("ERROR ANTHROPIC_API_KEY no encontrada en .env")
            print("Agrega tu API key al archivo .env:")
            print("   ANTHROPIC_API_KEY=tu_api_key_aqui")
            return False
        elif not api_key.startswith("sk-ant-"):
            print("ERROR ANTHROPIC_API_KEY parece no ser válida")
            print("Verifica que tu API key comience con 'sk-ant-'")
            return False
        else:
            print("OK ANTHROPIC_API_KEY configurada")
            return True
            
    except Exception as e:
        print(f"ERROR verificando .env: {e}")
        return False

async def test_server():
    """Probar que el servidor MCP avanzado se pueda iniciar"""
    print("Probando servidor MCP avanzado...")
    
    try:
        # Intentar iniciar el servidor por unos segundos
        process = await asyncio.create_subprocess_exec(
            sys.executable, "beauty_server.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Esperar un poco para ver si se inicia
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print("OK Servidor MCP avanzado se inició correctamente")
                return True
            else:
                print(f"ERROR Servidor falló con código: {process.returncode}")
                if stderr:
                    print(f"   Error: {stderr.decode()}")
                return False
                
        except asyncio.TimeoutError:
            # El servidor sigue corriendo, eso es bueno
            process.terminate()
            await process.wait()
            print("OK Servidor MCP avanzado se inició (proceso terminado manualmente)")
            return True
            
    except Exception as e:
        print(f"ERROR probando servidor avanzado: {e}")
        return False

def test_color_theory():
    """Probar funcionalidades específicas de teoría del color"""
    print("Probando teoría del color...")
    
    try:
        import metodos_server
        
        # Probar generación de armonías
        base_colors = ["#FF6B35", "#4169E1"]
        harmony_colors = metodos_server.ColorAnalyzer.generate_harmony_palette(base_colors, "complementary")
        
        if len(harmony_colors) > 0:
            print("OK Generación de armonías de color funciona")
        else:
            print("ERROR Generación de armonías falló")
            
        # Probar todas las estaciones
        seasons_count = len(metodos_server.ColorAnalyzer.SEASONS)
        if seasons_count == 8:
            print(f"OK Sistema de 8 estaciones implementado correctamente")
            for season_key, season_info in metodos_server.ColorAnalyzer.SEASONS.items():
                if "best_colors" in season_info and len(season_info["best_colors"]) > 0:
                    continue
                else:
                    print(f"ERROR Estación {season_key} mal configurada")
                    return False
        else:
            print(f"ERROR Número incorrecto de estaciones: {seasons_count}, esperado: 8")
            return False
            
        return True
        
    except Exception as e:
        print(f"ERROR probando teoría del color: {e}")
        return False

def show_color_examples():
    """Mostrar ejemplos de análisis de color"""
    print("Ejemplos de análisis colorimétrico:")
    print("-" * 40)
    
    examples = [
        {
            "descripcion": "Persona con subtono frío",
            "caracteristicas": {
                "venas": "azul",
                "joyeria": "plata", 
                "sol": "se_quema",
                "labios": "rosado"
            },
            "resultado_esperado": "frio"
        },
        {
            "descripcion": "Persona con subtono cálido",
            "caracteristicas": {
                "venas": "verde",
                "joyeria": "oro",
                "sol": "broncea_facil", 
                "labios": "durazno"
            },
            "resultado_esperado": "calido"
        }
    ]
    
    try:
        import metodos_server
        
        for example in examples:
            print(f"\n{example['descripcion']}:")
            analysis = metodos_server.ColorAnalyzer.analyze_undertone(
                example['caracteristicas']['venas'],
                example['caracteristicas']['joyeria'],
                example['caracteristicas']['sol'],
                example['caracteristicas']['labios']
            )
            
            print(f"   Resultado: {analysis['undertone']}")
            print(f"   Confianza: {analysis['confidence']:.1f}%")
            print(f"   Esperado: {example['resultado_esperado']}")
            print(f"   ✓ Correcto" if analysis['undertone'] == example['resultado_esperado'] else "   ✗ Incorrecto")
    
    except Exception as e:
        print(f"ERROR mostrando ejemplos: {e}")

async def main():
    """Función principal de prueba del sistema avanzado"""
    print("DIAGNÓSTICO DEL SISTEMA AVANZADO DE COLORIMETRÍA")
    print("=" * 60)
    print("Sistema Profesional de Análisis de Belleza v2.0")
    print("Incluye 8 estaciones de color y análisis científico de subtono")
    print("=" * 60)
    
    tests = [
        ("Archivos", test_files),
        ("Dependencias", test_imports),
        ("Configuración", test_env),
        ("Teoría del Color", test_color_theory),
        ("Beauty Tools Avanzado", test_metodos_server),
        ("Servidor MCP Avanzado", test_server)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        
        if asyncio.iscoroutinefunction(test_func):
            passed = await test_func()
        else:
            passed = test_func()
        
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ TODAS LAS PRUEBAS DEL SISTEMA AVANZADO PASARON")
        print("\nCaracterísticas implementadas:")
        print("  • Análisis científico de subtono basado en 4 indicadores")
        print("  • Sistema de 8 estaciones de color profesional")
        print("  • Generación de paletas con teoría de armonías")
        print("  • Análisis de contraste personalizado")
        print("  • Recomendaciones específicas por tipo de evento")
        print("\nEjecuta: python beauty_client.py")
        
        # Mostrar ejemplos de análisis
        print("\n" + "=" * 60)
        show_color_examples()
        
    else:
        print("✗ ALGUNAS PRUEBAS FALLARON")
        print("Revisa los errores arriba y corrígelos")
        print("Una vez corregidos, vuelve a ejecutar este script")

if __name__ == "__main__":
    asyncio.run(main())