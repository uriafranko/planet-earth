FROM python:3.12.10-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the project into `/app`
WORKDIR /app

COPY pyproject.toml .
RUN uv pip install -r pyproject.toml --system


COPY . /app
RUN uv pip install -e . --system
# Copy entrypoint script first and make it executable
COPY --chmod=0755 entrypoint.sh /app/entrypoint.sh
# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching

# Double-check permissions (redundant but ensures it's executable)
RUN chmod 755 /app/entrypoint.sh

# Set default service type (can be overridden with -e SERVICE_TYPE=api)
ENV SERVICE_TYPE=api

# Expose the port the app runs on
EXPOSE 8000

# Set the entrypoint script
CMD ["sh", "/app/entrypoint.sh"]
