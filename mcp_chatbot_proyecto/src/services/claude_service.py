"""
Claude Service - Servicio para interacción con Claude API
"""

import os
import asyncio
from typing import List, Dict, Optional
from anthropic import Anthropic


class ClaudeService:
    def __init__(self):
        """Inicializar servicio de Claude"""
        self.client = None
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-haiku-20240307')
        self.max_tokens = 2000
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Inicializar cliente de Claude"""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print(" ANTHROPIC_API_KEY no encontrada en variables de entorno")
                return False
            
            self.client = Anthropic(api_key=api_key)
            
            # Test de conexión
            test_response = await self._test_connection()
            if test_response:
                self.is_initialized = True
                print(" Claude API conectado correctamente")
                return True
            else:
                print(" Error en test de conexión con Claude API")
                return False
                
        except Exception as e:
            print(f" Error inicializando Claude Service: {str(e)}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test de conexión con Claude API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[{"role": "user", "content": "Test de conexión. Responde solo 'OK'."}]
            )
            
            return response and response.content and len(response.content) > 0
            
        except Exception as e:
            print(f" Error en test de conexión: {str(e)}")
            return False
    
    async def send_message(self, message: str, conversation_history: List[Dict] = None) -> Optional[str]:
        """
        Enviar mensaje a Claude
        
        Args:
            message: Mensaje del usuario
            conversation_history: Historial de conversación
            
        Returns:
            Respuesta de Claude o None si hay error
        """
        if not self.is_initialized:
            return " Claude Service no está inicializado"
        
        try:
            # Construir mensajes para la API
            messages = []
            
            # Agregar historial si existe
            if conversation_history:
                messages.extend(conversation_history)
            
            # Agregar mensaje actual si no está ya en el historial
            if not conversation_history or conversation_history[-1]["content"] != message:
                messages.append({"role": "user", "content": message})
            
            # Construir sistema prompt especializado
            system_prompt = self._build_system_prompt()
            
            # Llamar a Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages
            )
            
            if response and response.content:
                return response.content[0].text
            else:
                return " No se recibió respuesta de Claude"
                
        except Exception as e:
            return f" Error comunicándose con Claude: {str(e)}"
    
    def _build_system_prompt(self) -> str:
        """Construir prompt del sistema especializado"""
        return """Eres un asistente especializado en belleza, moda y estilo personal. Tienes acceso a un sistema MCP avanzado que incluye:

 SISTEMA DE BELLEZA:
- Creación de perfiles personalizados basados en características físicas
- Generación de paletas de colores para ropa, maquillaje y accesorios
- Recomendaciones basadas en teoría del color y análisis personal
- Historial de preferencias y paletas generadas

💬 CAPACIDADES ADICIONALES:
- Gestión de archivos y control de versiones
- Acceso a citas inspiracionales y consejos
- Análisis de tendencias y recomendaciones personalizadas

INSTRUCCIONES IMPORTANTES:
1. Cuando el usuario mencione colores, paletas, maquillaje, ropa o estilo, sugiere usar el sistema de belleza MCP
2. Proporciona consejos basados en principios reales de colorimetría y estilismo
3. Sé específico con recomendaciones de colores usando códigos hex cuando sea relevante
4. Considera el contexto (evento, estación, tipo de piel) en tus recomendaciones
5. Si el usuario no tiene perfil, sugiere crear uno para recomendaciones más precisas

EJEMPLOS DE RESPUESTAS:
- "Para recomendaciones personalizadas, te sugiero crear un perfil con /beauty create_profile"
- "Basándome en tu tono de piel [X], te recomendaría colores como..."
- "Para ese evento específico, una paleta de [tipo] sería ideal. ¿Quieres que genere una?"

