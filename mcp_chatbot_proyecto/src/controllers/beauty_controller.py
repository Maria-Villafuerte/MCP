"""
Beauty Controller - Controlador para sistema de belleza y paletas
"""

from typing import Optional, Dict, List
from models.beauty_model import BeautyModel
from models.logging_model import LoggingModel
from services.beauty_service import BeautyService
from services.claude_service import ClaudeService
from views.beauty_view import BeautyView


class BeautyController:
    def __init__(self, claude_service: ClaudeService, logging_model: LoggingModel):
        """
        Inicializar controlador de belleza
        
        Args:
            claude_service: Servicio de Claude API
            logging_model: Modelo de logging
        """
        self.claude_service = claude_service
        self.logging_model = logging_model
        
        # Modelos y servicios
        self.beauty_model = None
        self.beauty_service = None
        self.beauty_view = None
        
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Inicializar componentes del controlador"""
        try:
            # Inicializar modelos y servicios
            self.beauty_model = BeautyModel()
            self.beauty_service = BeautyService()
            self.beauty_view = BeautyView()
            
            self.is_initialized = True
            print("Beauty Controller inicializado correctamente")
            return True
            
        except Exception as e:
            print(f"Error inicializando Beauty Controller: {str(e)}")
            return False
    
    async def handle_command(self, command: str) -> Optional[str]:
        """
        Manejar comandos del sistema de belleza
        
        Args:
            command: Comando completo del usuario
            
        Returns:
            Respuesta formateada o None si no hay respuesta directa
        """
        if not self.is_initialized:
            return "Error: Beauty Controller no inicializado"
        
        try:
            # Parsear comando
            parts = command.strip().split()
            if len(parts) < 2:
                return self.beauty_view.show_beauty_help()
            
            action = parts[1].lower()
            
            # Procesar según acción
            if action == "help":
                return self.beauty_view.show_beauty_help()
            
            elif action == "create_profile":
                return await self._handle_create_profile()
            
            elif action == "profile":
                user_id = parts[2] if len(parts) > 2 else None
                return await self._handle_show_profile(user_id)
            
            elif action == "list_profiles":
                return await self._handle_list_profiles()
            
            elif action == "update_profile":
                user_id = parts[2] if len(parts) > 2 else None
                return await self._handle_update_profile(user_id)
            
            elif action == "delete_profile":
                user_id = parts[2] if len(parts) > 2 else None
                return await self._handle_delete_profile(user_id)
            
            elif action == "history":
                user_id = parts[2] if len(parts) > 2 else None
                return await self._handle_show_history(user_id)
            
            elif action == "stats":
                user_id = parts[2] if len(parts) > 2 else None
                return await self._handle_show_stats(user_id)
            
            elif action == "export":
                user_id = parts[2] if len(parts) > 2 else None
                return await self._handle_export_data(user_id)
            
            # Comandos de paleta
            elif command.startswith("/palette"):
                return await self._handle_palette_command(command)
            
            else:
                return f"Acción desconocida: {action}. Usa /beauty help para ver comandos disponibles"
        
        except Exception as e:
            error_msg = f"Error procesando comando de belleza: {str(e)}"
            self.logging_model.log_beauty_interaction(
                "command_error", error=error_msg, success=False
            )
            return error_msg
    
    async def _handle_create_profile(self) -> str:
        """Manejar creación de perfil"""
        try:
            # Recopilar datos del perfil
            profile_data = self.beauty_view.collect_profile_data()
            
            if not profile_data:
                return "Creación de perfil cancelada"
            
            # Verificar si el perfil ya existe
            existing_profile = self.beauty_model.load_profile(profile_data["user_id"])
            if existing_profile:
                return f"Error: Ya existe un perfil con ID '{profile_data['user_id']}'"
            
            # Crear perfil
            profile = self.beauty_model.create_profile(profile_data)
            
            # Registrar interacción
            self.logging_model.log_beauty_interaction(
                "create_profile", 
                user_id=profile.user_id,
                result=f"Perfil creado para {profile.name}",
                success=True
            )
            
            # Mostrar perfil creado
            profile_display = self.beauty_view.show_profile(profile)
            
            return f"Perfil creado exitosamente:\n\n{profile_display}\n\nAhora puedes generar paletas personalizadas usando /palette"
            
        except Exception as e:
            error_msg = f"Error creando perfil: {str(e)}"
            self.logging_model.log_beauty_interaction(
                "create_profile", error=error_msg, success=False
            )
            return error_msg
    
    async def _handle_show_profile(self, user_id: Optional[str]) -> str:
        """Manejar visualización de perfil"""
        if not user_id:
            return "Error: Especifica un user_id. Uso: /beauty profile <user_id>"
        
        try:
            profile = self.beauty_model.load_profile(user_id)
            
            if not profile:
                profiles = self.beauty_model.list_profiles()
                available = ", ".join(profiles) if profiles else "ninguno"
                return f"Perfil '{user_id}' no encontrado. Perfiles disponibles: {available}"
            
            return self.beauty_view.show_profile(profile)
            
        except Exception as e:
            return f"Error mostrando perfil: {str(e)}"
    
    async def _handle_list_profiles(self) -> str:
        """Manejar listado de perfiles"""
        try:
            profiles = self.beauty_model.list_profiles()
            return self.beauty_view.show_profile_list(profiles)
            
        except Exception as e:
            return f"Error listando perfiles: {str(e)}"
    
    async def _handle_update_profile(self, user_id: Optional[str]) -> str:
        """Manejar actualización de perfil"""
        if not user_id:
            return "Error: Especifica un user_id. Uso: /beauty update_profile <user_id>"
        
        try:
            # Cargar perfil existente
            existing_profile = self.beauty_model.load_profile(user_id)
            if not existing_profile:
                return f"Perfil '{user_id}' no encontrado"
            
            # Recopilar nuevos datos
            print(f"Actualizando perfil de {existing_profile.name}...")
            new_data = self.beauty_view.collect_profile_data()
            
            if not new_data:
                return "Actualización cancelada"
            
            # Mantener el mismo user_id
            new_data["user_id"] = user_id
            
            # Crear perfil actualizado
            updated_profile = self.beauty_model.create_profile(new_data)
            
            self.logging_model.log_beauty_interaction(
                "update_profile",
                user_id=user_id,
                result="Perfil actualizado",
                success=True
            )
            
            return f"Perfil actualizado exitosamente:\n\n{self.beauty_view.show_profile(updated_profile)}"
            
        except Exception as e:
            return f"Error actualizando perfil: {str(e)}"
    
    async def _handle_delete_profile(self, user_id: Optional[str]) -> str:
        """Manejar eliminación de perfil"""
        if not user_id:
            return "Error: Especifica un user_id. Uso: /beauty delete_profile <user_id>"
        
        try:
            # Verificar que existe
            profile = self.beauty_model.load_profile(user_id)
            if not profile:
                return f"Perfil '{user_id}' no encontrado"
            
            # Confirmar eliminación
            confirm = self.beauty_view._prompt_input(
                f"¿Eliminar perfil de {profile.name}? (escriba 'CONFIRMAR')"
            )
            
            if confirm != "CONFIRMAR":
                return "Eliminación cancelada"
            
            # Eliminar perfil
            if self.beauty_model.delete_profile(user_id):
                self.logging_model.log_beauty_interaction(
                    "delete_profile",
                    user_id=user_id,
                    result="Perfil eliminado",
                    success=True
                )
                return f"Perfil '{user_id}' eliminado exitosamente"
            else:
                return f"Error eliminando perfil '{user_id}'"
                
        except Exception as e:
            return f"Error eliminando perfil: {str(e)}"
    
    async def _handle_show_history(self, user_id: Optional[str]) -> str:
        """Manejar visualización de historial"""
        if not user_id:
            return "Error: Especifica un user_id. Uso: /beauty history <user_id>"
        
        try:
            # Verificar que el perfil existe
            profile = self.beauty_model.load_profile(user_id)
            if not profile:
                return f"Perfil '{user_id}' no encontrado"
            
            # Cargar historial de paletas
            palettes = self.beauty_model.load_user_palettes(user_id)
            
            return self.beauty_view.show_palette_history(palettes, user_id)
            
        except Exception as e:
            return f"Error mostrando historial: {str(e)}"
    
    async def _handle_show_stats(self, user_id: Optional[str]) -> str:
        """Manejar estadísticas de usuario"""
        if not user_id:
            return "Error: Especifica un user_id. Uso: /beauty stats <user_id>"
        
        try:
            # Verificar perfil
            profile = self.beauty_model.load_profile(user_id)
            if not profile:
                return f"Perfil '{user_id}' no encontrado"
            
            # Obtener paletas
            palettes = self.beauty_model.load_user_palettes(user_id)
            
            # Calcular estadísticas
            total_palettes = len(palettes)
            palette_types = {}
            event_types = {}
            
            for palette in palettes:
                palette_types[palette.palette_type] = palette_types.get(palette.palette_type, 0) + 1
                event_types[palette.event_type] = event_types.get(palette.event_type, 0) + 1
            
            stats_text = f"ESTADÍSTICAS DE {profile.name.upper()} ({user_id}):\n\n"
            stats_text += f"Total de paletas generadas: {total_palettes}\n\n"
            
            if palette_types:
                stats_text += "Tipos de paleta más usados:\n"
                for ptype, count in sorted(palette_types.items(), key=lambda x: x[1], reverse=True):
                    stats_text += f"  {ptype}: {count}\n"
                stats_text += "\n"
            
            if event_types:
                stats_text += "Eventos más frecuentes:\n"
                for etype, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
                    stats_text += f"  {etype}: {count}\n"
            
            return stats_text
            
        except Exception as e:
            return f"Error generando estadísticas: {str(e)}"
    
    async def _handle_export_data(self, user_id: Optional[str]) -> str:
        """Manejar exportación de datos"""
        if not user_id:
            return "Error: Especifica un user_id. Uso: /beauty export <user_id>"
        
        try:
            # Verificar perfil
            profile = self.beauty_model.load_profile(user_id)
            if not profile:
                return f"Perfil '{user_id}' no encontrado"
            
            # Obtener todas las paletas
            palettes = self.beauty_model.load_user_palettes(user_id)
            
            # Crear resumen de exportación
            export_data = {
                "profile": profile.__dict__,
                "palettes_count": len(palettes),
                "export_date": self.beauty_model.datetime.now().isoformat()
            }
            
            # Guardar en archivo (simulado)
            export_filename = f"beauty_export_{user_id}_{self.beauty_model.datetime.now().strftime('%Y%m%d')}.json"
            
            self.logging_model.log_beauty_interaction(
                "export_data",
                user_id=user_id,
                result=f"Datos exportados a {export_filename}",
                success=True
            )
            
            return f"Datos exportados exitosamente:\n\nArchivo: {export_filename}\nPerfil: {profile.name}\nPaletas: {len(palettes)}\n\nLos datos han sido preparados para exportación."
            
        except Exception as e:
            return f"Error exportando datos: {str(e)}"
    
    async def _handle_palette_command(self, command: str) -> str:
        """Manejar comandos de generación de paletas"""
        try:
            # Parsear comando: /palette <tipo> [user_id] [evento] [preferencias]
            parts = command.strip().split()
            
            if len(parts) < 2:
                return "Uso: /palette <tipo> [user_id] [evento]\nTipos: ropa, maquillaje, accesorios"
            
            palette_type = parts[1].lower()
            
            if palette_type not in ["ropa", "maquillaje", "accesorios"]:
                return "Tipo de paleta no válido. Opciones: ropa, maquillaje, accesorios"
            
            # Determinar si es paleta rápida o con perfil
            if len(parts) >= 3 and parts[2] == "quick":
                return await self._generate_quick_palette(palette_type, parts[3:])
            else:
                return await self._generate_profile_palette(palette_type, parts[2:])
        
        except Exception as e:
            return f"Error procesando comando de paleta: {str(e)}"
    
    async def _generate_quick_palette(self, palette_type: str, params: List[str]) -> str:
        """Generar paleta rápida sin perfil"""
        try:
            event_type = params[0] if params else "casual"
            
            # Crear perfil temporal básico
            temp_profile_data = {
                "user_id": "temp_user",
                "name": "Usuario Temporal",
                "skin_tone": "media",
                "undertone": "neutro",
                "eye_color": "cafe",
                "hair_color": "castano",
                "hair_type": "liso",
                "style_preference": "moderno"
            }
            
            temp_profile = self.beauty_model.create_profile(temp_profile_data)
            
            # Generar paleta
            palette = await self.beauty_service.generate_advanced_palette(
                temp_profile, palette_type, event_type
            )
            
            # No guardar la paleta temporal
            self.logging_model.log_beauty_interaction(
                "quick_palette",
                palette_type=palette_type,
                result=f"Paleta rápida {palette_type} para {event_type}",
                success=True
            )
            
            palette_display = self.beauty_view.show_palette(palette)
            return f"PALETA RÁPIDA GENERADA:\n\n{palette_display}\n\nPara recomendaciones más precisas, crea un perfil con /beauty create_profile"
            
        except Exception as e:
            return f"Error generando paleta rápida: {str(e)}"
    
    async def _generate_profile_palette(self, palette_type: str, params: List[str]) -> str:
        """Generar paleta basada en perfil"""
        try:
            if not params:
                return "Error: Especifica user_id. Uso: /palette <tipo> <user_id> [evento]"
            
            user_id = params[0]
            event_type = params[1] if len(params) > 1 else "casual"
            
            # Cargar perfil
            profile = self.beauty_model.load_profile(user_id)
            if not profile:
                return f"Perfil '{user_id}' no encontrado. Usa /beauty list_profiles para ver perfiles disponibles"
            
            # Recopilar preferencias adicionales
            preferences = self.beauty_view.collect_palette_preferences(palette_type, event_type)
            
            # Generar paleta
            palette = await self.beauty_service.generate_advanced_palette(
                profile, palette_type, event_type, preferences
            )
            
            # Guardar paleta
            self.beauty_model.save_palette(palette)
            
            # Registrar interacción
            self.logging_model.log_beauty_interaction(
                "generate_palette",
                user_id=user_id,
                palette_type=palette_type,
                result=f"Paleta {palette_type} para {event_type}",
                success=True
            )
            
            # Generar respuesta contextual con Claude
            claude_response = await self._get_claude_styling_advice(profile, palette, event_type)
            
            palette_display = self.beauty_view.show_palette(palette)
            
            final_response = f"{palette_display}\n\n"
            if claude_response:
                final_response += f"CONSEJOS ADICIONALES:\n{claude_response}"
            
            return final_response
            
        except Exception as e:
            return f"Error generando paleta: {str(e)}"
    
    async def _get_claude_styling_advice(self, profile, palette, event_type: str) -> Optional[str]:
        """Obtener consejos de estilo de Claude"""
        try:
            # Preparar contexto para Claude
            profile_context = {
                "skin_tone": profile.skin_tone,
                "undertone": profile.undertone,
                "eye_color": profile.eye_color,
                "hair_color": profile.hair_color,
                "style_preference": profile.style_preference
            }
            
            advice_request = f"Basándome en la paleta de {palette.palette_type} que generé para un evento {event_type}, ¿podrías darme 3-4 consejos específicos de estilo y aplicación?"
            
            return await self.claude_service.send_beauty_context_message(
                advice_request, profile_context
            )
            
        except Exception as e:
            print(f"Error obteniendo consejos de Claude: {str(e)}")
            return None
    
    async def cleanup(self):
        """Limpiar recursos del controlador"""
        self.is_initialized = False
        print("Beauty Controller limpiado")


# Testing del controlador
if __name__ == "__main__":
    import asyncio
    from unittest.mock import MagicMock
    
    async def test_beauty_controller():
        print("Testing Beauty Controller...")
        
        # Crear mocks
        claude_service = MagicMock()
        logging_model = MagicMock()
        
        # Inicializar controlador
        controller = BeautyController(claude_service, logging_model)
        
        if await controller.initialize():
            print("Controlador inicializado")
            
            # Test comando de ayuda
            help_response = await controller.handle_command("/beauty help")
            print(f"Ayuda: {help_response[:100]}...")
            
            # Test listar perfiles
            list_response = await controller.handle_command("/beauty list_profiles")
            print(f"Lista: {list_response[:100]}...")
            
            print("Beauty Controller funcionando correctamente")
        else:
            print("Error inicializando controlador")
        
        await controller.cleanup()
    
    asyncio.run(test_beauty_controller())