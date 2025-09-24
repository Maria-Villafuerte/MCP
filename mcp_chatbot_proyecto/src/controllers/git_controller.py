"""
Git Controller - Controlador para gestión de archivos y control de versiones
"""

import os
import subprocess
import tempfile
from typing import Optional
from pathlib import Path
from models.logging_model import LoggingModel


class GitController:
    def __init__(self, logging_model: LoggingModel):
        """
        Inicializar controlador de git y filesystem
        
        Args:
            logging_model: Modelo de logging
        """
        self.logging_model = logging_model
        self.workspace_dir = Path("mcp_workspace")
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Inicializar controlador y crear workspace"""
        try:
            # Crear directorio de trabajo
            self.workspace_dir.mkdir(exist_ok=True)
            
            # Verificar si git está disponible
            self.git_available = self._check_git_availability()
            
            if self.git_available:
                print("Git Controller inicializado - Git disponible")
            else:
                print("Git Controller inicializado - Git no disponible (solo filesystem)")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Error inicializando Git Controller: {str(e)}")
            return False
    
    def _check_git_availability(self) -> bool:
        """Verificar si git está disponible en el sistema"""
        try:
            result = subprocess.run(
                ["git", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def handle_command(self, command: str) -> Optional[str]:
        """
        Manejar comandos de git y filesystem
        
        Args:
            command: Comando completo del usuario
            
        Returns:
            Respuesta formateada
        """
        if not self.is_initialized:
            return "Error: Git Controller no inicializado"
        
        try:
            # Parsear comando
            parts = command.strip().split()
            if len(parts) < 2:
                return self._show_git_help()
            
            main_command = parts[0].lower()  # /git o /fs
            action = parts[1].lower()
            
            # Comandos de filesystem
            if main_command == "/fs":
                return await self._handle_filesystem_command(action, parts[2:])
            
            # Comandos de git
            elif main_command == "/git":
                return await self._handle_git_command(action, parts[2:])
            
            else:
                return "Comando no reconocido. /help"
        
        except Exception as e:
            error_msg = f"Error procesando comando: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "git_filesystem", "command_error", {"command": command}, 
                error=error_msg, success=False
            )
            return error_msg
    
    def _show_git_help(self) -> str:
        """Mostrar ayuda del sistema de git y filesystem"""
        git_status = "disponible" if self.git_available else "no disponible"
        
        return f"""SISTEMA DE ARCHIVOS Y CONTROL DE VERSIONES

COMANDOS DE FILESYSTEM:
  /fs help                     - Mostrar esta ayuda
  /fs read <archivo>           - Leer archivo
  /fs write <archivo> <texto>  - Escribir archivo
  /fs list [directorio]        - Listar contenido de directorio
  /fs delete <archivo>         - Eliminar archivo
  /fs mkdir <directorio>       - Crear directorio
  /fs info <archivo>           - Información del archivo

COMANDOS DE GIT (Git {git_status}):
  /git help                    - Ayuda de git
  /git init                    - Inicializar repositorio
  /git status                  - Estado del repositorio
  /git add [archivo]           - Agregar archivos al staging
  /git commit "<mensaje>"      - Hacer commit
  /git log                     - Ver historial de commits
  /git branch [nombre]         - Crear/listar ramas
  /git reset                   - Reset del staging area

DIRECTORIO DE TRABAJO: {self.workspace_dir}

EJEMPLOS:
  /fs write README.md "# Mi Proyecto"
  /fs read README.md
  /git init
  /git add README.md
  /git commit "Primer commit"
