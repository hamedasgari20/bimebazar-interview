This document outlines considerations for scaling the URL shortener service.

## 1. Logging Performance Impact

**Problem:** If logging each `GET /{short_code}` request (including writing to the `VisitLog` table and potentially sending logs externally) becomes time-consuming, it will increase the latency of the redirect request, impacting user experience. Synchronous logging ties the redirect response time directly to the logging time.

**Solutions:**

1.  **Asynchronous Background Tasks (Implemented):**
    *   **Approach:** Use FastAPI's built-in `BackgroundTasks`. The redirect response is sent immediately, and the logging (`VisitLog` insert) and `visit_count` increment happen in a separate thread *after* the response.
    *   **Pros:** Simple to implement within FastAPI, decouples logging from the request lifecycle, significantly reduces redirect latency.
    *   **Cons:** Runs within the same application process. A surge in requests can still overwhelm the server's capacity to handle background tasks. No built-in retry mechanism or persistence if the server crashes before the task completes.

2.  **Dedicated Task Queue (e.g., Celery with Redis/RabbitMQ):**
    *   **Approach:** Instead of `BackgroundTasks`, publish logging/increment jobs to a message queue (like Redis or RabbitMQ). Dedicated worker processes consume jobs from the queue and perform the database operations.
    *   **Pros:** Robust decoupling. Workers can be scaled independently of API servers. Provides persistence, retry mechanisms, and better resource management. Handles bursts effectively.
    *   **Cons:** Adds infrastructure complexity (queue broker, worker processes).


**Chosen Approach (Initial):** BackgroundTasks for simplicity, suitable for moderate load. For higher scale, migrating to a dedicated Task Queue (Celery) is recommended.

## 2. Multi-Instance Deployment

**Problem:** Running the application on a single server limits throughput and provides no redundancy. Scaling requires running multiple instances across different servers/containers.

**Changes Needed & Decoupling:**

1.  **Stateless Application Servers:** The FastAPI application instances *must* be stateless. Any state required across requests (like user sessions, if added later) needs to be externalized.
2.  **Externalized Database:** The database (PostgreSQL, MySQL, etc.) must be accessible by all application instances. Use a managed database service (AWS RDS, Google Cloud SQL) or a properly configured, highly available database cluster. Connection pooling (handled by SQLAlchemy's engine) is crucial.
3.  **Load Balancer:** Introduce a load balancer (Nginx, HAProxy, AWS ELB, Cloudflare) in front of the application instances to distribute incoming traffic.
4.  **Shared Cache (Highly Recommended, per diagram):** Implement caching (e.g., using Redis or Memcached) for `short_code -> original_url` lookups. This cache must be shared and accessible by all instances. This significantly reduces database load for the high-traffic redirect endpoint.
5.  **Shared Task Queue (If using Celery/etc.):** If using a task queue for background jobs (logging, increments), the queue broker (Redis, RabbitMQ) must be shared and accessible by all API instances (producers) and worker instances (consumers).
6.  **Centralized Configuration:** Manage configuration (like `DATABASE_URL`, cache address) consistently across instances, typically using environment variables injected during deployment or a configuration management service.
7.  **Containerization (Docker/Kubernetes):** Package the application using Docker for consistent environments. Use Kubernetes or similar orchestrators to manage deployment, scaling, and health checks of application instances, workers, cache, etc.

**Potential Risks & Mitigation:**

*   **Single Points of Failure (SPOF):** Database, Cache, Queue Broker, Load Balancer can become SPOFs.
    *   **Mitigation:** Use managed services with built-in high availability (HA), configure replicas/clusters for self-hosted components, use multiple load balancer instances.
*   **Data Consistency:** Ensuring cache coherence across instances if data changes.
    *   **Mitigation:** Implement appropriate cache invalidation strategies (e.g., delete cache entry when URL mapping is updated/deleted - though less relevant for this simple app). Use Time-To-Live (TTL) effectively.
*   **Deployment Complexity:** Coordinating updates across multiple instances.
    *   **Mitigation:** Use deployment strategies like Blue/Green or Canary deployments managed by orchestration tools. Automate deployment pipelines.

## 3. Handling High Traffic (Marketing Campaign)

**Problem:** A sudden surge to thousands of requests per second (RPS) can overwhelm the system, leading to slow responses or failures.

**Measures:**

1.  **Aggressive Caching (Primary Defense):**
    *   **Target:** `GET /{short_code}` endpoint (redirects). This is likely the highest volume endpoint.
    *   **Implementation:** Use an external, in-memory cache like **Redis** or **Memcached** (as shown in the design diagram) to store `short_code` -> `original_url` mappings with a suitable TTL (e.g., hours or days, depending on how often URLs change, if ever).
    *   **Flow:** Request comes -> Check Cache -> If Hit, redirect immediately -> If Miss, Query DB -> Store in Cache -> Redirect.
    *   **Impact:** Drastically reduces read load on the primary database. Can handle a massive number of redirects.

2.  **Database Optimization:**
    *   **Connection Pooling:** Ensure SQLAlchemy's connection pool is appropriately sized (`pool_size`, `max_overflow`). (Already configured via `create_engine`).
    *   **Read Replicas:** If DB reads are still a bottleneck *after* caching, configure database read replicas. Direct read-heavy queries (like potentially `/stats`, though this might also be cached) to replicas. Writes (`/shorten`, count increments) go to the primary.
    *   **Indexing:** Ensure critical columns (`short_code`, `url_mapping_id`, `visit_time`) are indexed. (Done via models/Alembic).
    *   **Async Database Operations:** Switch to an async DB driver (like `asyncpg` for PostgreSQL) and use async session/queries within FastAPI endpoints (`async def` endpoints with `await db.execute(...)`). This improves concurrency handling within each application instance.

3.  **Horizontal Scaling:**
    *   **Application Instances:** Increase the number of running FastAPI application instances behind the load balancer. Orchestration tools (Kubernetes HPA) can automate this based on CPU/memory usage or request counts.
    *   **Worker Instances:** If using a task queue (Celery), scale the number of worker instances independently to handle the load of background jobs (logging, increments).

4.  **Rate Limiting:**
    *   **Target:** Primarily `POST /shorten` to prevent abuse/overload. Possibly apply lighter limits to `/stats` or even `/` if needed.
    *   **Implementation:** Use middleware in FastAPI (e.g., `slowapi` library) or implement at the API Gateway/Load Balancer level.

5.  **Queue-Based Processing (Reinforced):**
    *   **Target:** Logging (`VisitLog` insert) and `visit_count` increments.
    *   **Implementation:** Move these operations from FastAPI `BackgroundTasks` to a robust message queue (Celery/Redis/RabbitMQ/Kafka). This decouples the write operations entirely from the request path and absorbs traffic bursts effectively.

