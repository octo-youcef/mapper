# Mapper (Application Mapper)

![Version](https://img.shields.io/badge/version-0.4.7-blue.svg)
![Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/octo-youcef/3424657d04826a3196811985d2f13687/raw/mapper-tests.json&cacheSeconds=300)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/octo-youcef/3424657d04826a3196811985d2f13687/raw/mapper-coverage.json&cacheSeconds=300)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)

AST-based Python code analyser that maps application structure and relationships into a Neo4j graph database, with CLI and web UI for exploration.

## Overview

Mapper helps you understand complex Python applications by analysing their Abstract Syntax Trees (AST) and creating an interactive graph representation of classes, functions, methods, imports, and their relationships.

### Key Features

- **Comprehensive AST Analysis**: Maps classes, functions, methods, imports, decorators, and more
- **Neo4j Graph Storage**: Store and query code relationships in a graph database
- **Incremental Updates**: Track versions and update only what changed
- **CLI Tool**: Powerful command-line interface built with Typer
- **Web UI**: Interactive visualization and exploration (FastAPI + React)
- **Package-Wide Analysis**: Analyse entire Python packages from a directory

### Use Cases

- **Process Optimization**: Understand complex codebases for refactoring
- **Application Mapping**: Visualize dependencies and relationships
- **Code Navigation**: Explore large applications interactively
- **Impact Analysis**: Trace changes through the codebase

### Architecture

- **CLI**: Typer + Rich for beautiful terminal output
- **Backend**: FastAPI for web UI API
- **Database**: Neo4j for graph storage
- **Parser**: Python `ast` module for code analysis
- **Package Manager**: uv
- **Task Runner**: just
- **Testing**: pytest + pytest-asyncio + pytest-mock
- **Code Quality**: ruff, isort, mypy

## Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- [uv](https://docs.astral.sh/uv/) package manager
- [just](https://github.com/casey/just) task runner

### Installation

```bash
# Clone the repository
git clone git@github.com:octo-youcef/mapper.git
cd mapper

# Install dependencies
just install

# Start the development environment (Neo4j + API + Web UI)
just up
```

The services will be available at:
- **Neo4j Browser**: http://localhost:7474 (username: neo4j, password: devpassword)
- **Backend API**: http://localhost:8080/api/
- **Web UI**: http://localhost:3000

### Basic Usage

```bash
# Initialize configuration
mapper init

# Start analyzing a Python package
mapper analyse start /path/to/package

# View analysis results in Neo4j Browser
# Navigate to http://localhost:7474

# Start the web UI for interactive exploration
# Navigate to http://localhost:3000
```

## Development

### Common Commands

```bash
# Development
just install          # Install dependencies
just build           # Build Docker containers
just up              # Start containers (Neo4j + API + Web UI)
just down            # Stop containers
just reset           # Full reset (stops, removes volumes, rebuilds)

# Testing & Quality
just test            # Run all tests
just test-coverage   # Run tests with coverage report
just format          # Format code (ruff + isort)
just lint            # Run all quality checks
just fix             # Auto-fix linting issues

# CLI Development
just mapper [args]     # Run CLI tool locally

# Versioning
just version-show    # Show current version
just version patch   # Bump patch version (0.1.0 → 0.1.1)
just version minor   # Bump minor version (0.1.0 → 0.2.0)
just version major   # Bump major version (0.1.0 → 1.0.0)
```

### Running Tests

```bash
# Run all tests
just test

# Run with coverage
just test-coverage

# Run specific test file
uv run pytest tests/test_parser.py

# Run specific test
uv run pytest tests/test_parser.py::test_parse_function
```

### Code Quality

```bash
# Check code quality
just lint

# Format code
just format

# Fix auto-fixable issues
just fix
```

## Project Structure

```
mapper/
├── src/
│   └── mapper/             # Main package
│       ├── cli/            # CLI commands
│       ├── parser.py       # AST parsing
│       ├── graph.py        # Neo4j operations
│       ├── analyser/       # Analysis packages
│       ├── api.py          # FastAPI backend
│       └── config_manager/ # Configuration management
├── tests/                  # Test suite
├── docs/                   # Documentation
│   ├── technical/          # Technical documentation
│   └── user-journeys/      # User journey documentation
├── .github/
│   └── workflows/          # CI/CD workflows
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker image definition
├── justfile                # Task runner commands
├── pyproject.toml          # Project dependencies and config
├── CHANGELOG.md            # Version history
├── CLAUDE.md               # AI agent instructions
└── README.md               # This file
```

## CLI Commands

```bash
# Setup
mapper init              # Initialize configuration
mapper status            # Check system health
mapper version           # Show version

# Analysis
mapper analyse start /path/to/package          # Analyze a package
mapper analyse list                            # List analyzed packages
mapper analyse get <package-name>              # Show package details
mapper analyse export <package-name>           # Export graph data
mapper analyse delete <package-name>           # Delete package from database

# Configuration
mapper config get [key]                        # Get config value(s)
mapper config set <key> <value>                # Set config value
mapper config edit                             # Edit config in $EDITOR

# Queries
mapper query list                              # List available queries
mapper query run <query-name> <package>        # Run a query
mapper query create                            # Create custom query
```

## API Documentation

API documentation will be available at http://localhost:8080/docs once the backend is implemented.

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests and linting: `just test && just lint`
4. Commit your changes
5. Push and create a pull request

### Commit Guidelines

- Keep commits atomic and focused
- Write clear commit messages
- Prefer rebasing over fix commits

## Versioning

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

Use `just version [patch|minor|major]` to bump the version. Tags are created automatically by GitHub Actions on release.

## Documentation

- **Technical Documentation**: See [docs/technical/](docs/technical/)
- **User Journeys**: See [docs/user-journeys/](docs/user-journeys/)

## License

[Add license information here]

## Support

For issues and questions, please open a GitHub issue.
