FROM python:3.12-slim

WORKDIR /app

# Install dependencies first: this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Print output immediately, and don't write __pycache__ folders into the mounted project
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# The code itself is not copied: docker-compose.yml mounts the project folder at /app
