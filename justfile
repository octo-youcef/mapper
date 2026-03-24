# ==============================================================================
# Setup & Help
# ==============================================================================

# List all available commands
default:
    @just --list

# Install dependencies
install:
    uv sync
    uv run pre-commit install

# ==============================================================================
# Docker
# ==============================================================================

# Build Docker containers
build:
    docker-compose build

# Start Docker containers
up:
    docker-compose up -d
    @echo ""
    @echo "✅ Containers started!"
    @echo ""
    @echo "🌐 Service URLs:"
    @echo "   Neo4j Browser: http://localhost:7474 (neo4j/devpassword)"
    @echo "   Backend API:   http://localhost:8080/api/"
    @echo "   Web UI:        http://localhost:3000"
    @echo ""
    @echo "📋 Useful commands:"
    @echo "   just logs        - View container logs"
    @echo "   just mapper      - Run CLI tool"
    @echo "   just down        - Stop containers"
    @echo ""

# Stop Docker containers
down:
    docker-compose down

# View logs from Docker containers
logs service="":
    @if [ -z "{{service}}" ]; then \
        docker-compose logs -f; \
    else \
        docker-compose logs -f {{service}}; \
    fi

# Rebuild and restart containers
restart: down build up

# Full reset: stop containers, remove volumes, rebuild, and start
reset:
    docker-compose down -v
    docker-compose build
    docker-compose up -d
    @echo ""
    @echo "✅ Environment reset complete!"
    @echo ""
    @echo "🌐 Service URLs:"
    @echo "   Neo4j Browser: http://localhost:7474 (neo4j/devpassword)"
    @echo "   Backend API:   http://localhost:8080/api/"
    @echo "   Web UI:        http://localhost:3000"
    @echo ""

# ==============================================================================
# Development
# ==============================================================================

# Run CLI tool
mapper *args:
    uv run mapper {{args}}

# Format code (ruff + isort)
format:
    uv run ruff format .
    uv run isort .

# Fix all auto-fixable issues
fix:
    uv run ruff format .
    uv run isort .
    uv run ruff check --fix .

# ==============================================================================
# Linting
# ==============================================================================

# Check code formatting (ruff format)
lint-format:
    uv run ruff format --check .

# Check import sorting (isort)
lint-imports:
    uv run isort --check-only .

# Check code quality (ruff)
lint-ruff:
    uv run ruff check .

# Check type hints (mypy)
lint-types:
    uv run mypy .

# Run all linting checks
lint: lint-format lint-imports lint-ruff lint-types

# Run all code quality checks (alias for lint)
quality: lint

# ==============================================================================
# Testing
# ==============================================================================

# Run all tests (unit + integration)
test *args:
    uv run pytest {{args}}

# Run unit tests only
test-unit *args:
    uv run pytest tests/unit {{args}}

# Run integration tests only
test-integration *args:
    uv run pytest tests/integration {{args}}

# Run unit tests with coverage (fails if coverage < 75%)
test-coverage:
    uv run pytest tests/unit --cov=src/mapper --cov-report=html --cov-report=term --cov-report=json --cov-fail-under=75

# ==============================================================================
# Maintenance
# ==============================================================================

# Clean up generated files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.coverage" -delete
    rm -rf htmlcov/ .coverage .pytest_cache/ .mypy_cache/ .ruff_cache/

# ==============================================================================
# Versioning
# ==============================================================================

# Show current version
version-show:
    @uv run bump-my-version show current_version

# Bump patch version (0.1.0 -> 0.1.1)
version-patch:
    uv run bump-my-version bump patch

# Bump minor version (0.1.0 -> 0.2.0)
version-minor:
    uv run bump-my-version bump minor

# Bump major version (0.1.0 -> 1.0.0)
version-major:
    uv run bump-my-version bump major

# Bump version (interactive)
version part="":
    @if [ -z "{{part}}" ]; then \
        echo "Usage: just version [patch|minor|major]"; \
        echo ""; \
        echo "Current version: $(uv run bump-my-version show current_version)"; \
        echo ""; \
        echo "Examples:"; \
        echo "  just version patch   - Bump patch version (0.1.0 -> 0.1.1)"; \
        echo "  just version minor   - Bump minor version (0.1.0 -> 0.2.0)"; \
        echo "  just version major   - Bump major version (0.1.0 -> 1.0.0)"; \
        echo ""; \
        echo "Or use:"; \
        echo "  just version-show    - Show current version"; \
        echo "  just version-patch   - Bump patch version"; \
        echo "  just version-minor   - Bump minor version"; \
        echo "  just version-major   - Bump major version"; \
    else \
        uv run bump-my-version bump {{part}}; \
    fi
