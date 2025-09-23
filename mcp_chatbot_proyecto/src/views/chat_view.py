"""
Chat View - Vista principal para la interfaz de chat
"""

from typing import Optional


class ChatView:
    def __init__(self):
        """Inicializar vista del chat"""
        self.colors = {
            'header': '\033[95m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'end': '\033[0m',
            'bold': '\033[1m',
            'underline': '\033[4m'
        }
    
    def show_welcome_message(self) -> None:
        """Mostrar mensaje de bienvenida completo"""
        welcome_text = f"""
{self.colors['cyan']}╔══════════════════════════════════════════════════════════════╗
║                   {self.colors['bold']}MCPChatbot - Sistema de Belleza{self.colors['end']}{self.colors['cyan']}           ║
║              {self.colors['bold']}Chat Inteligente con Claude API{self.colors['end']}{self.colors['cyan']}                ║
╠══════════════════════════════════════════════════════════════╣
║  {self.colors['green']}🤖 Claude API Integration{self.colors['cyan']}                                   ║
║  {self.colors['green']} Sistema de Paletas de Colores Avanzado{self.colors['cyan']}                  ║
║  {self.colors['green']} Recomendaciones de Belleza Personalizadas{self.colors['cyan']}               ║
║  {self.colors['green']} Gestión de Perfiles y Historial{self.colors['cyan']}                         ║
║  {self.colors['green']}🌐 Servidor de Citas Remotas{self.colors['cyan']}                               ║
║  {self.colors['green']}📁 Gestión de Archivos y Git{self.colors['cyan']}                               ║
╚══════════════════════════════════════════════════════════════╝{self.colors['end']}

{self.colors['yellow']}💬 Puedes hacer preguntas normales o usar comandos especiales:{self.colors['end']}

{self.colors['bold']} COMANDOS PRINCIPALES:{self.colors['end']}
{self.colors['blue']}  /help{self.colors['end']}        - Mostrar ayuda completa
{self.colors['blue']}  /beauty help{self.colors['end']} - Sistema de belleza y paletas
{self.colors['blue']}  /quotes help{self.colors['end']} - Citas inspiracionales
{self.colors['blue']}  /git help{self.colors['end']}    - Gestión de archivos y git
{self.colors['blue']}  /stats{self.colors['end']}       - Estadísticas del sistema
{self.colors['blue']}  /quit{self.colors['end']}        - Salir del chatbot

{self.colors['bold']} COMANDOS RÁPIDOS DE BELLEZA:{self.colors['end']}
{self.colors['green']}  /beauty create_profile{self.colors['end']} - Crear perfil personal
{self.colors['green']}  /palette ropa{self.colors['end']}          - Generar paleta de ropa
{self.colors['green']}  /palette maquillaje{self.colors['end']}    - Generar paleta de maquillaje
{self.colors['green']}  /beauty history{self.colors['end']}        - Ver historial de paletas

{self.colors['yellow']} Ejemplo: "Ayúdame a elegir colores para una entrevista de trabajo"
{self.colors['yellow']} Ejemplo: "/beauty create_profile" para crear tu perfil personalizado{self.colors['end']}

{self.colors['cyan']}{'='*60}{self.colors['end']}
"""
        print(welcome_text)
    
    def get_user_input(self) -> str:
        """Obtener entrada del usuario"""
        try:
            user_input = input(f"\n{self.colors['bold']} Tú:{self.colors['end']} ").strip()
            return user_input
        except (KeyboardInterrupt, EOFError):
            return "/quit"
    
    def show_response(self, response: str) -> None:
        """Mostrar respuesta del sistema"""
        print(f"\n{self.colors['bold']}{self.colors['green']}🤖 Claude:{self.colors['end']} {response}")
    
    def show_error(self, error_message: str) -> None:
        """Mostrar mensaje de error"""
        print(f"\n{self.colors['red']} Error:{self.colors['end']} {error_message}")
    
    def show_success(self, success_message: str) -> None:
        """Mostrar mensaje de éxito"""
        print(f"\n{self.colors['green']} Éxito:{self.colors['end']} {success_message}")
    
    def show_warning(self, warning_message: str) -> None:
        """Mostrar mensaje de advertencia"""
        print(f"\n{self.colors['yellow']}⚠️  Advertencia:{self.colors['end']} {warning_message}")
    
    def show_info(self, info_message: str) -> None:
        """Mostrar mensaje informativo"""
        print(f"\n{self.colors['blue']}ℹ️  Info:{self.colors['end']} {info_message}")
    
    def show_thinking(self) -> None:
        """Mostrar indicador de procesamiento"""
        print(f"\n{self.colors['yellow']}🤔 Procesando...{self.colors['end']}")
    
    def show_goodbye(self) -> None:
        """Mostrar mensaje de despedida"""
        goodbye_text = f"""
{self.colors['cyan']}╔══════════════════════════════════════════════════════════════╗
║                         {self.colors['bold']}¡Hasta luego!{self.colors['end']}{self.colors['cyan']}                         ║
║                                                              ║
║    {self.colors['green']}Gracias por usar MCPChatbot - Sistema de Belleza{self.colors['cyan']}         ║
║                                                              ║
║    {self.colors['yellow']}💾 Tu sesión ha sido guardada automáticamente{self.colors['cyan']}           ║
║    {self.colors['yellow']} Tus perfiles de belleza están seguros{self.colors['cyan']}                ║
║    {self.colors['yellow']}📊 Los logs están disponibles para revisión{self.colors['cyan']}             ║
║                                                              ║
║              {self.colors['bold']}¡Vuelve pronto para más belleza!{self.colors['end']}{self.colors['cyan']}              ║
╚══════════════════════════════════════════════════════════════╝{self.colors['end']}
"""
        print(goodbye_text)
    
    def get_help_message(self) -> str:
        """Obtener mensaje de ayuda completa"""
        help_text = f"""{self.colors['bold']} COMANDOS DISPONIBLES:{self.colors['end']}

{self.colors['cyan']} SISTEMA DE BELLEZA:{self.colors['end']}
{self.colors['blue']}  /beauty help{self.colors['end']}                    - Ayuda del sistema de belleza
{self.colors['blue']}  /beauty create_profile{self.colors['end']}          - Crear perfil personalizado
{self.colors['blue']}  /beauty profile <user_id>{self.colors['end']}       - Ver perfil específico
{self.colors['blue']}  /beauty list_profiles{self.colors['end']}           - Listar todos los perfiles
{self.colors['blue']}  /beauty history <user_id>{self.colors['end']}       - Ver historial de paletas
{self.colors['blue']}  /palette ropa{self.colors['end']}                   - Generar paleta de ropa
{self.colors['blue']}  /palette maquillaje{self.colors['end']}             - Generar paleta de maquillaje
{self.colors['blue']}  /palette accesorios{self.colors['end']}             - Generar paleta de accesorios

{self.colors['cyan']}🌐 CITAS INSPIRACIONALES:{self.colors['end']}
{self.colors['blue']}  /quotes help{self.colors['end']}                    - Ayuda de citas
{self.colors['blue']}  /quotes get{self.colors['end']}                     - Obtener cita inspiracional
{self.colors['blue']}  /quotes tip{self.colors['end']}                     - Consejo de belleza
{self.colors['blue']}  /quotes search <palabra>{self.colors['end']}        - Buscar citas
{self.colors['blue']}  /quotes wisdom{self.colors['end']}                  - Sabiduría diaria

{self.colors['cyan']}📁 GESTIÓN DE ARCHIVOS Y GIT:{self.colors['end']}
{self.colors['blue']}  /git help{self.colors['end']}                       - Ayuda de git
{self.colors['blue']}  /fs read <archivo>{self.colors['end']}              - Leer archivo
{self.colors['blue']}  /fs write <archivo> <contenido>{self.colors['end']} - Escribir archivo
{self.colors['blue']}  /fs list [directorio]{self.colors['end']}           - Listar archivos
{self.colors['blue']}  /git init{self.colors['end']}                       - Inicializar repositorio
{self.colors['blue']}  /git add{self.colors['end']}                        - Agregar cambios
{self.colors['blue']}  /git commit "<mensaje>"{self.colors['end']}         - Hacer commit

{self.colors['cyan']}🔧 SISTEMA:{self.colors['end']}
{self.colors['blue']}  /stats{self.colors['end']}                          - Estadísticas de uso
{self.colors['blue']}  /log{self.colors['end']}                            - Ver log de interacciones
{self.colors['blue']}  /mcp{self.colors['end']}                            - Ver interacciones MCP
{self.colors['blue']}  /context{self.colors['end']}                        - Ver resumen del contexto
{self.colors['blue']}  /clear{self.colors['end']}                          - Limpiar contexto
{self.colors['blue']}  /save{self.colors['end']}                           - Guardar sesión
{self.colors['blue']}  /quit{self.colors['end']}                           - Salir del sistema

{self.colors['cyan']} EJEMPLOS DE USO:{self.colors['end']}
{self.colors['green']}  "¿Qué colores me quedan bien para una cita?"{self.colors['end']}
{self.colors['green']}  "Ayúdame a crear un look profesional"{self.colors['end']}
{self.colors['green']}  "/beauty create_profile"{self.colors['end']}
{self.colors['green']}  "/palette ropa casual verano"{self.colors['end']}
{self.colors['green']}  "/quotes get motivacion"{self.colors['end']}

{self.colors['yellow']} El sistema aprende de tus preferencias para darte mejores recomendaciones{self.colors['end']}"""
        
        return help_text
    
    def prompt_for_input(self, prompt: str, required: bool = False) -> Optional[str]:
        """
        Solicitar entrada específica del usuario
        
        Args:
            prompt: Texto del prompt
            required: Si la entrada es obligatoria
            
        Returns:
            Entrada del usuario o None si no es requerida y está vacía
        """
        while True:
            try:
                response = input(f"{self.colors['yellow']}{prompt}{self.colors['end']}: ").strip()
                
                if response or not required:
                    return response if response else None
                else:
                    print(f"{self.colors['red']} Este campo es obligatorio{self.colors['end']}")
                    
            except (KeyboardInterrupt, EOFError):
                return None
    
    def prompt_for_choice(self, prompt: str, options: list, default: int = 0) -> Optional[str]:
        """
        Solicitar selección de opciones
        
        Args:
            prompt: Texto del prompt
            options: Lista de opciones
            default: Opción por defecto
            
        Returns:
            Opción seleccionada o None si se cancela
        """
        print(f"\n{self.colors['yellow']}{prompt}{self.colors['end']}")
        
        for i, option in enumerate(options, 1):
            default_marker = " (por defecto)" if i == default + 1 else ""
            print(f"  {i}. {option}{default_marker}")
        
        while True:
            try:
                choice = input(f"\n{self.colors['blue']}Selección (1-{len(options)}){self.colors['end']}: ").strip()
                
                if not choice:
                    return options[default]
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return options[choice_num - 1]
                else:
                    print(f"{self.colors['red']} Selecciona un número entre 1 y {len(options)}{self.colors['end']}")
                    
            except ValueError:
                print(f"{self.colors['red']} Ingresa un número válido{self.colors['end']}")
            except (KeyboardInterrupt, EOFError):
                return None
    
    def show_table(self, headers: list, rows: list, title: str = None) -> None:
        """
        Mostrar datos en formato de tabla
        
        Args:
            headers: Encabezados de la tabla
            rows: Filas de datos
            title: Título opcional de la tabla
        """
        if title:
            print(f"\n{self.colors['bold']}{self.colors['cyan']}{title}{self.colors['end']}")
            print(f"{self.colors['cyan']}{'-' * len(title)}{self.colors['end']}")
        
        # Calcular anchos de columna
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Mostrar encabezados
        header_row = " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers))
        print(f"\n{self.colors['bold']}{header_row}{self.colors['end']}")
        print("-" * len(header_row))
        
        # Mostrar filas
        for row in rows:
            row_str = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            print(row_str)
        
        print()
    
    def show_loading(self, message: str = "Cargando") -> None:
        """Mostrar indicador de carga"""
        print(f"\n{self.colors['yellow']}⏳ {message}...{self.colors['end']}")
    
    def clear_screen(self) -> None:
        """Limpiar pantalla (funciona en la mayoría de terminales)"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')


# Testing de la vista
if __name__ == "__main__":
    view = ChatView()
    
    print(" Testing Chat View...")
    
    # Mostrar mensaje de bienvenida
    view.show_welcome_message()
    
    # Mostrar diferentes tipos de mensajes
    view.show_success("Sistema inicializado correctamente")
    view.show_error("Error de conexión simulado")
    view.show_warning("Función en desarrollo")
    view.show_info("Información de prueba")
    
    # Mostrar ayuda
    help_msg = view.get_help_message()
    print("\n" + help_msg[:200] + "...")
    
    # Mostrar tabla de ejemplo
    view.show_table(
        ["ID", "Nombre", "Tipo"], 
        [["001", "Paleta Verano", "Ropa"], ["002", "Look Noche", "Maquillaje"]], 
        "Paletas Guardadas"
    )
    
    print(" Chat View funcionando correctamente")