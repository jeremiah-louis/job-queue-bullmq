# # Use Ubuntu 24.04 as base image
# FROM ubuntu:24.04

# # Prevent interactive prompts during package installation
# ENV DEBIAN_FRONTEND=noninteractive

# # Install system dependencies
# RUN apt-get update && \
#     apt-get install -y \
#     python3-full \
#     python3-pip \
#     ffmpeg \
#     curl \
#     && rm -rf /var/lib/apt/lists/*
    
# WORKDIR /app
# # Create and activate virtual environment
# RUN python3 -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"

# # Upgrade pip
# RUN python3 -m pip install --upgrade pip

# # Install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir --timeout=1000 -r requirements.txt

# # Copy application files
# COPY . /app

# # Create storage directory
# RUN mkdir -p /app/.storage

# # Set environment variables
# ENV PYTHONUNBUFFERED=1
# ENV STORAGE_DIR=/app/.storage
# # Expose port
# EXPOSE 8000

# # Add health check
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8000/health || exit 1

# # Verify installations
# RUN echo "Verifying installations:" && \
#     echo "Ubuntu version:" && cat /etc/os-release && \
#     echo "FFmpeg version:" && ffmpeg -version && \
#     echo "Python version:" && python3 --version && \
#     echo "Pip version:" && pip --version && \
#     echo "Installed packages:" && pip list

# # Command to run when container starts
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]



# --- Stage 1: Builder ---
# Use a Python base image that includes build tools
FROM python:3.11 AS builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages OR runtime (like ffmpeg)
# If requirements.txt needs compilation against system libs (e.g., postgresql client), add them here.
# We install ffmpeg here AND in the final stage, as it's needed for runtime.
# curl is needed for the final stage healthcheck.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment (optional but good practice within the builder)
# Note: We will copy the installed packages, not necessarily the venv structure itself
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip within the venv
RUN pip install --upgrade pip

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies into the virtual environment
# --no-cache-dir is still good practice here
RUN pip install --no-cache-dir --timeout=1000 -r requirements.txt

# Copy the rest of the application code
COPY . .

# --- Stage 2: Final ---
# Use a slim Python base image for the runtime
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Install ONLY runtime system dependencies
# We need ffmpeg (used by the app) and curl (used by healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    # Add any other *runtime* system libraries your app absolutely needs
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment (installed packages) from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code from the builder stage
COPY --from=builder /app /app

# Create storage directory
RUN mkdir -p /app/.storage

# Set environment variables
# Make sure Python finds packages in the virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV STORAGE_DIR=/app/.storage

# Expose port
EXPOSE 8000

# Add health check (requires curl installed above)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run when container starts
# Uses python/uvicorn from the virtual environment copied above
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]