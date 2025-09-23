"""
Quotes Controller - Controlador para sistema de citas remotas
"""

from typing import Optional
from models.logging_model import LoggingModel
from services.remote_quotes_service import RemoteQuotesService


class QuotesController:
    def __init__(self, logging_model: LoggingModel):
        """
        Inicializar controlador de citas
        
        Args:
            logging_model: Modelo de logging
        """
        self.logging_model = logging_model
        self.quotes_service = None
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Inicializar controlador y servicio remoto"""
        try:
            self.quotes_service = RemoteQuotesService()
            service_available = await self.quotes_service.initialize()
            
            if service_available:
                print("Quotes Controller inicializado - Servidor remoto disponible")
            else:
                print("Quotes Controller inicializado - Servidor remoto no disponible (modo fallback)")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Error inicializando Quotes Controller: {str(e)}")
            return False
    
    async def handle_command(self, command: str) -> Optional[str]:
        """
        Manejar comandos del sistema de citas
        
        Args:
            command: Comando completo del usuario
            
        Returns:
            Respuesta formateada
        """
        if not self.is_initialized:
            return "Error: Quotes Controller no inicializado"
        
        try:
            # Parsear comando
            parts = command.strip().split()
            if len(parts) < 2:
                return self._show_quotes_help()
            
            action = parts[1].lower()
            
            # Procesar según acción
            if action == "help":
                return self._show_quotes_help()
            
            elif action == "get":
                category = parts[2] if len(parts) > 2 else None
                return await self._handle_get_quote(category)
            
            elif action == "tip":
                return await self._handle_get_tip()
            
            elif action == "search":
                if len(parts) < 3:
                    return "Error: Especifica término de búsqueda. Uso: /quotes search <palabra>"
                query = " ".join(parts[2:])
                return await self._handle_search_quotes(query)
            
            elif action == "wisdom":
                return await self._handle_get_wisdom()
            
            elif action == "status":
                return await self._handle_status_check()
            
            else:
                return f"Acción desconocida: {action}. Usa /quotes help para ver comandos disponibles"
        
        except Exception as e:
            error_msg = f"Error procesando comando de citas: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "quotes_remote", "command_error", {"command": command}, 
                error=error_msg, success=False
            )
            return error_msg
    
    def _show_quotes_help(self) -> str:
        """Mostrar ayuda del sistema de citas"""
        return """SISTEMA DE CITAS INSPIRACIONALES

COMANDOS DISPONIBLES:
  /quotes help                 - Mostrar esta ayuda
  /quotes get [categoría]      - Obtener cita inspiracional
  /quotes tip                  - Obtener consejo de belleza/bienestar
  /quotes search <palabra>     - Buscar citas por palabra clave
  /quotes wisdom               - Obtener sabiduría diaria
  /quotes status               - Verificar estado del servidor

CATEGORÍAS DISPONIBLES:
  motivacion, belleza, confianza, éxito, amor, vida, inspiracion

EJEMPLOS DE USO:
  /quotes get motivacion
  /quotes search belleza
  /quotes tip
  /quotes wisdom

