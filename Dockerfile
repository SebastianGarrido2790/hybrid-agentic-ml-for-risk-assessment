FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy uv (faster pip alternative) configuration
# We will use simple pip here for simplicity within the container, 
# relying on the requirements.txt generated from pyproject.toml or uv
# Or better, just copy the pyproject.toml and use uv if available, or pip install .

# Copy project files
COPY . /app

# Install dependencies
# Using pip to install the package in editable mode or just dependencies
RUN pip install --no-cache-dir .

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
