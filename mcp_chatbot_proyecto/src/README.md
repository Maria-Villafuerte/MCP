# Beauty Palette MCP Server Local

Servidor MCP local especializado en paletas de colores y sistema de belleza personalizado.

##  Características

- **Perfiles Personalizados**: Crea perfiles basados en tono de piel, color de ojos, cabello y estilo
- **Paletas Inteligentes**: Genera paletas para ropa, maquillaje y accesorios
- **Análisis de Armonía**: Analiza la compatibilidad entre colores
- **Citas Inspiracionales**: Base de datos de citas de belleza y estilo
- **Protocolo MCP**: Compatible con clientes MCP estándar

##  Requisitos

- Python 3.8 o superior
- Biblioteca `mcp` instalada

##  Instalación

1. **Ejecutar el instalador:**
   ```bash
   python setup_beauty_server.py
   ```

2. **O instalar manualmente:**
   ```bash
   pip install mcp>=1.0.0
   ```

##  Uso

### Iniciar el Servidor

```bash
# Opción 1: Script de inicio
python start_beauty_server.py

# Opción 2: Directamente
python beauty_mcp_server_local.py
```

### Probar el Servidor

```bash
# Ejecutar cliente de prueba
python test_beauty_client.py
```

## 🛠️ Herramientas MCP Disponibles

### `create_beauty_profile`
Crear un perfil de belleza personalizado.

**Parámetros:**
- `user_id` (string): ID único del usuario
- `name` (string): Nombre completo
- `skin_tone` (enum): clara, media, oscura
- `undertone` (enum): frio, calido, neutro
- `eye_color` (enum): azul, verde, cafe, gris, negro
- `hair_color` (enum): rubio, castano, negro, rojo, gris
- `hair_type` (enum): liso, ondulado, rizado
- `style_preference` (enum): moderno, clasico, bohemio, minimalista, romantico, edgy

### `generate_color_palette`
Generar paleta de colores personalizada.

**Parámetros:**
- `user_id` (string): ID del usuario
- `palette_type` (enum): ropa, maquillaje, accesorios
- `event_type` (enum): casual, trabajo, formal, fiesta, cita
- `season` (enum): primavera, verano, otono, invierno

### `get_beauty_profile`
Obtener perfil de belleza existente.

### `list_beauty_profiles`
Listar todos los perfiles disponibles.

### `get_user_palette_history`
Ver historial de paletas de un usuario.

### `get_inspirational_quote`
Obtener cita inspiracional de belleza.

### `analyze_color_harmony`
Analizar armonía entre colores.

## 📝 Ejemplos

### Crear Perfil
```python
await call_tool("create_beauty_profile", {
    "user_id": "maria_123",
    "name": "María García",
    "skin_tone": "media",
    "undertone": "calido",
    "eye_color": "cafe",
    "hair_color": "castano",
    "style_preference": "moderno"
})
```

### Generar Paleta
```python
await call_tool("generate_color_palette", {
    "user_id": "maria_123",
    "palette_type": "ropa",
    "event_type": "trabajo"
})
```

## 🔧 Integración con Otros Sistemas

Este servidor MCP puede integrarse con:
- Clientes MCP estándar
- Sistemas de chat con Claude
- Aplicaciones de moda y belleza
- Sistemas de recomendación personalizados

##  Almacenamiento

- **Perfiles**: Almacenados en memoria durante la sesión
- **Paletas**: Historial en memoria por usuario
- **Persistencia**: Para uso productivo, considera implementar almacenamiento en archivo

## 🛡️ Limitaciones

- Almacenamiento en memoria (se pierde al reiniciar)
- Un servidor por instancia
- Análisis de color básico

## 🤝 Contribuciones

Para mejoras o nuevas características:
1. Agrega nuevos colores a la base de datos
2. Mejora los algoritmos de armonía
3. Implementa persistencia en archivo
4. Añade más tipos de eventos

## 📄 Licencia

MIT License - Uso libre para proyectos personales y comerciales.
