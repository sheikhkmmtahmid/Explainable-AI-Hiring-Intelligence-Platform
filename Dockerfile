FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.huggingface

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node for React build
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements/base.txt requirements/base.txt
COPY requirements/production.txt requirements/production.txt
RUN pip install --no-cache-dir -r requirements/production.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy source
COPY . .

# Build React frontend
RUN cd frontend && npm ci && npm run build

# Collect static files with a dummy secret key (real one injected at runtime)
RUN DJANGO_SECRET_KEY=build-placeholder python manage.py collectstatic --noinput

RUN chmod +x start.sh

EXPOSE 7860

CMD ["./start.sh"]
