FROM continuumio/miniconda3 AS build

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY environment.yml .
RUN conda env create -f environment.yml && conda clean -afy

# Copy application code
COPY . .

# Create non-root user for security
#RUN useradd --create-home --shell /bin/bash appuser && \
#    chown -R appuser:appuser /app
#USER appuser

# Expose only the main application port (NOT the Locust ports)
EXPOSE 8000

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH /opt/conda/envs/multi-user-load-tester/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