NOTA: Las citas provienen de un servidor remoto. Si no está disponible, se mostrarán citas locales de respaldo."""
    
    async def _handle_get_quote(self, category: Optional[str] = None) -> str:
        """Obtener cita inspiracional"""
        try:
            # Llamar al servicio remoto
            quote_data = await self.quotes_service.get_inspirational_quote(
                category=category, time_based=True
            )
            
            # Registrar interacción
            self.logging_model.log_mcp_interaction(
                "quotes_remote", "get_quote", 
                {"category": category}, 
                result=quote_data, 
                success="error" not in quote_data
            )
            
            # Formatear respuesta
            return self.quotes_service.format_quote_response(quote_data)
            
        except Exception as e:
            error_msg = f"Error obteniendo cita: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "quotes_remote", "get_quote", {"category": category}, 
                error=error_msg, success=False
            )
            return error_msg
    
    async def _handle_get_tip(self) -> str:
        """Obtener consejo de belleza/bienestar"""
        try:
            # Llamar al servicio remoto
            tip_data = await self.quotes_service.get_sleep_hygiene_tip()
            
            # Registrar interacción
            self.logging_model.log_mcp_interaction(
                "quotes_remote", "get_tip", {}, 
                result=tip_data, 
                success="error" not in tip_data
            )
            
            # Formatear respuesta
            return self.quotes_service.format_tip_response(tip_data)
            
        except Exception as e:
            error_msg = f"Error obteniendo consejo: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "quotes_remote", "get_tip", {}, 
                error=error_msg, success=False
            )
            return error_msg
    
    async def _handle_search_quotes(self, query: str) -> str:
        """Buscar citas por palabra clave"""
        try:
            # Validar query
            if len(query.strip()) < 2:
                return "Error: Término de búsqueda demasiado corto (mínimo 2 caracteres)"
            
            # Llamar al servicio remoto
            search_data = await self.quotes_service.search_quotes(query, limit=8)
            
            # Registrar interacción
            self.logging_model.log_mcp_interaction(
                "quotes_remote", "search_quotes", 
                {"query": query}, 
                result=search_data, 
                success="error" not in search_data
            )
            
            # Formatear respuesta
            return self.quotes_service.format_search_results(search_data)
            
        except Exception as e:
            error_msg = f"Error en búsqueda: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "quotes_remote", "search_quotes", {"query": query}, 
                error=error_msg, success=False
            )
            return error_msg
    
    async def _handle_get_wisdom(self) -> str:
        """Obtener sabiduría diaria"""
        try:
            # Llamar al servicio remoto
            wisdom_data = await self.quotes_service.get_wisdom(include_tip=True)
            
            # Registrar interacción
            self.logging_model.log_mcp_interaction(
                "quotes_remote", "get_wisdom", {}, 
                result=wisdom_data, 
                success="error" not in wisdom_data
            )
            
            # Formatear respuesta
            return self.quotes_service.format_quote_response(wisdom_data)
            
        except Exception as e:
            error_msg = f"Error obteniendo sabiduría: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "quotes_remote", "get_wisdom", {}, 
                error=error_msg, success=False
            )
            return error_msg
    
    async def _handle_status_check(self) -> str:
        """Verificar estado del servidor remoto"""
        try:
            # Obtener estado de conexión
            status = await self.quotes_service.get_connection_status()
            
            # Formatear respuesta de estado
            status_text = "ESTADO DEL SERVIDOR DE CITAS:\n\n"
            status_text += f"URL del servidor: {status['server_url']}\n"
            status_text += f"Estado: {'Conectado' if status['is_available'] else 'Desconectado'}\n"
            status_text += f"Timeout: {status['timeout']} segundos\n"
            
            if status['last_check']:
                check_status = status['last_check'].get('status', 'unknown')
                status_text += f"Última verificación: {check_status}\n"
                
                if 'message' in status['last_check']:
                    status_text += f"Mensaje: {status['last_check']['message']}\n"
            
            # Realizar test en tiempo real
            health_check = await self.quotes_service.health_check()
            if health_check.get('status') == 'healthy':
                status_text += "\nTest en tiempo real: EXITOSO"
            else:
                status_text += f"\nTest en tiempo real: FALLIDO - {health_check.get('message', 'Sin detalles')}"
            
            return status_text
            
        except Exception as e:
            return f"Error verificando estado: {str(e)}"
    
    async def get_contextual_quote(self, context: str) -> Optional[str]:
        """
        Obtener cita contextual para el sistema de belleza
        
        Args:
            context: Contexto para la cita (ej: "beauty", "confidence", "style")
            
        Returns:
            Cita formateada o None si hay error
        """
        try:
            # Mapear contexto a categoría
            context_mapping = {
                "beauty": "belleza",
                "confidence": "confianza", 
                "style": "inspiracion",
                "motivation": "motivacion",
                "success": "éxito"
            }
            
            category = context_mapping.get(context.lower(), "inspiracion")
            
            # Obtener cita
            quote_data = await self.quotes_service.get_inspirational_quote(category=category)
            
            if "error" not in quote_data:
                return self.quotes_service.format_quote_response(quote_data)
            else:
                return None
                
        except Exception:
            return None
    
    async def get_beauty_tip(self) -> Optional[str]:
        """Obtener consejo específico de belleza"""
        try:
            tip_data = await self.quotes_service.get_sleep_hygiene_tip()
            
            if "error" not in tip_data:
                # Adaptar el consejo al contexto de belleza
                formatted_tip = self.quotes_service.format_tip_response(tip_data)
                return formatted_tip.replace("CONSEJO DE BELLEZA:", "CONSEJO DE BIENESTAR:")
            else:
                return None
                
        except Exception:
            return None
    
    async def cleanup(self):
        """Limpiar recursos del controlador"""
        if self.quotes_service:
            await self.quotes_service.cleanup()
        
        self.is_initialized = False
        print("Quotes Controller limpiado")


# Testing del controlador
if __name__ == "__main__":
    import asyncio
    from unittest.mock import MagicMock
    
    async def test_quotes_controller():
        print("Testing Quotes Controller...")
        
        # Crear mock del logging
        logging_model = MagicMock()
        
        # Inicializar controlador
        controller = QuotesController(logging_model)
        
        if await controller.initialize():
            print("Controlador inicializado")
            
            # Test comando de ayuda
            help_response = await controller.handle_command("/quotes help")
            print(f"Ayuda: {help_response[:100]}...")
            
            # Test obtener cita
            quote_response = await controller.handle_command("/quotes get motivacion")
            print(f"Cita: {quote_response[:100]}...")
            
            # Test estado
            status_response = await controller.handle_command("/quotes status")
            print(f"Estado: {status_response[:100]}...")
            
            # Test método contextual
            contextual_quote = await controller.get_contextual_quote("beauty")
            if contextual_quote:
                print(f"Cita contextual: {contextual_quote[:100]}...")
            
            print("Quotes Controller funcionando correctamente")
        else:
            print("Error inicializando controlador")
        
        await controller.cleanup()
    
    asyncio.run(test_quotes_controller())