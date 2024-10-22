FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    docker.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copie du code
COPY backend/ /app/backend/

WORKDIR /app/backend

CMD ["python", "app.py"]