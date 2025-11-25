# Arborescent Trust - Invite Tree API

A forensic-first invite tree system for tracking and surgically removing malicious actor networks.

## Features

- **Invite-only registration** with token-based access control
- **Tree/graph data structure** for tracking invite relationships
- **Recursive pruning** to remove entire branches of bad actors
- **Health score calculation** based on subtree quality
- **Immutable audit logging** for forensic analysis
- **Background tasks** for token expiration and health monitoring
- **Admin dashboard API** for investigation and management

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with recursive CTEs
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **ORM**: SQLAlchemy
- **Migrations**: Alembic

## Quick Start

### 1. Clone and Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
```

### 2. Run with Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI API (port 8000)
- Celery Worker
- Celery Beat (scheduler)

### 3. Run Database Migrations

```bash
# Create initial migration
docker-compose exec api alembic revision --autogenerate -m "Initial schema"

# Apply migrations
docker-compose exec api alembic upgrade head
```

### 4. Create Initial Admin User

```bash
docker-compose exec api python -m app.scripts.create_admin
```

### 5. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development Setup

### Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis locally
# Or use docker-compose for just the databases:
docker-compose up postgres redis -d

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload

# Start Celery worker (in another terminal)
celery -A app.tasks worker --loglevel=info

# Start Celery beat (in another terminal)
celery -A app.tasks beat --loglevel=info
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register with invite token
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Invites
- `POST /api/invites/create` - Create invite tokens
- `GET /api/invites/my-invites` - List your invites
- `GET /api/invites/validate/{token}` - Validate token (public)
- `POST /api/invites/revoke/{token_id}` - Revoke token

### Users
- `GET /api/users/me` - Your profile
- `GET /api/users/{id}` - Public profile
- `GET /api/users/{id}/tree` - Invite tree (descendants)
- `GET /api/users/{id}/ancestors` - Path to root
- `GET /api/users/{id}/stats` - Tree statistics

### Admin (Requires admin role)
- `GET /api/admin/stats` - Dashboard statistics
- `GET /api/admin/users` - List all users
- `GET /api/admin/users/{id}` - Detailed user info
- `POST /api/admin/users/{id}/flag` - Flag user
- `POST /api/admin/prune` - Prune branch
- `GET /api/admin/prune-history` - Prune history
- `GET /api/admin/audit-log` - Audit log
- `POST /api/admin/quota/adjust` - Adjust user quota

## Background Tasks

### Hourly
- **Token Expiration**: Expire unused tokens and credit back to creators

### Daily
- **Health Score Calculation**: Calculate health scores for all users
- **Flag Low Health Users**: Auto-flag users below threshold
- **Quota Adjustment**: Grant additional invites to healthy users

## Database Schema

### Core Tables
- `users` - User accounts with tree relationships
- `invite_tokens` - Single-use invite codes
- `invite_audit_log` - Immutable event log
- `user_health_scores` - Calculated health metrics
- `prune_operations` - Branch removal records

### Key Indexes
- Tree traversal: `invited_by_user_id`
- Token lookups: `token`, `is_used`
- Audit queries: `event_type`, `created_at`

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_tree_service.py
```

## Deployment

### Production Checklist

1. **Environment Variables**
   - Change `JWT_SECRET_KEY` to secure random value
   - Set `DEBUG=False`
   - Configure `CORS_ORIGINS` for your domain
   - Use secure database credentials

2. **Database**
   - Use managed PostgreSQL (RDS, Supabase, Render)
   - Enable connection pooling
   - Set up automated backups
   - Configure SSL/TLS connections

3. **Redis**
   - Use managed Redis (Upstash, Redis Cloud)
   - Enable persistence

4. **Application**
   - Use Gunicorn + Uvicorn workers
   - Configure proper logging (Sentry)
   - Set up monitoring (Prometheus/Grafana)
   - Enable HTTPS only

5. **Migrations**
   - Run `alembic upgrade head` on deploy
   - Never auto-create tables in production

## Architecture Highlights

### Forensic-First Design
- **Immutable audit logs**: All actions logged permanently
- **Soft deletes**: Never hard delete users (breaks tree integrity)
- **Forensic metadata**: Capture IP, user agent, device fingerprint
- **Retroactive analysis**: Query historical relationships

### Tree Operations
- **Recursive CTEs**: Efficient subtree/ancestor queries
- **Health scores**: Weighted calculation based on descendant quality
- **Surgical pruning**: Remove entire branches while maintaining tree integrity
- **Maturity levels**: Branch → Supporting Trunk → Core

### Security
- **JWT authentication**: Short-lived access tokens (15 min)
- **Refresh token rotation**: 7-day expiry
- **Password hashing**: Bcrypt with cost factor 12
- **Rate limiting**: Redis-backed (coming soon)
- **Input validation**: Pydantic schemas

## Contributing

See main repository README for contribution guidelines.

## License

See LICENSE file in repository root.

## Support

For issues and questions, open an issue on GitHub.

