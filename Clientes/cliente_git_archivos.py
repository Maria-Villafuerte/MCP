#!/usr/bin/env python3

import asyncio
import json
import sys
import subprocess
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt
from rich.markdown import Markdown

@dataclass
class MCPServer:
    name: str
    command: List[str]
    process: Optional[subprocess.Popen] = None
    tools: List[Dict[str, Any]] = field(default_factory=list)
    connected: bool = False

class NaturalLanguageProcessor:
    """Procesador de lenguaje natural para interpretar comandos"""
    
    def __init__(self):
        # Patrones para operaciones de Git
        self.git_patterns = {
            r"(?:crear|inicializar|init)\s+(?:repo|repositorio)\s+(?:en\s+)?(.+)": ("git-init", "repo_path"),
            r"(?:crear|agregar|añadir)\s+(?:el\s+)?archivo\s+(.+?)\s+con\s+contenido\s+(.+)": ("git-create-file", "path", "content"),
            r"(?:agregar|añadir|add)\s+(?:el\s+archivo\s+)?(.+)": ("git-add", "paths"),
            r"(?:hacer|realizar|crear)\s+commit\s+(?:con\s+mensaje\s+)?[\"'](.+)[\"'](?:\s+autor\s+(.+))?": ("git-commit", "message"),
            r"(?:ver|mostrar|check)\s+(?:el\s+)?status": ("git-status",),
            r"(?:ver|mostrar|listar)\s+(?:los\s+)?commits?(?:\s+(?:limite|limit)\s+(\d+))?": ("git-log", "limit"),
            r"(?:mostrar|ver)\s+(?:el\s+)?archivo\s+(.+)": ("git-show-file", "path"),
        }
        
        # Patrones para operaciones de filesystem
        self.fs_patterns = {
            r"(?:listar|ver|mostrar)\s+(?:archivos\s+de\s+|contenido\s+de\s+|directorio\s+)?(.+)": ("fs-list-dir", "path"),
            r"(?:leer|ver|mostrar|abrir)\s+(?:el\s+)?archivo\s+(.+)": ("fs-read-file", "path"),
            r"(?:escribir|guardar|crear)\s+(?:en\s+)?(?:el\s+archivo\s+)?(.+?)\s+(?:el\s+contenido\s+)?[\"'](.+)[\"']": ("fs-write-file", "path", "content"),
            r"(?:eliminar|borrar|delete)\s+(?:el\s+archivo\s+|la\s+carpeta\s+)?(.+)": ("fs-delete", "path"),
            r"(?:crear|hacer)\s+(?:el\s+)?(?:directorio|carpeta)\s+(.+)": ("fs-create-dir", "path"),
        }

    def parse_command(self, command: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Parsea un comando en lenguaje natural
        Retorna: (servidor, herramienta, argumentos)
        """
        command = command.lower().strip()
        
        # Intentar patrones de Git
        for pattern, action_data in self.git_patterns.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                tool_name = action_data[0]
                args = {}
                
                # Mapear grupos capturados a argumentos
                for i, arg_name in enumerate(action_data[1:], 1):
                    if i <= len(match.groups()) and match.group(i):
                        value = match.group(i).strip()
                        
                        # Procesamiento especial según el argumento
                        if arg_name == "paths":
                            args[arg_name] = [value]
                        elif arg_name == "remote":
                            args[arg_name] = "remot" in command
                        elif arg_name == "limit" and value.isdigit():
                            args[arg_name] = int(value)
                        else:
                            args[arg_name] = value
                
                return "git", tool_name, args
        
        # Intentar patrones de filesystem
        for pattern, action_data in self.fs_patterns.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                tool_name = action_data[0]
                args = {}
                
                for i, arg_name in enumerate(action_data[1:], 1):
                    if i <= len(match.groups()) and match.group(i):
                        args[arg_name] = match.group(i).strip()
                
                return "filesystem", tool_name, args
        
        return None, None, {}

class MCPClient:
    def __init__(self):
        self.console = Console()
        self.servers: Dict[str, MCPServer] = {}
        self.nlp = NaturalLanguageProcessor()
        
    async def setup_servers(self):
        """Configura y conecta a ambos servidores"""
        # Configurar servidores con las rutas corregidas
        git_server = MCPServer(
            name="git",
            command=["python", "../Servidores/GitHub/server.py"]
        )
        
        fs_server = MCPServer(
            name="filesystem", 
            command=["python", "../Servidores/Manejador_paquetes/server.py"]
        )
        
        self.servers = {
            "git": git_server,
            "filesystem": fs_server
        }
        
        # Intentar conectar a ambos servidores
        for server_name, server in self.servers.items():
            await self.start_server(server)

    async def start_server(self, server: MCPServer) -> bool:
        """Inicia un servidor MCP"""
        try:
            self.console.print(f"[yellow]🚀 Iniciando servidor {server.name}...[/yellow]")
            
            # Verificar que el archivo del servidor existe
            server_path = Path(server.command[1]) if len(server.command) > 1 else None
            if server_path and not server_path.exists():
                raise Exception(f"Archivo del servidor no encontrado: {server_path}")
            
            server.process = subprocess.Popen(
                server.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Esperar un momento para que el servidor se inicie
            await asyncio.sleep(0.5)
            
            # Verificar que el proceso sigue ejecutándose
            if server.process.poll() is not None:
                stderr_output = server.process.stderr.read()
                raise Exception(f"El servidor terminó prematuramente. Error: {stderr_output}")
            
            # Protocolo de inicialización MCP
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "natural-mcp-client", "version": "1.0.0"}
                }
            }
            
            self.console.print(f"[dim]📤 Enviando inicialización a {server.name}...[/dim]")
            await self.send_request(server, init_request)
            
            self.console.print(f"[dim]📥 Esperando respuesta de {server.name}...[/dim]")
            response = await self.read_response(server)
            
            if not response:
                stderr_output = ""
                if server.process.stderr:
                    stderr_output = server.process.stderr.read()
                raise Exception(f"No se recibió respuesta de inicialización. Stderr: {stderr_output}")
            
            if "error" in response:
                raise Exception(f"Error en inicialización: {response['error']}")
                
            if "result" not in response:
                raise Exception(f"Respuesta inválida: {response}")
            
            # Notificación de inicialización completa
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await self.send_notification(server, initialized_notification)
            
            # Obtener herramientas disponibles
            self.console.print(f"[dim]🔧 Obteniendo herramientas de {server.name}...[/dim]")
            await self.list_tools(server)
            
            server.connected = True
            self.console.print(f"[green]✅ Servidor {server.name} conectado ({len(server.tools)} herramientas)[/green]")
            return True
            
        except Exception as e:
            # Mostrar información de diagnóstico
            error_info = str(e)
            if server.process and server.process.stderr:
                stderr_content = server.process.stderr.read()
                if stderr_content:
                    error_info += f"\nStderr: {stderr_content}"
            
            self.console.print(f"[red]❌ Error conectando servidor {server.name}: {error_info}[/red]")
            
            # Limpiar proceso si existe
            if server.process:
                server.process.terminate()
                server.process = None
            
            return False

    async def send_request(self, server: MCPServer, request: Dict[str, Any]):
        """Envía una request JSON-RPC al servidor"""
        message = json.dumps(request) + "\n"
        server.process.stdin.write(message)
        server.process.stdin.flush()

    async def send_notification(self, server: MCPServer, notification: Dict[str, Any]):
        """Envía una notificación JSON-RPC al servidor"""
        message = json.dumps(notification) + "\n"
        server.process.stdin.write(message)
        server.process.stdin.flush()

    async def read_response(self, server: MCPServer) -> Optional[Dict[str, Any]]:
        """Lee una respuesta del servidor"""
        try:
            line = server.process.stdout.readline()
            if line:
                return json.loads(line.strip())
        except Exception as e:
            self.console.print(f"[red]Error leyendo respuesta: {e}[/red]")
        return None

    async def list_tools(self, server: MCPServer):
        """Lista las herramientas disponibles de un servidor"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        await self.send_request(server, request)
        response = await self.read_response(server)
        
        if response and "result" in response and "tools" in response["result"]:
            server.tools = response["result"]["tools"]

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Llama a una herramienta de un servidor específico"""
        server = self.servers[server_name]
        
        if not server.connected:
            return {"error": f"Servidor {server_name} no conectado"}
        
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        await self.send_request(server, request)
        response = await self.read_response(server)
        
        if response and "result" in response:
            # Los servidores devuelven el resultado en content[0].text como JSON
            content = response["result"].get("content", [])
            if content and len(content) > 0:
                try:
                    # Parsear el JSON que viene en el texto
                    result_text = content[0].get("text", "{}")
                    parsed_result = json.loads(result_text)
                    return parsed_result
                except json.JSONDecodeError:
                    return {"error": "Respuesta inválida del servidor"}
            return {"error": "Respuesta vacía del servidor"}
        elif response and "error" in response:
            return {"error": response["error"]}
        else:
            return {"error": "No se recibió respuesta válida"}

    def display_result(self, result: Dict[str, Any], server_name: str, tool_name: str):
        """Muestra el resultado de una operación de manera elegante"""
        
        if "error" in result:
            self.console.print(f"[red]❌ Error: {result['error']}[/red]")
            return
        
        # Procesar resultado según el tipo de herramienta
        if server_name == "git":
            self.display_git_result(result, tool_name)
        elif server_name == "filesystem":
            self.display_fs_result(result, tool_name)
        else:
            # Mostrar resultado genérico
            self.console.print(Panel(
                json.dumps(result, indent=2, ensure_ascii=False),
                title=f"[blue]{server_name}[/blue] - [cyan]{tool_name}[/cyan]",
                border_style="blue"
            ))

    def display_git_result(self, result: Dict[str, Any], tool_name: str):
        """Muestra resultados específicos de Git"""
        if tool_name == "git-status":
            if result.get("files"):
                self.console.print("[green]📁 Estado del repositorio:[/green]")
                for file_info in result["files"]:
                    status = file_info["status"]
                    filename = file_info["file"]
                    self.console.print(f"  [yellow]{status}[/yellow] {filename}")
            else:
                self.console.print("[green]✅ Repositorio limpio[/green]")
                
        elif tool_name == "git-log":
            self.console.print("[green]📝 Commits recientes:[/green]")
            for commit in result.get("commits", []):
                self.console.print(f"  • [yellow]{commit['hash'][:8]}[/yellow] - {commit['subject']} ([dim]{commit['author']}[/dim])")
                
        elif tool_name == "git-show-file":
            if "content" in result:
                self.console.print(Panel(
                    Syntax(result["content"], "text", theme="monokai", line_numbers=True),
                    title=f"[cyan]📄 {result.get('path', 'archivo')}[/cyan]",
                    border_style="cyan"
                ))
            else:
                self.console.print(f"[red]No se pudo mostrar el archivo[/red]")
                
        else:
            # Resultado genérico para otras operaciones de Git
            if result.get("success"):
                message = result.get("message", f"{tool_name} ejecutado correctamente")
                self.console.print(f"[green]✅ {message}[/green]")
                if "stdout" in result and result["stdout"]:
                    self.console.print(f"[dim]{result['stdout']}[/dim]")
            else:
                error = result.get("error", "Error desconocido")
                self.console.print(f"[red]❌ Error en {tool_name}: {error}[/red]")
                if "stderr" in result and result["stderr"]:
                    self.console.print(f"[dim]{result['stderr']}[/dim]")

    def display_fs_result(self, result: Dict[str, Any], tool_name: str):
        """Muestra resultados específicos del sistema de archivos"""
        if tool_name == "fs-list-dir":
            if result.get("success"):
                self.console.print(f"[green]📁 Contenido de {result.get('path', 'directorio')}:[/green]")
                
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Nombre", style="cyan")
                table.add_column("Tipo", style="green")
                table.add_column("Tamaño", style="yellow", justify="right")
                
                for file_info in result.get("files", []):
                    file_type = "📁 Dir" if file_info["is_dir"] else "📄 Archivo"
                    size = f"{file_info['size']} bytes" if not file_info["is_dir"] else "-"
                    table.add_row(file_info["name"], file_type, size)
                
                self.console.print(table)
            else:
                error = result.get("error", "Error desconocido")
                self.console.print(f"[red]❌ Error listando directorio: {error}[/red]")
            
        elif tool_name == "fs-read-file":
            if result.get("success"):
                if "content" in result:
                    # Detectar tipo de archivo para syntax highlighting
                    path = result.get("path", "")
                    extension = Path(path).suffix.lower()
                    
                    language_map = {
                        ".py": "python", ".js": "javascript", ".json": "json",
                        ".html": "html", ".css": "css", ".md": "markdown",
                        ".yml": "yaml", ".yaml": "yaml", ".xml": "xml"
                    }
                    
                    language = language_map.get(extension, "text")
                    
                    self.console.print(Panel(
                        Syntax(result["content"], language, theme="monokai", line_numbers=True),
                        title=f"[cyan]📄 {Path(path).name}[/cyan]",
                        border_style="cyan"
                    ))
                else:
                    self.console.print("[red]No se pudo leer el archivo[/red]")
            else:
                error = result.get("error", "Error desconocido")
                self.console.print(f"[red]❌ Error leyendo archivo: {error}[/red]")
                
        else:
            # Resultado genérico para otras operaciones
            if result.get("success"):
                message = result.get("message", f"{tool_name} ejecutado correctamente")
                self.console.print(f"[green]✅ {message}[/green]")
            else:
                error = result.get("error", "Error desconocido")
                self.console.print(f"[red]❌ Error en {tool_name}: {error}[/red]")

    async def process_command(self, command: str):
        """Procesa un comando en lenguaje natural"""
        server_name, tool_name, arguments = self.nlp.parse_command(command)
        
        if not server_name or not tool_name:
            self.console.print("[red]❓ No pude entender el comando. Prueba con algo como:[/red]")
            self.console.print("  • [cyan]crear repo en mi_proyecto[/cyan]")
            self.console.print("  • [cyan]ver archivos de src[/cyan]")
            self.console.print("  • [cyan]hacer commit con mensaje 'Initial commit'[/cyan]")
            self.console.print("  • [cyan]leer archivo package.json[/cyan]")
            return
        
        self.console.print(f"[dim]🔄 Ejecutando {tool_name} en servidor {server_name}...[/dim]")
        
        # Ejecutar la herramienta
        result = await self.call_tool(server_name, tool_name, arguments)
        
        # Mostrar resultado
        self.display_result(result, server_name, tool_name)

    def show_help(self):
        """Muestra la ayuda del cliente"""
        help_text = """
# 🤖 Cliente MCP con Lenguaje Natural

## Comandos de Git disponibles:
- **crear repo en [ruta]** - Inicializa un repositorio
- **crear archivo [ruta] con contenido [texto]** - Crea un archivo
- **agregar [archivo]** - Añade archivo al staging
- **hacer commit con mensaje '[mensaje]'** - Realiza commit
- **ver status** - Muestra estado del repo
- **listar ramas** - Lista ramas disponibles
- **ver commits** - Muestra commits recientes
- **mostrar archivo [ruta]** - Muestra contenido de archivo
- **buscar '[patrón]'** - Busca texto en el repo
- **configurar remoto [url]** - Configura repositorio remoto
- **hacer push** - Sube cambios al remoto
- **crear rama [nombre]** - Crea nueva rama

## Comandos de Sistema de Archivos:
- **ver archivos de [directorio]** - Lista archivos
- **leer archivo [ruta]** - Lee contenido de archivo
- **escribir archivo [ruta] '[contenido]'** - Crea/modifica archivo
- **eliminar [archivo/directorio]** - Elimina archivo o directorio

## Comandos especiales:
- **help** - Muestra esta ayuda
- **status** - Estado de conexión de servidores
- **exit** - Salir del cliente
        """
        self.console.print(Markdown(help_text))

    def show_status(self):
        """Muestra el estado de conexión de los servidores"""
        table = Table(title="📊 Estado de Servidores MCP")
        table.add_column("Servidor", style="cyan")
        table.add_column("Estado", style="green")
        table.add_column("Herramientas", justify="right", style="yellow")
        
        for name, server in self.servers.items():
            status = "🟢 Conectado" if server.connected else "🔴 Desconectado"
            tools_count = str(len(server.tools)) if server.tools else "0"
            table.add_row(name, status, tools_count)
        
        self.console.print(table)

    async def interactive_mode(self):
        """Modo interactivo del cliente"""
        self.console.print(Panel(
            "[bold green]🎯 Cliente MCP con Lenguaje Natural[/bold green]\n"
            "Escribe comandos en español natural. Usa '[cyan]help[/cyan]' para ver ejemplos.",
            border_style="green"
        ))
        
        while True:
            try:
                command = Prompt.ask("\n[bold blue]MCP[/bold blue]", default="help").strip()
                
                if command.lower() in ["exit", "quit", "salir"]:
                    self.console.print("[yellow]👋 ¡Hasta luego![/yellow]")
                    break
                elif command.lower() in ["help", "ayuda"]:
                    self.show_help()
                elif command.lower() == "status":
                    self.show_status()
                else:
                    await self.process_command(command)
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]👋 Saliendo...[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error: {e}[/red]")

    async def cleanup(self):
        """Limpia recursos y cierra conexiones"""
        for server in self.servers.values():
            if server.process:
                server.process.terminate()
                server.process.wait()

async def main():
    client = MCPClient()
    
    try:
        # Configurar servidores
        await client.setup_servers()
        
        # Verificar que al menos un servidor esté conectado
        connected_servers = [s for s in client.servers.values() if s.connected]
        if not connected_servers:
            client.console.print("[red]❌ No se pudo conectar a ningún servidor. Verifica que los servidores estén disponibles.[/red]")
            return
        
        # Modo interactivo
        await client.interactive_mode()
        
    finally:
        await client.cleanup()

if __name__ == "__main__":
    # Instalar dependencias requeridas si no están disponibles
    try:
        import rich
    except ImportError:
        print("Instalando rich...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
        import rich
    
    asyncio.run(main())