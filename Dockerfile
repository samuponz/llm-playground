FROM python:3.12-slim

WORKDIR /app

# Install dependencies first: this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Print output immediately, and don't write __pycache__ folders into the mounted project
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # matplotlib needs a writable cache folder; the app runs as your user, without a home
    MPLCONFIGDIR=/tmp/matplotlib

# The code itself is not copied: docker-compose.yml mounts the project folder at /app

# Default command: `docker compose run --rm app` starts the chat
CMD ["python", "chat.py"]
