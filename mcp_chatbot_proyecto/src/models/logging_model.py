"""
Logging Model - Sistema de logging para interacciones MCP y generales
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class LoggingModel:
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        Inicializar sistema de logging
        
        Args:
            log_dir: Directorio de logs
            log_level: Nivel de logging
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Archivos de log
        self.log_file = self.log_dir / "interactions.log"
        self.mcp_log_file = self.log_dir / "mcp_interactions.json"
        self.beauty_log_file = self.log_dir / "beauty_interactions.json"
        self.errors_log_file = self.log_dir / "errors.log"
        
        # Configurar logging principal
        self._setup_logging(log_level)
        
        # Listas en memoria para interacciones
        self.mcp_interactions = []
        self.beauty_interactions = []
        
        # Cargar interacciones existentes
        self._load_existing_logs()
    
    def _setup_logging(self, log_level: str) -> None:
        """Configurar sistema de logging"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Logger principal
        self.logger = logging.getLogger('MCPChatbot')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Handler para archivo general
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # Handler para errores
        error_handler = logging.FileHandler(self.errors_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Handler para consola (solo WARNING y ERROR)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        
        # Limpiar handlers existentes
        self.logger.handlers = []
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def _load_existing_logs(self) -> None:
        """Cargar logs existentes desde archivos"""
        try:
            # Cargar interacciones MCP
            if self.mcp_log_file.exists():
                with open(self.mcp_log_file, 'r', encoding='utf-8') as f:
                    self.mcp_interactions = json.load(f)
            
            # Cargar interacciones de belleza
            if self.beauty_log_file.exists():
                with open(self.beauty_log_file, 'r', encoding='utf-8') as f:
                    self.beauty_interactions = json.load(f)
                    
        except Exception as e:
            self.logger.warning(f"No se pudieron cargar logs previos: {e}")
            self.mcp_interactions = []
            self.beauty_interactions = []
    
    def log_user_input(self, message: str, session_id: str = None) -> None:
        """Registrar entrada del usuario"""
        self.logger.info(f"USER_INPUT | Session: {session_id} | Message: {message[:100]}...")
    
    def log_claude_response(self, response: str, tokens_used: int = None, session_id: str = None) -> None:
        """Registrar respuesta de Claude"""
        response_preview = response[:200] + "..." if len(response) > 200 else response
        token_info = f" | Tokens: {tokens_used}" if tokens_used else ""
        self.logger.info(f"CLAUDE_RESPONSE | Session: {session_id}{token_info} | Response: {response_preview}")
    
    def log_mcp_interaction(self, server_name: str, action: str, parameters: Dict = None, 
                           result: Any = None, success: bool = True, error: str = None) -> None:
        """
        Registrar interacciones con servidores MCP
        
        Args:
            server_name: Nombre del servidor MCP
            action: Acción realizada
            parameters: Parámetros enviados
            result: Resultado obtenido
            success: Si fue exitosa
            error: Mensaje de error
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'server': server_name,
            'action': action,
            'parameters': parameters or {},
            'success': success,
            'result': self._sanitize_result(result) if success else None,
            'error': error if not success else None
        }
        
        # Agregar a lista en memoria
        self.mcp_interactions.append(interaction)
        
        # Mantener solo las últimas 1000 interacciones
        if len(self.mcp_interactions) > 1000:
            self.mcp_interactions = self.mcp_interactions[-1000:]
        
        # Guardar en archivo
        self._save_mcp_interactions()
        
        # Log en archivo principal
        status = "SUCCESS" if success else "ERROR"
        log_msg = f"MCP_INTERACTION | {status} | Server: {server_name} | Action: {action}"
        
        if success:
            self.logger.info(log_msg + f" | Result: {str(result)[:100]}...")
        else:
            self.logger.error(log_msg + f" | Error: {error}")
    
    def log_beauty_interaction(self, action: str, user_id: str = None, 
                              palette_type: str = None, result: Any = None, 
                              success: bool = True, error: str = None) -> None:
        """
        Registrar interacciones específicas del sistema de belleza
        
        Args:
            action: Acción realizada (create_profile, generate_palette, etc.)
            user_id: ID del usuario
            palette_type: Tipo de paleta si aplica
            result: Resultado obtenido
            success: Si fue exitosa
            error: Mensaje de error
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_id': user_id,
            'palette_type': palette_type,
            'success': success,
            'result': self._sanitize_result(result) if success else None,
            'error': error if not success else None
        }
        
        # Agregar a lista en memoria
        self.beauty_interactions.append(interaction)
        
        # Mantener solo las últimas 500 interacciones
        if len(self.beauty_interactions) > 500:
            self.beauty_interactions = self.beauty_interactions[-500:]
        
        # Guardar en archivo
        self._save_beauty_interactions()
        
        # Log en archivo principal
        status = "SUCCESS" if success else "ERROR"
        log_msg = f"BEAUTY_INTERACTION | {status} | Action: {action} | User: {user_id}"
        
        if success:
            self.logger.info(log_msg + f" | Type: {palette_type}")
        else:
            self.logger.error(log_msg + f" | Error: {error}")
    
    def _sanitize_result(self, result: Any) -> Any:
        """Sanitizar resultado para evitar logs muy largos"""
        if isinstance(result, str) and len(result) > 1000:
            return result[:1000] + f"... [truncado, {len(result)} caracteres totales]"
        elif isinstance(result, (list, dict)):
            result_str = json.dumps(result, indent=2)
            if len(result_str) > 1000:
                return f"[Objeto grande truncado: {type(result).__name__} con {len(str(result))} elementos]"
        return result
    
    def _save_mcp_interactions(self) -> None:
        """Guardar interacciones MCP en archivo"""
        try:
            with open(self.mcp_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.mcp_interactions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error guardando interacciones MCP: {e}")
    
    def _save_beauty_interactions(self) -> None:
        """Guardar interacciones de belleza en archivo"""
        try:
            with open(self.beauty_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.beauty_interactions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error guardando interacciones de belleza: {e}")
    
    def show_interaction_log(self, lines: int = 50) -> None:
        """Mostrar las últimas líneas del log de interacciones"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            print(f"\n{'='*60}")
            print(f"📄 LOG DE INTERACCIONES (últimas {lines} líneas)")
            print(f"{'='*60}")
            
            for line in all_lines[-lines:]:
                print(line.rstrip())
            
            print(f"{'='*60}\n")
            
        except FileNotFoundError:
            print(" No hay log de interacciones disponible aún.")
    
    def show_mcp_interactions(self, server_filter: str = None, limit: int = 20) -> None:
        """Mostrar interacciones MCP recientes"""
        interactions = self.mcp_interactions
        
        # Filtrar por servidor si se especifica
        if server_filter:
            interactions = [i for i in interactions if i['server'] == server_filter]
        
        # Tomar las más recientes
        recent_interactions = interactions[-limit:]
        
        print(f"\n{'='*60}")
        print(f"🔧 INTERACCIONES MCP (últimas {len(recent_interactions)})")
        if server_filter:
            print(f"📡 Servidor: {server_filter}")
        print(f"{'='*60}")
        
        for interaction in recent_interactions:
            timestamp = datetime.fromisoformat(interaction['timestamp'])
            status_icon = "" if interaction['success'] else ""
            
            print(f"\n{status_icon} {timestamp.strftime('%H:%M:%S')} | {interaction['server']} | {interaction['action']}")
            
            if interaction['parameters']:
                params_str = json.dumps(interaction['parameters'], ensure_ascii=False)[:100]
                print(f"   📥 Parámetros: {params_str}...")
            
            if interaction['success'] and interaction['result']:
                result_str = str(interaction['result'])[:200]
                print(f"   📤 Resultado: {result_str}...")
            elif not interaction['success']:
                print(f"    Error: {interaction['error']}")
        
        print(f"{'='*60}\n")
    
    def show_beauty_interactions(self, user_filter: str = None, limit: int = 15) -> None:
        """Mostrar interacciones de belleza recientes"""
        interactions = self.beauty_interactions
        
        # Filtrar por usuario si se especifica
        if user_filter:
            interactions = [i for i in interactions if i.get('user_id') == user_filter]
        
        # Tomar las más recientes
        recent_interactions = interactions[-limit:]
        
        print(f"\n{'='*60}")
        print(f" INTERACCIONES DE BELLEZA (últimas {len(recent_interactions)})")
        if user_filter:
            print(f" Usuario: {user_filter}")
        print(f"{'='*60}")
        
        for interaction in recent_interactions:
            timestamp = datetime.fromisoformat(interaction['timestamp'])
            status_icon = "" if interaction['success'] else ""
            
            print(f"\n{status_icon} {timestamp.strftime('%H:%M:%S')} | {interaction['action']}")
            print(f"    Usuario: {interaction.get('user_id', 'N/A')}")
            
            if interaction.get('palette_type'):
                print(f"    Tipo: {interaction['palette_type']}")
            
            if interaction['success'] and interaction['result']:
                result_str = str(interaction['result'])[:150]
                print(f"   📤 Resultado: {result_str}...")
            elif not interaction['success']:
                print(f"    Error: {interaction['error']}")
        
        print(f"{'='*60}\n")
    
    def get_mcp_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso de servidores MCP"""
        if not self.mcp_interactions:
            return {
                "total_interactions": 0,
                "servers_used": [],
                "success_rate": 0,
                "most_used_server": None
            }
        
        total = len(self.mcp_interactions)
        successful = len([i for i in self.mcp_interactions if i['success']])
        servers = list(set(i['server'] for i in self.mcp_interactions))
        
        # Conteo por servidor
        server_counts = {}
        for interaction in self.mcp_interactions:
            server = interaction['server']
            server_counts[server] = server_counts.get(server, 0) + 1
        
        return {
            "total_interactions": total,
            "successful_interactions": successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "servers_used": servers,
            "interactions_per_server": server_counts,
            "most_used_server": max(server_counts.items(), key=lambda x: x[1])[0] if server_counts else None
        }
    
    def get_beauty_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de belleza"""
        if not self.beauty_interactions:
            return {
                "total_interactions": 0,
                "users_count": 0,
                "success_rate": 0,
                "most_common_action": None
            }
        
        total = len(self.beauty_interactions)
        successful = len([i for i in self.beauty_interactions if i['success']])
        users = list(set(i.get('user_id') for i in self.beauty_interactions if i.get('user_id')))
        
        # Conteo por acción
        action_counts = {}
        for interaction in self.beauty_interactions:
            action = interaction['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_interactions": total,
            "successful_interactions": successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "users_count": len(users),
            "actions_count": action_counts,
            "most_common_action": max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else None
        }
    
    def export_logs(self, output_dir: str = "exported_logs") -> bool:
        """Exportar todos los logs a un directorio"""
        try:
            export_path = Path(output_dir)
            export_path.mkdir(exist_ok=True)
            
            # Copiar archivos de log
            import shutil
            
            if self.log_file.exists():
                shutil.copy2(self.log_file, export_path / "interactions.log")
            
            if self.mcp_log_file.exists():
                shutil.copy2(self.mcp_log_file, export_path / "mcp_interactions.json")
            
            if self.beauty_log_file.exists():
                shutil.copy2(self.beauty_log_file, export_path / "beauty_interactions.json")
            
            if self.errors_log_file.exists():
                shutil.copy2(self.errors_log_file, export_path / "errors.log")
            
            # Crear resumen de estadísticas
            stats = {
                "export_date": datetime.now().isoformat(),
                "mcp_stats": self.get_mcp_stats(),
                "beauty_stats": self.get_beauty_stats()
            }
            
            with open(export_path / "stats_summary.json", 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            print(f"📦 Logs exportados a: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando logs: {e}")
            return False


# Testing del sistema de logging
if __name__ == "__main__":
    logger = LoggingModel()
    
    print(" Testing Logging Model...")
    
    # Simular interacciones
    logger.log_user_input("Crear perfil de belleza", "session_123")
    logger.log_beauty_interaction("create_profile", "maria_123", success=True, result="Perfil creado")
    logger.log_mcp_interaction("beauty_server", "generate_palette", {"type": "ropa"}, "Paleta generada")
    logger.log_claude_response("He creado tu perfil de belleza", 45, "session_123")
    
    # Mostrar estadísticas
    print(f"\n📊 Estadísticas MCP: {logger.get_mcp_stats()}")
    print(f" Estadísticas Beauty: {logger.get_beauty_stats()}")
    
    print(" Logging Model funcionando correctamente")