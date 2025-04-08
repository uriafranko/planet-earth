# Use an official Python runtime as a parent image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV POETRY_NO_INTERACTION=1
ENV PATH="/root/.local/bin:${PATH}"

# Install uv and required system dependencies
RUN apt-get update && apt-get install -y curl gcc g++ libc6-dev && \
    curl -LsSf https://astral.sh/uv/install.sh | bash

# Set the working directory in the container
WORKDIR /app

# Copy project files
COPY pyproject.toml .

# Create a virtual environment and install dependencies
RUN uv venv --python 3.11 .venv && \
    . .venv/bin/activate && \
    uv pip install --no-deps "hatchling" && \
    uv pip install -r pyproject.toml

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

WORKDIR /app

# Copy the rest of the application code
COPY --chown=appuser:appuser . .

# Final stage
FROM python:3.11-slim as final

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

# Copy the installed venv and application code from the builder stage
COPY --from=builder /app /app

# Create the appuser in the final stage
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Copy and make the entrypoint script executable
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Set default service type (can be overridden with -e SERVICE_TYPE=worker)
ENV SERVICE_TYPE=api

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
