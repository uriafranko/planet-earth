# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .

# Create a non-root user and set ownership
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Install Python dependencies
# We manually extract dependencies from pyproject.toml to avoid build issues
RUN pip install tomli && \
    python -c "import tomli; f = open('pyproject.toml', 'rb'); d = tomli.load(f); print('\n'.join(d['project']['dependencies']))" > requirements.txt && \
    pip install -r requirements.txt && \
    # Install psycopg2-binary explicitly for PostgreSQL support
    pip install psycopg2-binary && \
    # Force install uvicorn and its dependencies
    pip install uvicorn[standard]

# Copy application code
COPY --chown=appuser:appuser . .

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Set default service type (can be overridden with -e SERVICE_TYPE=api)
ENV SERVICE_TYPE=api

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
