# Milvus Setup Instructions

This document provides instructions for setting up and running Milvus for the RAG application.

## Prerequisites

- Docker and Docker Compose installed on your system
- At least 8GB of RAM available for Docker

## Starting Milvus

1. Make sure Docker is running on your system.

2. Start Milvus using Docker Compose:

```bash
docker-compose up -d
```

This will start Milvus in standalone mode with all necessary services (etcd, MinIO, and Milvus).

3. Verify that Milvus is running:

```bash
docker ps
```

You should see three containers running:

- milvus-standalone
- milvus-etcd
- milvus-minio

4. Check the Milvus logs:

```bash
docker logs milvus-standalone
```

5. Once Milvus is running, you can start the RAG application:

```bash
cd api
python -m uvicorn main:app --reload
```

## Stopping Milvus

To stop Milvus:

```bash
docker-compose down
```

## Troubleshooting

If you encounter issues with Milvus:

1. Check the Milvus logs:

```bash
docker logs milvus-standalone
```

2. Restart Milvus:

```bash
docker-compose down
docker-compose up -d
```

3. Check the API logs for connection issues:

```bash
cat api/logs/app.log
```

4. Use the `/milvus-status` endpoint to check if the API can connect to Milvus:

```bash
curl http://localhost:8000/milvus-status
```

## Data Persistence

Milvus data is stored in the `milvus-data` directory. This ensures that your vector data persists even if the containers are stopped or removed.

## Milvus Configuration

The default configuration uses:

- Host: localhost
- Port: 19530

These settings can be changed in the `.env` file if needed.
