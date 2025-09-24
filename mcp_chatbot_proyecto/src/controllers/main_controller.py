"""
Main Controller - Controlador principal del sistema MCP Chatbot
"""

import asyncio
from typing import Optional
from datetime import datetime

from models.session_model import SessionModel
from models.logging_model import LoggingModel
from services.claude_service import ClaudeService
from controllers.beauty_controller import BeautyController
from controllers.quotes_controller import QuotesController
from controllers.git_controller import GitController
from views.chat_view import ChatView


class MainController:
    def __init__(self):
        """Inicializar controlador principal"""
        # Modelos
        self.session_model = SessionModel()
        self.logging_model = LoggingModel()
        
        # Servicios
        self.claude_service = None
        
        # Controladores especializados
        self.beauty_controller = None
        self.quotes_controller = None
        self.git_controller = None
        
        # Vista
        self.chat_view = ChatView()
        
        # Estado
        self.is_initialized = False
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def initialize(self) -> bool:
        """Inicializar todos los componentes del sistema"""
        try:
            # Inicializar servicio de Claude
            self.claude_service = ClaudeService()
            if not await self.claude_service.initialize():
                print(" Error inicializando Claude Service")
                return False
            
            # Inicializar controladores especializados
            self.beauty_controller = BeautyController(self.claude_service, self.logging_model)
            self.quotes_controller = QuotesController(self.logging_model)
            self.git_controller = GitController(self.logging_model)
            
            # Inicializar controladores
            if not await self.beauty_controller.initialize():
                print(" Error inicializando Beauty Controller")
                return False
            
            if not await self.quotes_controller.initialize():
                print(" Error inicializando Quotes Controller")
                return False
            
            if not await self.git_controller.initialize():
                print(" Error inicializando Git Controller")
                return False
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f" Error en inicialización: {str(e)}")
            return False
    
    async def run_interactive_mode(self):
        """Ejecutar modo interactivo principal"""
        if not self.is_initialized:
            print(" Sistema no inicializado")
            return
        
        # Mostrar mensaje de bienvenida
        self.chat_view.show_welcome_message()
        
        while True:
            try:
                # Obtener entrada del usuario
                user_input = self.chat_view.get_user_input()
                
                # Procesar entrada
                if user_input.lower() == '/quit':
                    break
                elif not user_input.strip():
                    continue
                
                # Registrar entrada del usuario
                self.logging_model.log_user_input(user_input, self.session_id)
                
                # Procesar comando o mensaje
                response = await self.process_user_input(user_input)
                
                # Mostrar respuesta
                if response:
                    self.chat_view.show_response(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.chat_view.show_error(f"Error procesando entrada: {str(e)}")
        
        # Limpiar recursos al salir
        await self.cleanup()
        self.chat_view.show_goodbye()
    
    async def process_user_input(self, user_input: str) -> Optional[str]:
        """Procesar entrada del usuario y retornar respuesta"""
        try:
            # Verificar comandos especiales
            if user_input.startswith('/'):
                return await self.process_special_command(user_input)
            
            # Procesar mensaje normal con Claude
            self.session_model.add_message("user", user_input)
            
            # Construir contexto para Claude
            context = self.session_model.get_context()
            
            # Enviar a Claude
            response = await self.claude_service.send_message(user_input, context)
            
            if response:
                # Agregar respuesta al contexto
                self.session_model.add_message("assistant", response)
                
                # Registrar respuesta
                tokens_used = self.claude_service.estimate_tokens(response)
                self.logging_model.log_claude_response(response, tokens_used, self.session_id)
                
                return response
            else:
                return " No se pudo obtener respuesta de Claude"
                
        except Exception as e:
            return f" Error procesando mensaje: {str(e)}"
    
    async def process_special_command(self, command: str) -> Optional[str]:
        """Procesar comandos especiales del sistema"""
        command_lower = command.lower().strip()
        
        # Comandos del sistema
        if command_lower == '/help':
            return self.chat_view.get_help_message()
        elif command_lower == '/log':
            self.logging_model.show_interaction_log()
            return None
        elif command_lower == '/mcp':
            self.logging_model.show_mcp_interactions()
            return None
        elif command_lower == '/stats':
            return self.get_session_stats()
        elif command_lower == '/context':
            self.session_model.show_context_summary()
            return None
        elif command_lower == '/clear':
            self.session_model.clear_context()
            return " Contexto limpiado"
        elif command_lower == '/save':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}.json"
            self.session_model.save_session(filename)
            return f" Sesión guardada: {filename}"
        
        # Comandos de belleza
        elif command_lower.startswith('/beauty') or command_lower.startswith('/palette'):
            return await self.beauty_controller.handle_command(command)
        
        # Comandos de citas
        elif command_lower.startswith('/quotes'):
            return await self.quotes_controller.handle_command(command)
        
        # Comandos de git y filesystem
        elif command_lower.startswith('/git') or command_lower.startswith('/fs'):
            return await self.git_controller.handle_command(command)
        
        else:
            return f" Comando desconocido: {command}. Usa /help para ver comandos disponibles"
    
    def get_session_stats(self) -> str:
        """Obtener estadísticas de la sesión actual"""
        session_stats = self.session_model.get_session_stats()
        mcp_stats = self.logging_model.get_mcp_stats()
        
        stats_text = f""" ESTADÍSTICAS DE SESIÓN:
  💬 Total mensajes: {session_stats['total_messages']}
   Mensajes usuario: {session_stats['user_messages']}
   Mensajes asistente: {session_stats['assistant_messages']}
  ⏱️  Duración: {session_stats['session_duration']}
  🧠 Mensajes en contexto: {session_stats['messages_in_context']}

🔧 ESTADÍSTICAS MCP:
  📡 Interacciones totales: {mcp_stats['total_interactions']}
   Tasa de éxito: {mcp_stats['success_rate']:.1f}%
  🖥️  Servidores usados: {', '.join(mcp_stats['servers_used']) if mcp_stats['servers_used'] else 'Ninguno'}"""
        
        return stats_text
    
    async def cleanup(self):
        """Limpiar recursos al finalizar"""
        try:
            # Guardar sesión automáticamente
            self.session_model.save_session(f"{self.session_id}.json")
            
            # Limpiar controladores
            if self.beauty_controller:
                await self.beauty_controller.cleanup()
            if self.quotes_controller:
                await self.quotes_controller.cleanup()
            if self.git_controller:
                await self.git_controller.cleanup()
            
            print(" Recursos limpiados correctamente")
            
        except Exception as e:
            print(f"  Error limpiando recursos: {str(e)}")