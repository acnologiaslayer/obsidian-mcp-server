# Obsidian MCP Server

[![Tests](https://github.com/mahir009/obsidian-mcp-server/actions/workflows/test.yml/badge.svg)](https://github.com/mahir009/obsidian-mcp-server/actions/workflows/test.yml)
[![Docker Build](https://github.com/mahir009/obsidian-mcp-server/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/mahir009/obsidian-mcp-server/actions/workflows/docker-publish.yml)
[![Docker Hub](https://img.shields.io/docker/pulls/mahir009/obsidian-mcp-server)](https://hub.docker.com/r/mahir009/obsidian-mcp-server)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for seamless integration between Claude and your Obsidian vault. This server enables Claude to read, write, search, and analyze your Obsidian notes directly.

## Features

### Core Operations

- **read_note(filepath)** - Read any note's full content including frontmatter
- **create_note(filepath, content, frontmatter)** - Create new notes with optional YAML frontmatter
- **edit_note(filepath, content)** - Edit existing notes while preserving frontmatter
- **list_notes(directory)** - List all markdown notes in a directory with metadata
- **search_vault(query)** - Full-text search across all notes with contextual excerpts
- **get_vault_structure()** - Get the complete directory tree of your vault

### Metadata & Analysis

- **read_frontmatter(filepath)** - Parse YAML frontmatter from any note
- **update_frontmatter(filepath, frontmatter)** - Update note metadata
- **get_backlinks(note_name)** - Find all notes linking to a specific note
- **list_tags()** - Discover all unique tags across your vault
- **find_by_tag(tag)** - Find notes containing specific hashtags

## Quick Start

### Prerequisites

- Python 3.11 or higher (for local installation)
- Docker (for containerized deployment)
- An Obsidian vault directory

### Installation Options

#### Option 1: Docker (Recommended)

```bash
# Pull from Docker Hub
docker pull mahir009/obsidian-mcp-server:latest

# Or build locally
docker build -t obsidian-mcp-server .
```

#### Option 2: Python Package (via uv)

```bash
# Clone the repository
git clone https://github.com/mahir009/obsidian-mcp-server.git
cd obsidian-mcp-server

# Install with uv
uv venv
uv pip install -e .
```

## Configuration

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration file:

**macOS:**
```bash
~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

**Configuration:**
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "VAULT_PATH=/vault",
        "-e", "TRANSPORT=stdio",
        "-v", "/path/to/your/vault:/vault:ro",
        "mahir009/obsidian-mcp-server:latest"
      ],
      "env": {
        "VAULT_PATH": "/vault"
      }
    }
  }
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VAULT_PATH` | `/vault` | Path to your Obsidian vault |
| `TRANSPORT` | `stdio` | Transport mode: `stdio` (Claude Desktop) or `sse` (remote) |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `HOST` | `0.0.0.0` | Host for SSE mode |
| `PORT` | `3000` | Port for SSE mode |

### Using Docker Compose

Create a `docker-compose.yml`:

```yaml
version: "3.8"

services:
  obsidian-mcp-server:
    image: mahir009/obsidian-mcp-server:latest
    environment:
      - VAULT_PATH=/vault
      - TRANSPORT=stdio
      - LOG_LEVEL=INFO
    volumes:
      - /path/to/your/vault:/vault:ro
    stdin_open: true
    tty: true
```

Run with:
```bash
export VAULT_PATH=/path/to/your/vault
docker-compose up
```

## Usage Examples

Once configured, you can ask Claude to interact with your vault:

### Reading Notes

```
"Please read my Daily/2024-01-15.md note and summarize it."
```

### Creating Notes

```
"Create a new note in Projects/ called 'Website Redesign' with content about the new layout."
```

### Searching

```
"Search my vault for any mentions of 'machine learning' and summarize what I have."
```

### Analyzing Structure

```
"Show me the structure of my vault and suggest how I could better organize it."
```

### Working with Tags

```
"Find all notes tagged with #project and list their status from frontmatter."
```

### Finding Connections

```
"What notes link to my 'Project Ideas' note? Show me how they're related."
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/mahir009/obsidian-mcp-server.git
cd obsidian-mcp-server

# Create virtual environment with uv
uv venv

# Install in development mode
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_vault_manager.py
```

### Code Quality

```bash
# Run linter
ruff check src tests

# Run formatter
ruff format src tests

# Run type checker
mypy src
```

### Project Structure

```
obsidian-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py              # Main MCP server with tools
│   ├── vault_manager.py       # Vault operations logic
│   └── frontmatter_parser.py  # YAML frontmatter handling
├── tests/
│   ├── __init__.py
│   ├── test_server.py
│   ├── test_vault_manager.py
│   └── test_frontmatter_parser.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── .github/
    └── workflows/
        ├── test.yml
        └── docker-publish.yml
```

## Docker Hub Publishing

### Setting Up Automated Builds

1. Create a Docker Hub account at [hub.docker.com](https://hub.docker.com)
2. Create a new repository named `obsidian-mcp-server`
3. In your GitHub repository, add the following secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: A Docker Hub access token ([create one here](https://hub.docker.com/settings/security))

4. Update the GitHub Actions workflow files with your username:
   - Replace `mahir009` in `.github/workflows/docker-publish.yml`
   - Replace `mahir009` in `README.md`

5. Push to main branch or create a release to trigger the build:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

### Manual Docker Build

```bash
# Build for multiple platforms
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t mahir009/obsidian-mcp-server:latest \
  --push .
```

## Security Considerations

- The server runs as a non-root user inside the container
- Path traversal attacks are blocked - all paths must be within the vault
- Docker volumes are mounted read-only by default (`:ro`)
- No secrets or API keys are required for basic operation
- All file operations are logged for audit purposes

## Troubleshooting

### Server Won't Start

Check that `VAULT_PATH` is set correctly:
```bash
# Test vault path
ls -la $VAULT_PATH

# Run with debug logging
docker run -e VAULT_PATH=/vault -e LOG_LEVEL=DEBUG -v /your/vault:/vault obsidian-mcp-server
```

### Claude Can't Connect

- Verify the configuration JSON syntax is valid
- Ensure the vault path in `volumes` is absolute, not relative
- Check Claude Desktop logs for errors

### Permission Errors

The container runs as user `mcp` (UID 1000). Ensure your vault files are readable:
```bash
chmod -R 755 /path/to/your/vault
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and linting (`pytest && ruff check src tests`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) - the fastest way to build MCP servers in Python
- Uses the [Model Context Protocol](https://modelcontextprotocol.io) specification
- Inspired by the Obsidian community and the power of local-first knowledge management

## Support

- [GitHub Issues](https://github.com/mahir009/obsidian-mcp-server/issues) - Report bugs or request features
- [Discussions](https://github.com/mahir009/obsidian-mcp-server/discussions) - Ask questions and share ideas
- [Docker Hub](https://hub.docker.com/r/mahir009/obsidian-mcp-server) - Container images

---

**Note:** Remember to replace `mahir009` with your actual GitHub and Docker Hub username throughout the codebase before publishing.
