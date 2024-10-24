FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install numpy pandas matplotlib requests
