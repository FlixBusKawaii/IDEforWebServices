FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    docker.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ /app/backend/

COPY ../compilers /app/compilers

WORKDIR /app/backend

CMD ["python", "app.py"]
