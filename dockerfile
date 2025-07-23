# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd --create-home --shell /bin/bash app

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/data/sessions /app/data/vector_db \
    && chown -R app:app /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set proper permissions
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Set environment variables
ENV FLASK_ENV=development
ENV PYTHONPATH=/app
ENV USE_SIMPLE_CONFIG=true

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/auth/status || exit 1

# Run the application
CMD ["python", "minimal_run.py"]