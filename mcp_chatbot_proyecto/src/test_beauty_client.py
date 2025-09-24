#!/usr/bin/env python3
"""
Cliente de prueba para Beauty Palette MCP Server Local
"""

import asyncio
import subprocess
import json
import sys

class BeautyMCPClient:
    def __init__(self):
        self.server_process = None
        self.msg_id = 0
    
    async def start_server(self):
        """Iniciar servidor MCP"""
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "beauty_mcp_server_local.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Inicializar protocolo MCP
            init_msg = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "BeautyTestClient", "version": "1.0"}
                }
            }
            
            response = await self._send_request(init_msg)
            if response and "result" in response:
                # Enviar initialized notification
                await self._send_notification({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                })
                print("✅ Conectado al servidor MCP")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False
    
    def _next_id(self):
        self.msg_id += 1
        return self.msg_id
    
    async def _send_request(self, message):
        """Enviar request y obtener respuesta"""
        try:
            msg_str = json.dumps(message) + "\n"
            self.server_process.stdin.write(msg_str)
            self.server_process.stdin.flush()
            
            response_line = self.server_process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            return None
        except Exception:
            return None
    
    async def _send_notification(self, message):
        """Enviar notificación"""
        try:
            msg_str = json.dumps(message) + "\n"
            self.server_process.stdin.write(msg_str)
            self.server_process.stdin.flush()
        except Exception:
            pass
    
    async def call_tool(self, tool_name, arguments):
        """Llamar herramienta MCP"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await self._send_request(request)
        if response and "result" in response:
            content = response["result"]["content"]
            if content and len(content) > 0:
                return content[0]["text"]
        
        return "Sin respuesta"
    
    async def demo(self):
        """Ejecutar demo del sistema"""
        print(" Demo del Beauty Palette MCP Server")
        print("=" * 50)
        
        # Crear perfil de prueba
        print("\n1. Creando perfil de prueba...")
        profile_result = await self.call_tool("create_beauty_profile", {
            "user_id": "demo_user",
            "name": "Usuario Demo",
            "skin_tone": "media",
            "undertone": "calido",
            "eye_color": "cafe",
            "hair_color": "castano",
            "style_preference": "moderno"
        })
        print(profile_result)
        
        # Generar paleta de ropa
        print("\n2. Generando paleta de ropa para trabajo...")
        palette_result = await self.call_tool("generate_color_palette", {
            "user_id": "demo_user",
            "palette_type": "ropa",
            "event_type": "trabajo"
        })
        print(palette_result)
        
        # Obtener cita inspiracional
        print("\n3. Obteniendo cita inspiracional...")
        quote_result = await self.call_tool("get_inspirational_quote", {
            "category": "confianza"
        })
        print(quote_result)
        
        # Listar perfiles
        print("\n4. Listando perfiles...")
        list_result = await self.call_tool("list_beauty_profiles", {})
        print(list_result)
    
    def cleanup(self):
        """Limpiar recursos"""
        if self.server_process:
            self.server_process.terminate()

async def main():
    client = BeautyMCPClient()
    
    try:
        if await client.start_server():
            await client.demo()
        else:
            print("❌ No se pudo conectar al servidor")
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrumpido")
    finally:
        client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
