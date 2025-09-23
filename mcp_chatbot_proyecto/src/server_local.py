#!/usr/bin/env python3
"""
Servidor Local MCP - Expone funcionalidades via HTTP
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Importar controladores existentes
from controllers.beauty_controller import BeautyController
from controllers.quotes_controller import QuotesController
from controllers.git_controller import GitController
from services.claude_service import ClaudeService
from models.logging_model import LoggingModel
from models.session_model import SessionModel

# Modelos Pydantic para requests
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ProfileRequest(BaseModel):
    user_id: str
    name: str
    skin_tone: str
    undertone: Optional[str] = "neutro"
    eye_color: str
    hair_color: str
    hair_type: Optional[str] = "liso"
    style_preference: Optional[str] = "moderno"

class PaletteRequest(BaseModel):
    user_id: str
    palette_type: str  # ropa, maquillaje, accesorios
    event_type: str = "casual"
    preferences: Optional[Dict[str, Any]] = None

class CommandRequest(BaseModel):
    command: str

# Inicializar FastAPI
app = FastAPI(title="MCPChatbot Server", version="1.0.0")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales para controladores
claude_service = None
beauty_controller = None
quotes_controller = None
git_controller = None
logging_model = None
sessions = {}  # session_id -> SessionModel

async def initialize_system():
    """Inicializar todos los componentes del sistema"""
    global claude_service, beauty_controller, quotes_controller, git_controller, logging_model
    
    try:
        print("🚀 Inicializando sistema MCP...")
        
        # Cargar variables de entorno
        load_dotenv()
        
        # Inicializar logging
        logging_model = LoggingModel()
        
        # Inicializar Claude service
        claude_service = ClaudeService()
        if not await claude_service.initialize():
            raise Exception("Error inicializando Claude Service")
        
        # Inicializar controladores
        beauty_controller = BeautyController(claude_service, logging_model)
        quotes_controller = QuotesController(logging_model)
        git_controller = GitController(logging_model)
        
        # Inicializar cada controlador
        if not await beauty_controller.initialize():
            raise Exception("Error inicializando Beauty Controller")
            
        if not await quotes_controller.initialize():
            raise Exception("Error inicializando Quotes Controller")
            
        if not await git_controller.initialize():
            raise Exception("Error inicializando Git Controller")
        
        print("✅ Sistema inicializado correctamente")
        return True
        
    except Exception as e:
        print(f" Error inicializando sistema: {str(e)}")
        return False

def get_session(session_id: str) -> SessionModel:
    """Obtener o crear sesión"""
    if session_id not in sessions:
        sessions[session_id] = SessionModel()
    return sessions[session_id]

# Endpoints principales

@app.get("/health")
async def health_check():
    """Health check del servidor"""
    return {
        "status": "healthy",
        "services": {
            "claude": claude_service.is_initialized if claude_service else False,
            "beauty": beauty_controller.is_initialized if beauty_controller else False,
            "quotes": quotes_controller.is_initialized if quotes_controller else False,
            "git": git_controller.is_initialized if git_controller else False
        }
    }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Procesar mensaje de chat"""
    if not claude_service or not claude_service.is_initialized:
        raise HTTPException(status_code=503, detail="Claude service no disponible")
    
    try:
        session_id = request.session_id or "default"
        session = get_session(session_id)
        
        # Agregar mensaje del usuario al contexto
        session.add_message("user", request.message)
        
        # Procesar con Claude
        context = session.get_context()
        response = await claude_service.send_message(request.message, context)
        
        if response:
            # Agregar respuesta al contexto
            session.add_message("assistant", response)
            
            # Log
            logging_model.log_user_input(request.message, session_id)
            logging_model.log_claude_response(response, session_id=session_id)
            
            return {
                "response": response,
                "session_id": session_id
            }
        else:
            raise HTTPException(status_code=500, detail="No se pudo obtener respuesta")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Beauty Controller

