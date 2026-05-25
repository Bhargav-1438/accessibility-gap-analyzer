FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for Rtree/geopandas
RUN apt-get update && apt-get install -y \
    libspatialindex-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install standard requirements plus FastAPI dependencies
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn pydantic

COPY . .

# Precompute OSM graphs for zero cold-start latency
# This embeds the core city graphs into the Docker image itself.
RUN python precompute.py

EXPOSE 8000 8501
