# Multi-stage build for arroyopy
#
# Build examples:
#   Basic:         podman build -t arroyopy .
#   With ZMQ:      podman build --build-arg EXTRAS=zmq -t arroyopy:zmq .
#   With Redis:    podman build --build-arg EXTRAS=redis -t arroyopy:redis .
#   Full stack:    podman build --build-arg EXTRAS="zmq,redis,file-watch" -t arroyopy:full .
#
# Run examples:
#   podman run arroyopy --help
#   podman run -v ./config:/config arroyopy run /config/pipeline.yaml
#
# Build arguments for optional dependencies
ARG EXTRAS=""

FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy only what's needed for building
COPY pyproject.toml README.md LICENSE* ./
COPY src/ ./src/

# Build the wheel
RUN python -m build --wheel

# Final runtime image
FROM python:3.12-slim

ARG EXTRAS

WORKDIR /app

# Install runtime dependencies and the built wheel
COPY --from=builder /app/dist/*.whl /tmp/

# Install with optional extras if specified
RUN if [ -z "$EXTRAS" ]; then \
        pip install --no-cache-dir /tmp/*.whl; \
    else \
        pip install --no-cache-dir "/tmp/*.whl[$EXTRAS]"; \
    fi && \
    rm /tmp/*.whl

# Create a non-root user
RUN useradd -m -u 1000 arroyo && \
    chown -R arroyo:arroyo /app

USER arroyo

# Default command runs the CLI
ENTRYPOINT ["arroyo-run"]
CMD ["--help"]

# Labels
LABEL org.opencontainers.image.title="arroyopy"
LABEL org.opencontainers.image.description="A library to simplify processing streams of data"
LABEL org.opencontainers.image.source="https://github.com/als-computing/arroyopy"
LABEL org.opencontainers.image.licenses="BSD-3-Clause"
