FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Copy source directory (needed for editable install)
COPY src/ src/

# Install Python dependencies
RUN uv sync --frozen || uv sync

# Copy rest of project
COPY . .

# Expose port
EXPOSE 8080

# Run the application
CMD ["uv", "run", "uvicorn", "m_app.api:app", "--host", "0.0.0.0", "--port", "8080"]
