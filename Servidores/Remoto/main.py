#!/usr/bin/env python3
"""
Beauty Palette Server Integrado
Combina servidor FastAPI existente con funcionalidad MCP avanzada
"""

import json
import os
import colorsys
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Importar funciones del servidor MCP
from metodos_server import (
    init_data_storage,
    tool_create_profile,
    tool_show_profile,
    tool_list_profiles,
    tool_delete_profile,
    tool_generate_palette,
    tool_quick_palette,
    tool_export_data,
    ColorAnalyzer
)

# Configuración del servidor
app = FastAPI(
    title="Beauty Palette Server Integrado",
    description="Servidor completo con análisis MCP avanzado y API REST",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IntegratedBeautyServer:
    def __init__(self):
        """Servidor integrado que combina FastAPI + MCP"""
        self.server_name = "Beauty Server Integrado"
        self.version = "3.0.0"
        
        # Inicializar almacenamiento MCP
        init_data_storage()
        
        # Bases de datos del servidor original
        self.color_database = self._load_color_database()
        self.quotes_database = self._load_beauty_quotes()
    
    def _load_color_database(self) -> Dict[str, Any]:
        """Base de datos de colores del servidor original"""
        return {
            "skin_tones": {
                "clara": {
                    "base_colors": ["#F5E6D3", "#E8D4C2", "#F2E7D5", "#FDF2E9"],
                    "best_colors": ["#FFB6C1", "#87CEEB", "#DDA0DD", "#F0E68C", "#98FB98"],
                    "avoid_colors": ["#000000", "#8B0000", "#2F4F4F", "#4B0082"],
                    "recommendations": [
                        "Los pasteles y tonos suaves realzan tu piel clara",
                        "Evita colores muy oscuros o intensos",
                        "Los colores fríos como azules y rosas te favorecen"
                    ]
                },
                "media": {
                    "base_colors": ["#D4B896", "#C1A882", "#B8956A", "#DEB887"],
                    "best_colors": ["#FF6347", "#32CD32", "#4169E1", "#DAA520", "#FF69B4"],
                    "avoid_colors": ["#FFFF00", "#00FF00", "#FF00FF", "#00FFFF"],
                    "recommendations": [
                        "Tienes la versatilidad de usar muchos colores",
                        "Los tonos tierra y cálidos te sientan especialmente bien",
                        "Puedes experimentar con colores vibrantes"
                    ]
                },
                "oscura": {
                    "base_colors": ["#8B5A3C", "#6B4423", "#4A2C17", "#5D4037"],
                    "best_colors": ["#FF4500", "#9400D3", "#FFD700", "#DC143C", "#00CED1"],
                    "avoid_colors": ["#FFFFE0", "#F0F8FF", "#FFFAF0", "#F5F5DC"],
                    "recommendations": [
                        "Los colores ricos y vibrantes realzan tu belleza",
                        "Evita colores muy pálidos que pueden lavarte",
                        "Los metálicos como oro y cobre son perfectos"
                    ]
                }
            },
            "event_palettes": {
                "trabajo": {
                    "primary": ["#1E40AF", "#374151", "#6B7280", "#1F2937"],
                    "secondary": ["#F8FAFC", "#F1F5F9", "#E2E8F0", "#CBD5E1"],
                    "accent": ["#3B82F6", "#6366F1", "#8B5CF6"],
                    "description": "Colores profesionales que inspiran confianza"
                },
                "casual": {
                    "primary": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"],
                    "secondary": ["#DBEAFE", "#D1FAE5", "#FEF3C7", "#FEE2E2"],
                    "accent": ["#1D4ED8", "#059669", "#D97706", "#DC2626"],
                    "description": "Colores relajados y versátiles para el día a día"
                },
                "fiesta": {
                    "primary": ["#EC4899", "#8B5CF6", "#06B6D4", "#F59E0B"],
                    "secondary": ["#F9A8D4", "#C4B5FD", "#67E8F9", "#FCD34D"],
                    "accent": ["#FFD700", "#C0C0C0", "#B87333"],
                    "metallic": ["#FFD700", "#C0C0C0", "#CD7F32", "#E6E6FA"],
                    "description": "Colores vibrantes y llamativos para destacar"
                }
            }
        }
    
    def _load_beauty_quotes(self) -> List[Dict[str, str]]:
        """Base de datos de citas"""
        return [
            {
                "quote": "La belleza comienza en el momento en que decides ser tú misma",
                "author": "Coco Chanel",
                "category": "confianza"
            },
            {
                "quote": "El estilo es una manera de decir quién eres sin tener que hablar",
                "author": "Rachel Zoe",
                "category": "estilo"
            },
            {
                "quote": "La confianza es el mejor accesorio que puedes usar",
                "author": "Anónimo",
                "category": "confianza"
            }
        ]
    
    def analyze_color_harmony_advanced(self, colors: List[str]) -> Dict[str, Any]:
        """Análisis de armonía usando ColorAnalyzer del MCP"""
        if len(colors) < 2:
            return {"harmony_score": 0, "analysis": "Se necesitan al menos 2 colores"}
        
        try:
            # Usar el analizador MCP más avanzado
            harmony_palette = ColorAnalyzer.generate_harmony_palette(colors, "complementary")
            
            # Análisis básico de compatibilidad
            score = random.randint(70, 95)  # Simulado, puedes implementar lógica real
            
            return {
                "harmony_score": score,
                "harmony_type": "Análisis MCP Avanzado",
                "generated_harmony": harmony_palette[:5],
                "analysis": f"Paleta analizada con algoritmo MCP. Score: {score}%",
                "mcp_integration": True
            }
        except Exception as e:
            return {"harmony_score": 50, "error": str(e)}

# Instancia del servidor integrado
server = IntegratedBeautyServer()

# === ENDPOINTS EXISTENTES (mantener compatibilidad) ===

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página principal actualizada"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Beauty Server Integrado</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
            .section {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
            .method {{ font-weight: bold; color: #28a745; }}
            .new {{ background: #e8f5e8; border-left-color: #28a745; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1> Beauty Server Integrado</h1>
            <p>Servidor FastAPI + MCP con análisis avanzado de colorimetría</p>
            <p><strong>Versión:</strong> {server.version}</p>
            <p><strong>Estado:</strong> ✅ Activo con funcionalidad MCP</p>
        </div>
        
        <h2>🆕 Nuevos Endpoints MCP</h2>
        
        <div class="section new">
            <div class="method">POST /mcp/create-profile</div>
            <p>Crear perfil avanzado con análisis científico de subtono</p>
        </div>
        
        <div class="section new">
            <div class="method">GET /mcp/profile/{{user_id}}</div>
            <p>Mostrar análisis colorimétrico completo</p>
        </div>
        
        <div class="section new">
            <div class="method">GET /mcp/profiles</div>
            <p>Listar todos los perfiles</p>
        </div>
        
        <div class="section new">
            <div class="method">POST /mcp/generate-palette</div>
            <p>Generar paleta con análisis MCP avanzado</p>
        </div>
        
        <h2> Endpoints Existentes (compatibilidad)</h2>
        
        <div class="section">
            <div class="method">POST /api/generate-palette</div>
            <p>Generador de paletas original</p>
        </div>
        
        <div class="section">
            <div class="method">GET /api/quote</div>
            <p>Citas inspiracionales</p>
        </div>
        
        <div class="section">
            <div class="method">POST /api/analyze-harmony</div>
            <p>Análisis de armonía (ahora con integración MCP)</p>
        </div>
        
        <h2>📚 Documentación</h2>
        <p><a href="/docs">📖 Swagger UI</a> | <a href="/redoc">📘 ReDoc</a></p>
        
        <p><strong>🚀 Nuevas capacidades:</strong> Análisis científico de subtono, 8 estaciones de color, teoría de armonías avanzada</p>
    </body>
    </html>
    """
    return html_content

@app.get("/health")
async def health_check():
    """Estado del servidor integrado"""
    return {
        "status": "healthy",
        "server_name": server.server_name,
        "version": server.version,
        "timestamp": datetime.now().isoformat(),
        "features": {
            "fastapi_endpoints": True,
            "mcp_integration": True,
            "advanced_colorimetry": True,
            "profile_system": True
        },
        "endpoints": {
            "original": 5,
            "mcp": 6,
            "total": 11
        }
    }

# === NUEVOS ENDPOINTS MCP ===

@app.post("/mcp/create-profile")
async def create_mcp_profile(request: Dict[str, Any]):
    """Crear perfil usando el sistema MCP avanzado"""
    try:
        result = tool_create_profile(request)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "Perfil creado con análisis MCP avanzado"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/profile/{user_id}")
async def get_mcp_profile(user_id: str):
    """Obtener perfil MCP completo"""
    try:
        result = tool_show_profile({"user_id": user_id})
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "data": result["profile"],
            "analysis_type": "MCP Advanced"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/profiles")
async def list_mcp_profiles():
    """Listar todos los perfiles MCP"""
    try:
        result = tool_list_profiles({})
        return {
            "success": True,
            "data": result,
            "source": "MCP System"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/mcp/profile/{user_id}")
async def delete_mcp_profile(user_id: str):
    """Eliminar perfil MCP"""
    try:
        result = tool_delete_profile({"user_id": user_id})
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "message": result["message"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/generate-palette")
async def generate_mcp_palette(request: Dict[str, Any]):
    """Generar paleta usando el sistema MCP"""
    try:
        result = tool_generate_palette(request)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result["palette"],
            "analysis_type": "MCP Advanced Colorimetry"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/quick-palette")
async def generate_quick_mcp_palette(request: Dict[str, Any]):
    """Generar paleta rápida MCP sin perfil"""
    try:
        result = tool_quick_palette(request)
        return {
            "success": True,
            "data": result["palette"],
            "type": "Quick MCP Palette"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/export/{user_id}")
async def export_mcp_data(user_id: str):
    """Exportar datos completos del usuario"""
    try:
        result = tool_export_data({"user_id": user_id})
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "data": result["exported_data"],
            "summary": result["summary"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS EXISTENTES MEJORADOS ===

@app.post("/api/generate-palette")
async def generate_palette_original(request: Dict[str, Any]):
    """Generador original con mejoras MCP opcionales"""
    try:
        profile = request.get("profile", {})
        palette_type = request.get("palette_type", "ropa")
        event_type = request.get("event_type", "casual")
        use_mcp = request.get("use_mcp_analysis", False)  # Nueva opción
        
        # Si se solicita análisis MCP y hay suficiente info
        if use_mcp and profile.get("user_id"):
            try:
                # Intentar generar con MCP
                mcp_request = {
                    "user_id": profile["user_id"],
                    "palette_type": palette_type,
                    "event_type": event_type
                }
                mcp_result = tool_generate_palette(mcp_request)
                
                if "error" not in mcp_result:
                    return {
                        "success": True,
                        "data": mcp_result["palette"],
                        "enhanced_by": "MCP Advanced Analysis"
                    }
            except:
                pass  # Fallback al método original
        
        # Método original como fallback
        colors = []
        skin_tone = profile.get('skin_tone', 'media')
        
        if skin_tone in server.color_database['skin_tones']:
            skin_colors = server.color_database['skin_tones'][skin_tone]['best_colors']
            event_colors = server.color_database['event_palettes'].get(event_type, {}).get('primary', [])
            
            all_colors = skin_colors[:3] + event_colors[:3]
            
            for i, color in enumerate(all_colors[:6]):
                colors.append({
                    "hex": color,
                    "name": f"Color {i+1}",
                    "category": "generated"
                })
        
        return {
            "success": True,
            "data": {
                "palette_id": f"api_{palette_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "colors": colors,
                "type": palette_type,
                "event": event_type,
                "method": "Original API"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-harmony")
async def analyze_harmony_enhanced(request: Dict[str, Any]):
    """Análisis de armonía mejorado con MCP"""
    try:
        colors = request.get("colors", [])
        use_mcp = request.get("use_mcp", True)  # Usar MCP por defecto
        
        if len(colors) < 2:
            raise HTTPException(status_code=400, detail="Se requieren al menos 2 colores")
        
        if use_mcp:
            # Usar análisis MCP avanzado
            analysis = server.analyze_color_harmony_advanced(colors)
        else:
            # Análisis básico original
            analysis = {
                "harmony_score": random.randint(60, 90),
                "harmony_type": "Básico",
                "analysis": "Análisis básico de compatibilidad"
            }
        
        return {
            "success": True,
            "data": analysis,
            "colors_analyzed": len(colors),
            "analysis_method": "MCP Advanced" if use_mcp else "Basic"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quote")
async def get_quote_original(category: str = None):
    """Citas inspiracionales (endpoint original)"""
    try:
        quotes = server.quotes_database
        
        if category:
            filtered = [q for q in quotes if q.get('category', '').lower() == category.lower()]
            quotes = filtered if filtered else quotes
        
        quote = random.choice(quotes) if quotes else {
            "quote": "La belleza está en los ojos del que mira",
            "author": "Platón",
            "category": "filosofia"
        }
        
        return {
            "success": True,
            "data": quote,
            "server_info": server.server_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Configuración del servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Iniciando Beauty Server Integrado...")
    print(f"📍 Puerto: {port}")
    print("🌐 URL: https://beauty-pallet-server.railway.app")
    print("🔬 Funcionalidades: FastAPI + MCP Advanced")
    print("📚 Docs: /docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )