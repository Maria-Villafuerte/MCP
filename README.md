# MCP Chatbot - Model Context Protocol Implementation

A comprehensive chatbot implementation that integrates Claude API with various MCP (Model Context Protocol) servers, providing filesystem operations, Git version control, and custom beauty color palette generation capabilities.

## Features

### Core Functionality
- **Claude API Integration**: Direct communication with Anthropic's Claude API
- **Context Management**: Maintains conversation history throughout sessions
- **MCP Logging System**: Comprehensive logging of all MCP server interactions
- **Interactive Console Interface**: User-friendly command-line interface

### MCP Server Capabilities

#### Filesystem Operations
- **File Reading**: Read content from files in the workspace
- **File Writing**: Create and modify files with custom content
- **Directory Listing**: Browse directory structures

#### Git Version Control
- **Repository Initialization**: Create new Git repositories
- **File Staging**: Add files to Git staging area
- **Commit Operations**: Create commits with custom messages

#### Beauty Color Palette Generator
- **Personalized Color Recommendations**: Generate custom color palettes based on:
  - Skin tone (clara, media, oscura)
  - Eye color (azul, verde, cafe, gris)
  - Hair color (rubio, castano, negro, rojo)
  - Lip tone
  - Event type (casual, formal, fiesta, trabajo)
  - Season (primavera, verano, otoño, invierno)
  - Style preferences
- **Clothing Recommendations**: Specific suggestions for pants and blouses with hex color codes

## Installation

### Prerequisites
- Python 3.8 or higher
- Git (for Git MCP functionality)
- Anthropic API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd mcp-chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install anthropic python-dotenv
   ```

3. **Configure environment variables**
   ```bash
   # The script will create a .env file automatically on first run
   # Edit the .env file and add your Anthropic API key:
   ANTHROPIC_API_KEY=your_api_key_here
   ```

4. **Get your Anthropic API key**
   - Visit [Anthropic Console](https://console.anthropic.com/)
   - Create an account (get $5 free credits)
   - Generate an API key
   - Add it to your `.env` file

## 💻 Usage

### Starting the Chatbot
```bash
python main.py
```

### Available Commands

#### System Commands
- `/help` - Display all available commands
- `/log` - Show MCP interaction history
- `/clear` - Clear conversation context
- `/quit` - Exit the chatbot

#### Filesystem Operations
- `/read [filename]` - Read file content
- `/write [filename] [content]` - Write content to file
- `/ls [directory]` - List directory contents (default: current directory)

#### Git Operations
- `/git_init [repo_name]` - Initialize a new Git repository
- `/git_add [repo_name] [filename]` - Add file to staging area
- `/git_commit [repo_name] [message]` - Create a commit with message

#### Color Palette Generation
```bash
/palette [skin_tone] [eye_color] [hair_color] [lip_tone] [event] [season] [style]
```

**Example:**
```bash
/palette clara azul rubio rosa casual verano elegante
```

**Available Options:**
- **Skin tones**: clara, media, oscura
- **Eye colors**: azul, verde, cafe, gris
- **Hair colors**: rubio, castano, negro, rojo
- **Events**: casual, formal, fiesta, trabajo
- **Seasons**: primavera, verano, otoño, invierno

## Project Structure

```
mcp-chatbot/
├── main.py              # Main chatbot implementation
├── .env                 # Environment variables (auto-generated)
├── mcp_workspace/       # Working directory for file operations
├── README.md           # This file
└── requirements.txt    # Python dependencies (if needed)
```

## Usage Examples

### Complete Workflow Example
```bash
# Start the chatbot
python main.py

# Create a new project
/git_init my_beauty_app

# Create a README file
/write my_beauty_app/README.md "# Beauty Color Palette App"

# Add file to Git
/git_add my_beauty_app README.md

# Commit changes
/git_commit my_beauty_app "Initial commit: Add README"

# Generate a color palette
/palette clara azul rubio rosa fiesta verano elegante

# Check the interaction log
/log
```

### Natural Language Interaction
You can also interact with the chatbot using natural language:
```
"Can you help me choose colors for a formal event?"
"What files do I have in my project?"
"Tell me about version control best practices"
```

## Architecture

The chatbot implements the MCP (Model Context Protocol) architecture with three main components:

- **Host (Anfitrión)**: The main chatbot application that coordinates multiple MCP clients
- **Client**: Components that maintain connections with MCP servers
- **Server**: Tools that execute specific actions (filesystem, git, color palette generation)

## Technical Details

### MCP Protocol Implementation
- Uses JSON-RPC for communication
- Implements local MCP servers
- Maintains comprehensive interaction logging
- Provides error handling and user feedback

### API Integration
- Anthropic Claude API integration
- Context-aware conversations
- Error handling and connection management

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Error: ANTHROPIC_API_KEY no encontrada en variables de entorno
   ```
   **Solution**: Ensure your `.env` file contains a valid Anthropic API key

2. **Git Command Failures**
   ```
   Error con git init: [git] command not found
   ```
   **Solution**: Install Git on your system

3. **File Permission Errors**
   **Solution**: Ensure the script has write permissions in the working directory



### Implemented Features 
- [x] Claude API connection and context management
- [x] MCP interaction logging system
- [x] Filesystem MCP server (local)
- [x] Git MCP server (local)
- [x] Custom Color Palette MCP server (local)
- [x] Interactive console interface
- [x] Comprehensive error handling

### Upcoming Features 
- [ ] Integration with external MCP servers
- [ ] Remote MCP server implementation
- [ ] Network communication analysis
- [ ] Enhanced UI/UX improvements

