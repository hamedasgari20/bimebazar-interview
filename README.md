# URL Shortener Service

![System Design](system_design.jpg)

## System Design Overview

The URL Shortener service is built using a modern architecture with the following components:

1. **FastAPI Application Server**
   - Handles HTTP requests and responses
   - Implements URL shortening logic
   - Manages API endpoints
   - Built with Python and FastAPI framework

2. **PostgreSQL Database**
   - Stores URL mappings and visit statistics
   - Maintains data persistence
   - Handles concurrent requests efficiently

3. **Redis Cache**
   - Provides fast access to frequently accessed URLs
   - Reduces database load
   - Implements caching with TTL (Time To Live)
   - Improves response times for popular URLs

## Project Description

This URL Shortener service provides a robust and scalable solution for creating short URLs from long ones. The service includes features like:

- URL shortening with custom short codes
- URL redirection with visit tracking
- Visit statistics and analytics
- Caching for improved performance

## Prerequisites

- Docker
- Docker Compose
- Git

## Getting Started

1. Clone the repository:
```bash
git clone <repository-url>
cd url-shortener
```

2. Create a `.env` file in the root directory with the following variables:
```env
ENV_SETTING=dev
PG_DSN=postgresql+asyncpg://debug:debug@db:5432/db
SHORT_CODE_LENGTH=5
REDIS_URL=redis
REDIS_PORT=6379
REDIS_DB_NUMBER=0
```

3. Run the application using Docker Compose:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`


## Docker Compose Services

The project uses Docker Compose to manage three main services:

1. **app**: The FastAPI application
   - Port: 8000
   - Depends on Redis and PostgreSQL
   - Includes database initialization script
   - Hot-reload enabled for development

2. **db**: PostgreSQL database
   - Port: 5432
   - Persistent volume for data storage
   - Environment variables for configuration

3. **redis**: Redis cache
   - Port: 6379
   - Used for caching and rate limiting

## Development

### Project Structure
```
url-shortener/
├── app/
│   ├── api/
│   ├── repositories/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── tasks/
│   ├── utils/
│   └── main.py
│   └── config.py
├── scripts/
│   └── init-db.sh
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