@app.post("/beauty/profile")
async def create_profile(request: ProfileRequest):
    """Crear perfil de belleza"""
    if not beauty_controller:
        raise HTTPException(status_code=503, detail="Beauty controller no disponible")
    
    try:
        profile_data = request.dict()
        profile = beauty_controller.beauty_model.create_profile(profile_data)
        
        logging_model.log_beauty_interaction(
            "create_profile", user_id=profile.user_id, success=True
        )
        
        return {
            "success": True,
            "profile": {
                "user_id": profile.user_id,
                "name": profile.name,
                "created_at": profile.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/beauty/profiles")
async def list_profiles():
    """Listar perfiles disponibles"""
    if not beauty_controller:
        raise HTTPException(status_code=503, detail="Beauty controller no disponible")
    
    try:
        profiles = beauty_controller.beauty_model.list_profiles()
        return {"profiles": profiles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/beauty/profile/{user_id}")
async def get_profile(user_id: str):
    """Obtener perfil específico"""
    if not beauty_controller:
        raise HTTPException(status_code=503, detail="Beauty controller no disponible")
    
    try:
        profile = beauty_controller.beauty_model.load_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "skin_tone": profile.skin_tone,
            "undertone": profile.undertone,
            "eye_color": profile.eye_color,
            "hair_color": profile.hair_color,
            "hair_type": profile.hair_type,
            "style_preference": profile.style_preference,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/beauty/palette")
async def generate_palette(request: PaletteRequest):
    """Generar paleta de colores"""
    if not beauty_controller:
        raise HTTPException(status_code=503, detail="Beauty controller no disponible")
    
    try:
        # Cargar perfil
        profile = beauty_controller.beauty_model.load_profile(request.user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
        # Generar paleta
        palette = await beauty_controller.beauty_service.generate_advanced_palette(
            profile, request.palette_type, request.event_type, request.preferences
        )
        
        # Guardar paleta
        beauty_controller.beauty_model.save_palette(palette)
        
        logging_model.log_beauty_interaction(
            "generate_palette", 
            user_id=request.user_id,
            palette_type=request.palette_type,
            success=True
        )
        
        return {
            "success": True,
            "palette": {
                "palette_id": palette.palette_id,
                "palette_type": palette.palette_type,
                "event_type": palette.event_type,
                "season": palette.season,
                "colors": palette.colors,
                "recommendations": palette.recommendations,
                "created_at": palette.created_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/beauty/history/{user_id}")
async def get_user_history(user_id: str):
    """Obtener historial de paletas del usuario"""
    if not beauty_controller:
        raise HTTPException(status_code=503, detail="Beauty controller no disponible")
    
    try:
        palettes = beauty_controller.beauty_model.load_user_palettes(user_id)
        return {
            "user_id": user_id,
            "total_palettes": len(palettes),
            "palettes": [
                {
                    "palette_id": p.palette_id,
                    "palette_type": p.palette_type,
                    "event_type": p.event_type,
                    "created_at": p.created_at
                } for p in palettes
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Quotes Controller

@app.get("/quotes/get")
async def get_quote(category: Optional[str] = None):
    """Obtener cita inspiracional"""
    if not quotes_controller:
        raise HTTPException(status_code=503, detail="Quotes controller no disponible")
    
    try:
        command = f"/quotes get {category}" if category else "/quotes get"
        response = await quotes_controller.handle_command(command)
        return {"quote": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quotes/search/{query}")
async def search_quotes(query: str, limit: int = 5):
    """Buscar citas por término"""
    if not quotes_controller:
        raise HTTPException(status_code=503, detail="Quotes controller no disponible")
    
    try:
        command = f"/quotes search {query}"
        response = await quotes_controller.handle_command(command)
        return {"results": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quotes/wisdom")
async def get_wisdom():
    """Obtener sabiduría diaria"""
    if not quotes_controller:
        raise HTTPException(status_code=503, detail="Quotes controller no disponible")
    
    try:
        response = await quotes_controller.handle_command("/quotes wisdom")
        return {"wisdom": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Git Controller

@app.post("/git/command")
async def git_command(request: CommandRequest):
    """Ejecutar comando de git o filesystem"""
    if not git_controller:
        raise HTTPException(status_code=503, detail="Git controller no disponible")
    
    try:
        response = await git_controller.handle_command(request.command)
        return {"result": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de sistema

@app.get("/sessions/{session_id}/stats")
async def get_session_stats(session_id: str):
    """Obtener estadísticas de sesión"""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    return session.get_session_stats()

@app.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """Limpiar contexto de sesión"""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session.clear_context()
    return {"message": "Contexto limpiado"}

@app.get("/logs/mcp")
async def get_mcp_logs():
    """Obtener logs de interacciones MCP"""
    if not logging_model:
        raise HTTPException(status_code=503, detail="Logging no disponible")
    
    return logging_model.get_mcp_stats()

@app.get("/logs/beauty")
async def get_beauty_logs():
    """Obtener logs del sistema de belleza"""
    if not logging_model:
        raise HTTPException(status_code=503, detail="Logging no disponible")
    
    return logging_model.get_beauty_stats()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Inicializar sistema al arrancar el servidor"""
    success = await initialize_system()
    if not success:
        raise Exception("Falló la inicialización del sistema")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Limpiar recursos al cerrar el servidor"""
    print("🧹 Cerrando servidor...")
    
    if beauty_controller:
        await beauty_controller.cleanup()
    if quotes_controller:
        await quotes_controller.cleanup()
    if git_controller:
        await git_controller.cleanup()
    if claude_service:
        await claude_service.cleanup()

# Función principal
def main():
    """Ejecutar servidor"""
    print("🌐 Iniciando servidor local MCP...")
    print("📡 Servidor disponible en: http://localhost:8000")
    print("📚 Documentación API en: http://localhost:8000/docs")
    print("⛔ Presiona Ctrl+C para detener\n")
    
    uvicorn.run(
        "server_local:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()