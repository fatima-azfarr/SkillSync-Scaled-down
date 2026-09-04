# SkillSync API Service Dockerfile
# Builds a lightweight container for the FastAPI application

# Use Python 3.11 slim image (smaller than full image)
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (Docker caches this layer if requirements don't change)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API source code
COPY api/ ./api/

# Create a non-root user for security
# Running as root inside a container is a security risk
RUN useradd --create-home appuser
USER appuser

# Expose port 8000 (FastAPI's default port)
EXPOSE 8000

# Health check — Docker will ping this endpoint periodically
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start the API server using uvicorn
# --host 0.0.0.0 makes it accessible from outside the container
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