Mantén un tono amigable, profesional y enfocado en belleza y estilo."""
    
    async def send_beauty_context_message(self, message: str, profile_data: Dict = None, 
                                        palette_history: List = None) -> Optional[str]:
        """
        Enviar mensaje con contexto específico de belleza
        
        Args:
            message: Mensaje del usuario
            profile_data: Datos del perfil de belleza
            palette_history: Historial de paletas
            
        Returns:
            Respuesta contextualizada
        """
        # Construir contexto específico
        context_message = message
        
        if profile_data:
            context_info = f"\n\nCONTEXTO DEL PERFIL:\n"
            context_info += f"- Tono de piel: {profile_data.get('skin_tone', 'No especificado')}\n"
            context_info += f"- Subtono: {profile_data.get('undertone', 'No especificado')}\n"
            context_info += f"- Color de ojos: {profile_data.get('eye_color', 'No especificado')}\n"
            context_info += f"- Color de cabello: {profile_data.get('hair_color', 'No especificado')}\n"
            context_info += f"- Estilo preferido: {profile_data.get('style_preference', 'No especificado')}\n"
            
            context_message += context_info
        
        if palette_history:
            recent_palettes = palette_history[-3:]  # Últimas 3 paletas
            context_message += f"\n\nPALETAS RECIENTES:\n"
            for palette in recent_palettes:
                context_message += f"- {palette.get('palette_type', 'N/A')} para {palette.get('event_type', 'N/A')}\n"
        
        return await self.send_message(context_message)
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimar número de tokens en un texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Estimación de tokens
        """
        # Estimación aproximada: 1 token ≈ 3-4 caracteres para Claude
        return len(text) // 3
    
    async def analyze_color_compatibility(self, user_colors: List[str], suggested_colors: List[str]) -> str:
        """
        Analizar compatibilidad entre colores del usuario y sugeridos
        
        Args:
            user_colors: Colores preferidos del usuario
            suggested_colors: Colores sugeridos por el sistema
            
        Returns:
            Análisis de compatibilidad
        """
        analysis_prompt = f"""Analiza la compatibilidad entre estos colores:

COLORES PREFERIDOS DEL USUARIO: {', '.join(user_colors)}
COLORES SUGERIDOS: {', '.join(suggested_colors)}

Proporciona:
1. Nivel de compatibilidad (Alto/Medio/Bajo)
2. Explicación técnica basada en teoría del color
3. Sugerencias para mejorar la armonía
4. Colores alternativos si es necesario

Respuesta en máximo 200 palabras."""
        
        return await self.send_message(analysis_prompt)
    
    async def generate_style_advice(self, profile: Dict, event_type: str, season: str) -> str:
        """
        Generar consejo de estilo específico
        
        Args:
            profile: Perfil del usuario
            event_type: Tipo de evento
            season: Estación del año
            
        Returns:
            Consejo de estilo personalizado
        """
        advice_prompt = f"""Genera consejos de estilo específicos para:

PERFIL:
- Tono de piel: {profile.get('skin_tone', 'No especificado')}
- Color de ojos: {profile.get('eye_color', 'No especificado')}
- Color de cabello: {profile.get('hair_color', 'No especificado')}
- Estilo preferido: {profile.get('style_preference', 'No especificado')}

CONTEXTO:
- Evento: {event_type}
- Estación: {season}

Proporciona:
1. Paleta de colores específica (con códigos hex)
2. Combinaciones recomendadas de ropa
3. Sugerencias de maquillaje
4. Accesorios complementarios
5. Consejos adicionales de estilo

Sé específico y práctico en las recomendaciones."""
        
        return await self.send_message(advice_prompt)
    
    def set_model(self, model_name: str) -> bool:
        """
        Cambiar modelo de Claude
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            True si el cambio fue exitoso
        """
        valid_models = [
            'claude-3-haiku-20240307',
            'claude-3-sonnet-20240229',
            'claude-3-opus-20240229'
        ]
        
        if model_name in valid_models:
            self.model = model_name
            print(f" Modelo cambiado a: {model_name}")
            return True
        else:
            print(f" Modelo no válido: {model_name}")
            print(f"Modelos disponibles: {', '.join(valid_models)}")
            return False
    
    def get_model_info(self) -> Dict[str, str]:
        """Obtener información del modelo actual"""
        return {
            "model": self.model,
            "max_tokens": str(self.max_tokens),
            "status": "Conectado" if self.is_initialized else "Desconectado"
        }
    
    async def cleanup(self):
        """Limpiar recursos del servicio"""
        self.client = None
        self.is_initialized = False
        print("🧹 Claude Service desconectado")


# Testing del servicio
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    async def test_claude_service():
        load_dotenv()
        
        print(" Testing Claude Service...")
        
        # Inicializar servicio
        service = ClaudeService()
        
        if await service.initialize():
            print(" Servicio inicializado")
            
            # Test básico
            response = await service.send_message("Hola, ¿puedes ayudarme con colores para una fiesta?")
            print(f" Respuesta: {response[:100]}...")
            
            # Test con contexto de belleza
            profile = {
                "skin_tone": "media",
                "eye_color": "cafe",
                "hair_color": "negro",
                "style_preference": "moderno"
            }
            
            context_response = await service.send_beauty_context_message(
                "¿Qué colores me recomiendas para una entrevista?", 
                profile
            )
            print(f" Respuesta contextual: {context_response[:100]}...")
            
            # Info del modelo
            info = service.get_model_info()
            print(f"📊 Info del modelo: {info}")
            
        else:
            print(" Error inicializando servicio")
        
        await service.cleanup()
    
    asyncio.run(test_claude_service())