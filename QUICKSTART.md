# Quick Start Guide

Get Arborescent Trust up and running in 5 minutes.

## Prerequisites

- Docker & Docker Compose installed
- Git

## Step-by-Step Setup

### 1. Clone & Navigate

```bash
git clone https://github.com/yourusername/arborescent-trust.git
cd arborescent-trust/backend
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate a secure JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))" > jwt_secret.txt

# Edit .env and set JWT_SECRET_KEY to the generated value
# Or use the default for development (NOT FOR PRODUCTION!)
```

### 3. Start Services

```bash
# Start everything
docker-compose up -d

# Watch the logs
docker-compose logs -f api
```

Wait for: `✅ Database is ready` and `🚀 Arborescent Trust started`

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create admin user and initial invite tokens
docker-compose exec api python -m app.scripts.create_admin
```

**Save the invite tokens that are displayed!** You'll need them to create the first users.

### 5. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Open API documentation
open http://localhost:8000/docs
```

## Next Steps

### Register Your First User

1. Go to http://localhost:8000/docs
2. Find `POST /api/auth/register`
3. Click "Try it out"
4. Fill in:
   ```json
   {
     "email": "user@example.com",
     "username": "testuser",
     "password": "securepassword123",
     "invite_token": "TOKEN_FROM_ADMIN_CREATION"
   }
   ```
5. Click "Execute"

### Login

1. Find `POST /api/auth/login`
2. Use the credentials from registration
3. Copy the `access_token` from the response
4. Click "Authorize" at the top of the page
5. Paste: `Bearer YOUR_ACCESS_TOKEN`
6. Now you can test authenticated endpoints!

### Create Invite Tokens

1. Use `POST /api/invites/create` to generate new tokens
2. Share these tokens with others to invite them
3. Track your invites with `GET /api/invites/my-invites`

### View Your Tree

1. Use `GET /api/users/me/tree` to see your invite tree
2. As you invite users, your tree will grow
3. Check health scores with `GET /api/users/me/stats`

## Admin Functions

Login as admin (credentials from step 4):

### View Dashboard Stats

```bash
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:8000/api/admin/stats
```

### List All Users

```bash
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:8000/api/admin/users
```

### Prune a Branch (DRY RUN FIRST!)

```bash
curl -X POST -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"root_user_id": "USER_ID", "reason": "Test", "dry_run": true}' \
  http://localhost:8000/api/admin/prune
```

## Troubleshooting

### Services won't start

```bash
# Check if ports are already in use
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # API

# Stop and remove containers
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Database connection errors

```bash
# Check PostgreSQL is ready
docker-compose exec postgres pg_isready -U invitetree

# Check connection from API
docker-compose exec api python -c "from app.database import engine; print(engine.execute('SELECT 1').scalar())"
```

### Migration errors

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres redis
sleep 5
docker-compose exec api alembic upgrade head
```

### Can't access API docs

```bash
# Check API is running
docker-compose ps

# Check API logs
docker-compose logs api

# Restart API
docker-compose restart api
```

## Development Mode

### Run without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start API (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.tasks worker --loglevel=info

# In another terminal, start Celery beat
celery -A app.tasks beat --loglevel=info
```

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://invitetree:devpassword@localhost:5432/invite_tree_db

# JWT
JWT_SECRET_KEY=your-secret-key-here  # CHANGE THIS!
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Invite settings
DEFAULT_INVITE_QUOTA=5
INVITE_TOKEN_EXPIRY_HOURS=24

# Health thresholds
HEALTH_SCORE_LOW_THRESHOLD=50.0
SUPPORTING_TRUNK_MIN_DAYS=90
SUPPORTING_TRUNK_MIN_HEALTH=75.0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Debug
DEBUG=True  # Set to False in production!
```

## Common Tasks

### Create additional admin users

```bash
docker-compose exec api python
>>> from app.database import SessionLocal
>>> from app.models.user import User
>>> from app.core.security import hash_password
>>> from uuid import uuid4
>>> db = SessionLocal()
>>> admin = User(
...   id=uuid4(),
...   email="admin2@example.com",
...   username="admin2",
...   password_hash=hash_password("password123"),
...   role="admin",
...   is_core_member=True,
...   invite_quota=1000,
...   status="active"
... )
>>> db.add(admin)
>>> db.commit()
>>> exit()
```

### Manually expire tokens

```bash
docker-compose exec api python -c "
from app.database import SessionLocal
from app.services.invite_service import InviteService
db = SessionLocal()
service = InviteService(db)
count = service.expire_unused_tokens()
print(f'Expired {count} tokens')
"
```

### Recalculate health scores

```bash
docker-compose exec api python -c "
from app.database import SessionLocal
from app.services.health_service import HealthService
db = SessionLocal()
service = HealthService(db)
count = service.calculate_all_health_scores()
print(f'Calculated health for {count} users')
"
```

## Next: Read the Full Documentation

- [Backend README](backend/README.md) - Complete API reference
- [Technical Roadmap](invite_tree_roadmap.md) - Architecture details
- [Main README](README.md) - Overview and use cases

## Support

Having issues? 

1. Check the logs: `docker-compose logs api`
2. Check GitHub issues
3. Open a new issue with logs and error messages

Happy building! 🌳

