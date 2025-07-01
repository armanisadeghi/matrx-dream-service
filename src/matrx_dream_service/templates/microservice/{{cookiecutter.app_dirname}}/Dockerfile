FROM python:3.13-slim


# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV_NAME={{cookiecutter.app_name}}
ENV PROJECT_DIR=/app
ENV LOG_DIR=/var/log/{{cookiecutter.app_name}}
ENV VIRTUAL_ENV=/app/.venv

# Set working directory
WORKDIR /app

# Install system dependencies required for the project
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    libasound2-dev \
    libpulse-dev \
    libmagic1 \
    libpq-dev \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install --no-cache-dir uv

# Copy project files
COPY . /app/

# Install dependencies using UV
RUN uv sync --frozen

# Create necessary directories
RUN mkdir -p /var/log/{{cookiecutter.app_name}} /app/temp/app_outputs /app/reports


COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
