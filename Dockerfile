# Use multi-stage build for smaller final image
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Second stage
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create non-root user for security
RUN addgroup --system app && \
    adduser --system --group app

# Set working directory
WORKDIR /app

# Install dependencies from wheels
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY . /app/

# Create and set permissions for logs and cache directories
RUN mkdir -p /app/logs /app/cache /app/data && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Create volume mount points
VOLUME ["/app/logs", "/app/cache", "/app/data"]

# Expose port
EXPOSE 8000

# Start application with proper settings for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1