"""
Session Model - Gestión de sesiones de conversación
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional


class SessionModel:
    def __init__(self, max_context_messages: int = 20):
        """
        Inicializar modelo de sesiones
        
        Args:
            max_context_messages: Número máximo de mensajes en contexto
        """
        self.conversation_history = []
        self.max_context_messages = max_context_messages
        self.session_start = datetime.now()
        self.message_count = 0
        
        # Crear directorio de sesiones
        self.sessions_dir = "sessions"
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def add_message(self, role: str, content: str, metadata: Dict = None) -> None:
        """
        Agregar mensaje al historial
        
        Args:
            role: 'user' o 'assistant'
            content: Contenido del mensaje
            metadata: Información adicional opcional
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "message_id": self.message_count
        }
        
        if metadata:
            message.update(metadata)
        
        self.conversation_history.append(message)
        self.message_count += 1
        
        # Mantener solo los últimos N mensajes
        self._trim_context()
    
    def get_context(self) -> List[Dict]:
        """
        Obtener contexto actual para la API
        
        Returns:
            Lista de mensajes formateados para Claude API
        """
        return [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in self.conversation_history
        ]
    
    def get_full_history(self) -> List[Dict]:
        """
        Obtener historial completo con metadata
        
        Returns:
            Lista completa de mensajes
        """
        return self.conversation_history.copy()
    
    def clear_context(self) -> None:
        """Limpiar contexto de conversación"""
        self.conversation_history = []
        self.message_count = 0
        print(" Contexto limpiado. Sesión reiniciada.")
    
    def _trim_context(self) -> None:
        """Mantener solo los últimos N mensajes"""
        if len(self.conversation_history) > self.max_context_messages:
            removed_count = len(self.conversation_history) - self.max_context_messages
            self.conversation_history = self.conversation_history[-self.max_context_messages:]
            print(f"ℹ️  Se removieron {removed_count} mensajes antiguos del contexto")
    
    def get_session_stats(self) -> Dict:
        """
        Obtener estadísticas de la sesión
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.conversation_history:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "session_duration": "0 minutos",
                "messages_in_context": 0
            }
        
        user_msgs = len([msg for msg in self.conversation_history if msg["role"] == "user"])
        assistant_msgs = len([msg for msg in self.conversation_history if msg["role"] == "assistant"])
        
        duration = datetime.now() - self.session_start
        duration_minutes = duration.total_seconds() / 60
        
        return {
            "total_messages": self.message_count,
            "user_messages": user_msgs,
            "assistant_messages": assistant_msgs,
            "session_duration": f"{duration_minutes:.1f} minutos",
            "messages_in_context": len(self.conversation_history)
        }
    
    def save_session(self, filename: str = None) -> bool:
        """
        Guardar sesión en archivo JSON
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            True si se guardó exitosamente
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}.json"
        
        filepath = os.path.join(self.sessions_dir, filename)
        
        session_data = {
            "session_info": {
                "start_time": self.session_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_messages": self.message_count,
                "stats": self.get_session_stats()
            },
            "conversation_history": self.conversation_history
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Sesión guardada en: {filepath}")
            return True
        except Exception as e:
            print(f" Error guardando sesión: {str(e)}")
            return False
    
    def load_session(self, filename: str) -> bool:
        """
        Cargar sesión desde archivo
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            True si se cargó exitosamente
        """
        filepath = os.path.join(self.sessions_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.conversation_history = session_data.get("conversation_history", [])
            self.message_count = session_data.get("session_info", {}).get("total_messages", 0)
            
            print(f" Sesión cargada desde: {filepath}")
            print(f"ℹ️  {len(self.conversation_history)} mensajes restaurados")
            return True
            
        except FileNotFoundError:
            print(f" Archivo no encontrado: {filepath}")
            return False
        except json.JSONDecodeError:
            print(f" Error leyendo archivo JSON: {filepath}")
            return False
        except Exception as e:
            print(f" Error cargando sesión: {str(e)}")
            return False
    
    def list_saved_sessions(self) -> List[str]:
        """
        Listar sesiones guardadas
        
        Returns:
            Lista de nombres de archivos de sesión
        """
        try:
            files = [f for f in os.listdir(self.sessions_dir) if f.endswith('.json')]
            return sorted(files, reverse=True)  # Más recientes primero
        except Exception as e:
            print(f" Error listando sesiones: {str(e)}")
            return []
    
    def show_context_summary(self) -> None:
        """Mostrar resumen del contexto actual"""
        if not self.conversation_history:
            print(" No hay mensajes en el contexto actual")
            return
        
        print("\n RESUMEN DEL CONTEXTO ACTUAL:")
        print("-" * 40)
        
        # Mostrar últimos 5 mensajes
        recent_messages = self.conversation_history[-5:]
        for i, msg in enumerate(recent_messages, 1):
            role_icon = "" if msg["role"] == "user" else "🤖"
            content_preview = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
            print(f"{i}. {role_icon} {content_preview}")
        
        stats = self.get_session_stats()
        print(f"\n📊 Total: {stats['total_messages']} mensajes | En contexto: {stats['messages_in_context']}")


# Funciones de utilidad para testing
if __name__ == "__main__":
    # Test del modelo de sesiones
    session = SessionModel()
    
    print(" Probando SessionModel...")
    
    # Simular conversación
    session.add_message("user", "Hola, soy María")
    session.add_message("assistant", "Hola María, ¿en qué puedo ayudarte?")
    session.add_message("user", "¿Recuerdas mi nombre?")
    session.add_message("assistant", "Sí, tu nombre es María")
    
    # Mostrar contexto
    print("\n Contexto para API:")
    for msg in session.get_context():
        print(f"  {msg['role']}: {msg['content']}")
    
    # Mostrar estadísticas
    print(f"\n📊 Estadísticas: {session.get_session_stats()}")
    
    # Mostrar resumen
    session.show_context_summary()
    
    # Guardar sesión de prueba
    session.save_session("test_session.json")
    
    # Listar sesiones
    print(f"\n📁 Sesiones guardadas: {session.list_saved_sessions()}")