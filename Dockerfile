FROM python:3.11-slim

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

WORKDIR /app

# Системные зависимости для psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only backend files (not frontend)
COPY apps/ ./apps/
COPY config/ ./config/
COPY tests/ ./tests/
COPY manage.py .
COPY .env.example .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Use gunicorn for production, fallback to runserver for development
CMD ["sh", "-c", "if [ \"$DEBUG\" = \"False\" ]; then gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3; else python manage.py runserver 0.0.0.0:8000; fi"]
