# Docker Deployment Guide

This guide explains how to deploy the Weather Activity Advisor application using Docker Compose.

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)
- API Keys:
  - GROQ_API_KEY
  - WEATHER_API_KEY
  - DEEPGRAM_API_KEY

## Quick Start

1. **Create environment file**

   Copy the example environment file and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```env
   GROQ_API_KEY=your_actual_groq_api_key
   WEATHER_API_KEY=your_actual_weather_api_key
   DEEPGRAM_API_KEY=your_actual_deepgram_api_key
   ```

2. **Build and start services**

   ```bash
   docker-compose up -d
   ```

   This will:
   - Build the backend and frontend Docker images
   - Start both services in detached mode
   - Set up networking between services

3. **Access the application**

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Docker Compose Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Rebuild after code changes
```bash
# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend
```

### Check service status
```bash
docker-compose ps
```

### Execute commands in containers
```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh
```

## Architecture

The Docker setup consists of:

1. **Backend Service** (`backend`)
   - FastAPI application
   - Runs on port 8000
   - Uses Python 3.11 slim image
   - Environment variables loaded from `.env`

2. **Frontend Service** (`frontend`)
   - React application built with Vite
   - Served with `serve` (Node.js static file server)
   - Runs on port 3000
   - Single-stage build

3. **Network**
   - Both services are on the same Docker network
   - Services can communicate using service names

## Environment Variables

The following environment variables are required:

- `GROQ_API_KEY`: Your Groq API key for AI suggestions
- `WEATHER_API_KEY`: Your WeatherAPI.com key
- `DEEPGRAM_API_KEY`: Your Deepgram API key for speech-to-text
- `CORS_ORIGINS`: Comma-separated list of allowed origins (optional, defaults to localhost origins)

## Production Deployment

For production deployment, consider:

1. **Update CORS origins** in `docker-compose.yml`:
   ```yaml
   environment:
     - CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

2. **Use environment-specific builds**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **Add reverse proxy** (Nginx/Traefik) in front of services (optional)

4. **Use secrets management** instead of `.env` file for sensitive data

5. **Enable HTTPS** with SSL certificates

6. **Set up monitoring** and logging

7. **Use volume mounts** for persistent data (if needed)

## Troubleshooting

### Services won't start
- Check if ports 3000 and 8000 are already in use
- Verify `.env` file exists and contains valid API keys
- Check logs: `docker-compose logs`

### Frontend can't connect to backend
- Verify backend is healthy: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`
- Ensure CORS_ORIGINS includes the frontend URL

### Build fails
- Clear Docker cache: `docker-compose build --no-cache`
- Check Dockerfile syntax
- Verify all required files are present

### Permission issues
- Ensure Docker daemon is running
- Check file permissions in project directory

## Development with Docker

For development, you can mount volumes to enable hot-reload:

```yaml
# In docker-compose.yml, uncomment volumes for backend:
volumes:
  - ./backend:/app
```

Note: This is already configured for the backend service. For frontend, rebuild after changes:
```bash
docker-compose up -d --build frontend
```

## Clean Up

Remove all containers, networks, and volumes:
```bash
docker-compose down -v
```

Remove images:
```bash
docker-compose down --rmi all
```

