"""
Remote Quotes Service - Servicio para interacción con servidor remoto de citas
"""

import asyncio
import httpx
from typing import Dict, List, Optional, Any


class RemoteQuotesService:
    def __init__(self):
        """Inicializar servicio de citas remotas"""
        self.server_url = "https://web-production-de5ff.up.railway.app"
        self.timeout = 10.0
        self.is_available = False
    
    async def initialize(self) -> bool:
        """Inicializar y verificar conexión con servidor remoto"""
        try:
            health_status = await self.health_check()
            self.is_available = health_status.get("status") == "healthy"
            
            if self.is_available:
                print("Servidor de citas remotas conectado")
                return True
            else:
                print("Servidor de citas remotas no disponible")
                return False
                
        except Exception as e:
            print(f"Error conectando con servidor remoto: {str(e)}")
            self.is_available = False
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar estado del servidor remoto"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.server_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_inspirational_quote(self, category: Optional[str] = None, 
                                    mood: Optional[str] = None, 
                                    time_based: bool = False) -> Dict[str, Any]:
        """
        Obtener cita inspiracional
        
        Args:
            category: Categoría de la cita
            mood: Estado de ánimo
            time_based: Si usar citas basadas en hora del día
            
        Returns:
            Diccionario con la cita y metadatos
        """
        if not self.is_available:
            return {
                "error": "Servidor remoto no disponible",
                "fallback_quote": "La belleza comienza en el momento en que decides ser tú misma",
                "source": "local_fallback"
            }
        
        try:
            params = {}
            if category:
                params["category"] = category
            if mood:
                params["mood"] = mood
            params["time_based"] = str(time_based).lower()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.server_url}/api/quote", params=params)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            return {
                "error": f"Error obteniendo cita: {str(e)}",
                "fallback_quote": "El estilo es una manera de decir quién eres sin tener que hablar",
                "source": "local_fallback"
            }
    
    async def get_sleep_hygiene_tip(self) -> Dict[str, Any]:
        """Obtener consejo de higiene del sueño"""
        if not self.is_available:
            return {
                "error": "Servidor remoto no disponible",
                "fallback_tip": "Establecer una rutina de belleza nocturna puede mejorar tanto tu piel como tu sueño",
                "source": "local_fallback"
            }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.server_url}/api/tip")
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            return {
                "error": f"Error obteniendo consejo: {str(e)}",
                "fallback_tip": "Una buena hidratación es clave tanto para la belleza como para el bienestar",
                "source": "local_fallback"
            }
    
    async def search_quotes(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Buscar citas por palabra clave
        
        Args:
            query: Término de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Diccionario con resultados de búsqueda
        """
        if not self.is_available:
            return {
                "error": "Servidor remoto no disponible",
                "fallback_results": [
                    "La moda se desvanece, pero el estilo es eterno",
                    "La elegancia es la única belleza que nunca se desvanece"
                ],
                "source": "local_fallback"
            }
        
        try:
            params = {"limit": limit}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.server_url}/api/search/{query}", params=params)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            return {
                "error": f"Error en búsqueda: {str(e)}",
                "fallback_results": [f"No se pudo buscar '{query}' en el servidor remoto"],
                "source": "local_fallback"
            }
    
    async def get_wisdom(self, include_tip: bool = True) -> Dict[str, Any]:
        """
        Obtener sabiduría diaria
        
        Args:
            include_tip: Si incluir consejo adicional
            
        Returns:
            Diccionario con sabiduría y consejos
        """
        if not self.is_available:
            return {
                "error": "Servidor remoto no disponible",
                "fallback_wisdom": {
                    "quote": "La confianza es el mejor accesorio que puedes usar",
                    "tip": "Conoce tu paleta de colores personal para siempre verte radiante"
                },
                "source": "local_fallback"
            }
        
        try:
            params = {"include_tip": str(include_tip).lower()}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.server_url}/api/wisdom", params=params)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            return {
                "error": f"Error obteniendo sabiduría: {str(e)}",
                "fallback_wisdom": {
                    "quote": "El verdadero estilo nunca pasa de moda",
                    "tip": "Invierte en piezas de calidad que reflejen tu personalidad"
                },
                "source": "local_fallback"
            }
    
    async def call_mcp_method(self, method: str, params: Dict = None) -> Dict[str, Any]:
        """
        Llamar método MCP específico en el servidor remoto
        
        Args:
            method: Nombre del método MCP
            params: Parámetros del método
            
        Returns:
            Respuesta del servidor
        """
        if not self.is_available:
            return {"error": "Servidor remoto no disponible"}
        
        try:
            payload = {
                "method": method,
                "params": params or {}
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.server_url}/mcp", json=payload)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            return {"error": f"Error en llamada MCP: {str(e)}"}
    
    def format_quote_response(self, quote_data: Dict[str, Any]) -> str:
        """
        Formatear respuesta de cita para mostrar al usuario
        
        Args:
            quote_data: Datos de la cita del servidor
            
        Returns:
            Texto formateado para mostrar
        """
        if "error" in quote_data:
            if "fallback_quote" in quote_data:
                return f"CITA INSPIRACIONAL:\n\"{quote_data['fallback_quote']}\"\n\n(Servidor remoto temporalmente no disponible)"
            else:
                return f"Error: {quote_data['error']}"
        
        # Formatear respuesta exitosa
        if isinstance(quote_data, dict):
            if "quote" in quote_data:
                text = f"CITA INSPIRACIONAL:\n\"{quote_data['quote']}\""
                if "author" in quote_data:
                    text += f"\n- {quote_data['author']}"
                if "category" in quote_data:
                    text += f"\n\nCategoría: {quote_data['category']}"
                return text
            elif "wisdom" in quote_data:
                wisdom = quote_data["wisdom"]
                text = f"SABIDURÍA DIARIA:\n\"{wisdom.get('quote', 'No disponible')}\""
                if "tip" in wisdom:
                    text += f"\n\nConsejo: {wisdom['tip']}"
                return text
        
        return str(quote_data)
    
    def format_search_results(self, search_data: Dict[str, Any]) -> str:
        """
        Formatear resultados de búsqueda
        
        Args:
            search_data: Datos de búsqueda del servidor
            
        Returns:
            Texto formateado con resultados
        """
        if "error" in search_data:
            if "fallback_results" in search_data:
                results = search_data["fallback_results"]
                text = "RESULTADOS DE BÚSQUEDA (local):\n\n"
                for i, result in enumerate(results, 1):
                    text += f"{i}. \"{result}\"\n"
                return text
            else:
                return f"Error en búsqueda: {search_data['error']}"
        
        if "results" in search_data:
            results = search_data["results"]
            if not results:
                return "No se encontraron resultados para la búsqueda"
            
            text = f"RESULTADOS DE BÚSQUEDA ({len(results)} encontrados):\n\n"
            for i, result in enumerate(results, 1):
                if isinstance(result, dict):
                    quote = result.get("quote", result.get("text", str(result)))
                    author = result.get("author", "")
                    text += f"{i}. \"{quote}\""
                    if author:
                        text += f" - {author}"
                    text += "\n"
                else:
                    text += f"{i}. \"{result}\"\n"
            
            return text
        
        return str(search_data)
    
    def format_tip_response(self, tip_data: Dict[str, Any]) -> str:
        """
        Formatear respuesta de consejo
        
        Args:
            tip_data: Datos del consejo del servidor
            
        Returns:
            Texto formateado
        """
        if "error" in tip_data:
            if "fallback_tip" in tip_data:
                return f"CONSEJO DE BELLEZA:\n{tip_data['fallback_tip']}\n\n(Servidor remoto temporalmente no disponible)"
            else:
                return f"Error: {tip_data['error']}"
        
        if "tip" in tip_data:
            text = f"CONSEJO DE BELLEZA:\n{tip_data['tip']}"
            if "category" in tip_data:
                text += f"\n\nCategoría: {tip_data['category']}"
            return text
        
        return str(tip_data)
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Obtener estado de conexión detallado"""
        health = await self.health_check()
        
        return {
            "server_url": self.server_url,
            "is_available": self.is_available,
            "last_check": health,
            "timeout": self.timeout
        }
    
    async def cleanup(self):
        """Limpiar recursos del servicio"""
        self.is_available = False
        print("Servicio de citas remotas desconectado")


# Testing del servicio
if __name__ == "__main__":
    async def test_remote_quotes_service():
        print("Testing Remote Quotes Service...")
        
        # Inicializar servicio
        service = RemoteQuotesService()
        
        if await service.initialize():
            print("Servicio inicializado correctamente")
            
            # Test obtener cita
            quote = await service.get_inspirational_quote(category="motivation")
            formatted_quote = service.format_quote_response(quote)
            print(f"\nCita obtenida:\n{formatted_quote}")
            
            # Test obtener consejo
            tip = await service.get_sleep_hygiene_tip()
            formatted_tip = service.format_tip_response(tip)
            print(f"\nConsejo obtenido:\n{formatted_tip}")
            
            # Test búsqueda
            search_results = await service.search_quotes("beauty", 3)
            formatted_search = service.format_search_results(search_results)
            print(f"\nResultados de búsqueda:\n{formatted_search}")
            
            # Test sabiduría
            wisdom = await service.get_wisdom(True)
            formatted_wisdom = service.format_quote_response(wisdom)
            print(f"\nSabiduría diaria:\n{formatted_wisdom}")
            
            # Estado de conexión
            status = await service.get_connection_status()
            print(f"\nEstado: {status}")
            
        else:
            print("Error inicializando servicio")
        
        await service.cleanup()
    
    asyncio.run(test_remote_quotes_service())