"""
    
    async def _handle_filesystem_command(self, action: str, params: list) -> str:
        """Manejar comandos de filesystem"""
        try:
            if action == "help":
                return self._show_git_help()
            
            elif action == "read":
                if not params:
                    return "Error: Especifica archivo. Uso: /fs read <archivo>"
                return await self._fs_read_file(params[0])
            
            elif action == "write":
                if len(params) < 2:
                    return "Error: Especifica archivo y contenido. Uso: /fs write <archivo> <contenido>"
                filename = params[0]
                content = " ".join(params[1:])
                return await self._fs_write_file(filename, content)
            
            elif action == "list" or action == "ls":
                directory = params[0] if params else "."
                return await self._fs_list_directory(directory)
            
            elif action == "delete" or action == "rm":
                if not params:
                    return "Error: Especifica archivo. Uso: /fs delete <archivo>"
                return await self._fs_delete_file(params[0])
            
            elif action == "mkdir":
                if not params:
                    return "Error: Especifica directorio. Uso: /fs mkdir <directorio>"
                return await self._fs_create_directory(params[0])
            
            elif action == "info":
                if not params:
                    return "Error: Especifica archivo. Uso: /fs info <archivo>"
                return await self._fs_file_info(params[0])
            
            else:
                return f"Acción de filesystem desconocida: {action}"
        
        except Exception as e:
            return f"Error en filesystem: {str(e)}"
    
    async def _handle_git_command(self, action: str, params: list) -> str:
        """Manejar comandos de git"""
        if not self.git_available:
            return "Error: Git no está disponible en el sistema"
        
        try:
            if action == "help":
                return self._show_git_help()
            
            elif action == "init":
                return await self._git_init()
            
            elif action == "status":
                return await self._git_status()
            
            elif action == "add":
                filename = params[0] if params else "."
                return await self._git_add(filename)
            
            elif action == "commit":
                if not params:
                    return "Error: Especifica mensaje. Uso: /git commit \"<mensaje>\""
                message = " ".join(params).strip('"\'')
                return await self._git_commit(message)
            
            elif action == "log":
                return await self._git_log()
            
            elif action == "branch":
                branch_name = params[0] if params else None
                return await self._git_branch(branch_name)
            
            elif action == "reset":
                return await self._git_reset()
            
            else:
                return f"Comando de git desconocido: {action}"
        
        except Exception as e:
            return f"Error en git: {str(e)}"
    
    async def _fs_read_file(self, filename: str) -> str:
        """Leer archivo del filesystem"""
        try:
            file_path = self.workspace_dir / filename
            
            if not file_path.exists():
                return f" Archivo no encontrado: {filename}"
            
            if not file_path.is_file():
                return f" {filename} no es un archivo"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Registrar operación
            self.logging_model.log_mcp_interaction(
                "filesystem", "read_file", {"filename": filename}, 
                result=f"Archivo leído: {len(content)} caracteres", success=True
            )
            
            # Limitar contenido mostrado si es muy largo
            if len(content) > 2000:
                preview = content[:2000] + f"\n\n... [archivo truncado, {len(content)} caracteres totales]"
                return f" Contenido de {filename}:\n\n{preview}"
            else:
                return f" Contenido de {filename}:\n\n{content}"
        
        except Exception as e:
            error_msg = f"Error leyendo archivo: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "filesystem", "read_file", {"filename": filename}, 
                error=error_msg, success=False
            )
            return f" {error_msg}"
    
    async def _fs_write_file(self, filename: str, content: str) -> str:
        """Escribir archivo al filesystem"""
        try:
            file_path = self.workspace_dir / filename
            
            # Crear directorios padre si no existen
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Registrar operación
            self.logging_model.log_mcp_interaction(
                "filesystem", "write_file", 
                {"filename": filename, "content_length": len(content)}, 
                result=f"Archivo escrito: {filename}", success=True
            )
            
            return f" Archivo '{filename}' creado/actualizado ({len(content)} caracteres)"
        
        except Exception as e:
            error_msg = f"Error escribiendo archivo: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "filesystem", "write_file", {"filename": filename}, 
                error=error_msg, success=False
            )
            return f" {error_msg}"
    
    async def _fs_list_directory(self, directory: str) -> str:
        """Listar contenido de directorio"""
        try:
            dir_path = self.workspace_dir / directory
            
            if not dir_path.exists():
                return f" Directorio no encontrado: {directory}"
            
            if not dir_path.is_dir():
                return f" {directory} no es un directorio"
            
            items = []
            for item in sorted(dir_path.iterdir()):
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    items.append(f"📄 {item.name} ({size} bytes)")
            
            if not items:
                result = f" Directorio '{directory}' está vacío"
            else:
                result = f" Contenido de '{directory}':\n\n" + "\n".join(items)
            
            # Registrar operación
            self.logging_model.log_mcp_interaction(
                "filesystem", "list_directory", {"directory": directory}, 
                result=f"{len(items)} elementos listados", success=True
            )
            
            return result
        
        except Exception as e:
            error_msg = f"Error listando directorio: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "filesystem", "list_directory", {"directory": directory}, 
                error=error_msg, success=False
            )
            return f" {error_msg}"
    
    async def _fs_delete_file(self, filename: str) -> str:
        """Eliminar archivo"""
        try:
            file_path = self.workspace_dir / filename
            
            if not file_path.exists():
                return f" Archivo no encontrado: {filename}"
            
            if file_path.is_file():
                file_path.unlink()
                result = f" Archivo '{filename}' eliminado"
            elif file_path.is_dir():
                return f" {filename} es un directorio (usa rmdir para directorios)"
            else:
                return f" {filename} no es un archivo válido"
            
            # Registrar operación
            self.logging_model.log_mcp_interaction(
                "filesystem", "delete_file", {"filename": filename}, 
                result=result, success=True
            )
            
            return result
        
        except Exception as e:
            error_msg = f"Error eliminando archivo: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "filesystem", "delete_file", {"filename": filename}, 
                error=error_msg, success=False
            )
            return f" {error_msg}"
    
    async def _fs_create_directory(self, dirname: str) -> str:
        """Crear directorio"""
        try:
            dir_path = self.workspace_dir / dirname
            
            if dir_path.exists():
                return f"⚠️  Directorio '{dirname}' ya existe"
            
            dir_path.mkdir(parents=True, exist_ok=True)
            
            result = f" Directorio '{dirname}' creado"
            
            # Registrar operación
            self.logging_model.log_mcp_interaction(
                "filesystem", "create_directory", {"dirname": dirname}, 
                result=result, success=True
            )
            
            return result
        
        except Exception as e:
            error_msg = f"Error creando directorio: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "filesystem", "create_directory", {"dirname": dirname}, 
                error=error_msg, success=False
            )
            return f" {error_msg}"
    
    async def _fs_file_info(self, filename: str) -> str:
        """Obtener información del archivo"""
        try:
            file_path = self.workspace_dir / filename
            
            if not file_path.exists():
                return f" Archivo no encontrado: {filename}"
            
            stat = file_path.stat()
            
            info = f"📄 INFORMACIÓN DE '{filename}':\n\n"
            info += f"Tipo: {'Directorio' if file_path.is_dir() else 'Archivo'}\n"
            info += f"Tamaño: {stat.st_size} bytes\n"
            info += f"Modificado: {stat.st_mtime}\n"
            info += f"Ruta completa: {file_path.absolute()}\n"
            
            if file_path.is_file():
                # Información adicional para archivos
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                    info += f"Líneas: {lines}\n"
                except:
                    info += "Líneas: (no legible como texto)\n"
            
            return info
        
        except Exception as e:
            return f" Error obteniendo información: {str(e)}"
    
    async def _git_init(self) -> str:
        """Inicializar repositorio git"""
        return self._run_git_command(["git", "init"], "init")
    
    async def _git_status(self) -> str:
        """Obtener estado del repositorio"""
        return self._run_git_command(["git", "status", "--short"], "status")
    
    async def _git_add(self, filename: str) -> str:
        """Agregar archivo(s) al staging"""
        return self._run_git_command(["git", "add", filename], "add", {"filename": filename})
    
    async def _git_commit(self, message: str) -> str:
        """Hacer commit"""
        return self._run_git_command(["git", "commit", "-m", message], "commit", {"message": message})
    
    async def _git_log(self) -> str:
        """Ver historial de commits"""
        result = self._run_git_command(["git", "log", "--oneline", "-10"], "log")
        if result.startswith(""):
            return result.replace("", " HISTORIAL DE COMMITS:\n\n")
        return result
    
    async def _git_branch(self, branch_name: Optional[str]) -> str:
        """Crear o listar ramas"""
        if branch_name:
            return self._run_git_command(["git", "branch", branch_name], "create_branch", {"branch": branch_name})
        else:
            return self._run_git_command(["git", "branch"], "list_branches")
    
    async def _git_reset(self) -> str:
        """Reset del staging area"""
        return self._run_git_command(["git", "reset"], "reset")
    
    def _run_git_command(self, command: list, action: str, params: dict = None) -> str:
        """Ejecutar comando git y registrar resultado"""
        try:
            result = subprocess.run(
                command,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip() or "Comando ejecutado exitosamente"
                
                # Registrar éxito
                self.logging_model.log_mcp_interaction(
                    "git", action, params or {}, 
                    result=output, success=True
                )
                
                return f" {output}"
            else:
                error = result.stderr.strip() or "Error desconocido"
                
                # Registrar error
                self.logging_model.log_mcp_interaction(
                    "git", action, params or {}, 
                    error=error, success=False
                )
                
                return f" Git error: {error}"
        
        except subprocess.TimeoutExpired:
            error_msg = "Timeout ejecutando comando git"
            self.logging_model.log_mcp_interaction(
                "git", action, params or {}, 
                error=error_msg, success=False
            )
            return f" {error_msg}"
        
        except Exception as e:
            error_msg = f"Error ejecutando git: {str(e)}"
            self.logging_model.log_mcp_interaction(
                "git", action, params or {}, 
                error=error_msg, success=False
            )
            return f" {error_msg}"
    
    async def cleanup(self):
        """Limpiar recursos del controlador"""
        self.is_initialized = False
        print("Git Controller limpiado")


# Testing del controlador
if __name__ == "__main__":
    import asyncio
    from unittest.mock import MagicMock
    
    async def test_git_controller():
        print("Testing Git Controller...")
        
        # Crear mock del logging
        logging_model = MagicMock()
        
        # Inicializar controlador
        controller = GitController(logging_model)
        
        if await controller.initialize():
            print("Controlador inicializado")
            
            # Test filesystem
            write_response = await controller.handle_command("/fs write test.txt Hello World")
            print(f"Write: {write_response}")
            
            read_response = await controller.handle_command("/fs read test.txt")
            print(f"Read: {read_response[:50]}...")
            
            list_response = await controller.handle_command("/fs list")
            print(f"List: {list_response[:50]}...")
            
            # Test git si está disponible
            if controller.git_available:
                git_status = await controller.handle_command("/git status")
                print(f"Git status: {git_status[:50]}...")
            
            print("Git Controller funcionando correctamente")
        else:
            print("Error inicializando controlador")
        
        await controller.cleanup()
    
    asyncio.run(test_git_controller())