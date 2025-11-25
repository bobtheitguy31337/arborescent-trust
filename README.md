# Arborescent Trust

**A forensic-first invite tree system for tracking and surgically removing malicious actor networks.**

## Overview

Arborescent Trust implements an invite-only registration system where every user's lineage is tracked through a tree data structure. This enables retroactive forensic analysis and surgical removal of abuse networks - from bot farms to coordinated inauthentic behavior.

### Core Principle

**Build the data infrastructure to detect and surgically remove abuse networks, not to police human behavior.**

## Key Features

### 🌳 Invite Tree Architecture
- Every user (except core members) is invited by another user
- Creates a directed acyclic graph of relationships
- Enables tracing problems back to their source
- Supports recursive pruning of entire branches

### 🔍 Forensic Analysis
- **Immutable audit logs**: Every action permanently recorded
- **Forensic metadata**: Capture IP addresses, user agents, device fingerprints
- **Retroactive queries**: Analyze historical relationships
- **Health scores**: Automated quality metrics for subtrees

### ⚔️ Surgical Pruning
- Remove entire branches with one operation
- Soft delete maintains tree integrity
- Preview affected users before executing
- Full rollback capability

### 📊 Health Monitoring
- Automated health score calculation
- Maturity levels: Branch → Supporting Trunk → Core
- Background tasks for monitoring
- Auto-flagging of suspicious patterns

### 🛡️ Security
- JWT-based authentication
- Bcrypt password hashing
- Time-limited invite tokens (24h)
- Rate limiting (coming soon)
- Admin role-based access control

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│                                                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │    Auth    │  │  Invites   │  │   Users    │            │
│  │  Service   │  │  Service   │  │  Service   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Tree     │  │   Health   │  │   Prune    │            │
│  │  Service   │  │  Service   │  │  Service   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │    Celery    │
│   (Tree DB)  │  │  (Cache/Q)   │  │  (BG Tasks)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with recursive CTEs
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Auth**: JWT with refresh tokens
- **Password**: Bcrypt

## Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.11+, PostgreSQL 15+, Redis

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/arborescent-trust.git
cd arborescent-trust
```

### 2. Setup Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Services

```bash
# Start all services (PostgreSQL, Redis, API, Celery)
docker-compose up -d

# Watch logs
docker-compose logs -f api
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create admin user
docker-compose exec api python -m app.scripts.create_admin
```

### 5. Access API

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Documentation

### API Endpoints

See [backend/README.md](backend/README.md) for complete API documentation.

**Quick Overview:**

- **Authentication**: `/api/auth/*` - Register, login, refresh
- **Invites**: `/api/invites/*` - Create, validate, revoke tokens
- **Users**: `/api/users/*` - Profiles, trees, stats
- **Admin**: `/api/admin/*` - Management, pruning, audit logs

### Database Schema

See [invite_tree_roadmap.md](invite_tree_roadmap.md) for detailed schema documentation.

**Core Tables:**

- `users` - User accounts with tree relationships
- `invite_tokens` - Single-use invite codes
- `invite_audit_log` - Immutable event log
- `user_health_scores` - Quality metrics
- `prune_operations` - Branch removal records

### Background Tasks

- **Hourly**: Expire unused tokens
- **Daily**: Calculate health scores, flag low-health users, adjust quotas

## Use Cases

### 1. Social Platform Protection

Prevent bot networks from infiltrating your platform:

```
1. Bot operator creates account
2. Invites 50 bot accounts
3. Each bot invites 10 more bots
4. Health score drops due to suspicious patterns
5. Admin investigates, identifies root bot operator
6. Prunes entire branch: 550+ bots removed in one operation
```

### 2. Community Quality Control

Maintain high-quality communities:

```
1. Core members have high invite quotas
2. New members start with limited invites (3-5)
3. Health scores track quality of their invitees
4. High-quality inviters earn more quota
5. Low-quality branches get flagged for review
```

### 3. State Actor Detection

Identify coordinated inauthentic behavior:

```
1. Audit logs capture registration metadata
2. Pattern detection finds:
   - Same IP ranges
   - Similar user agents
   - Coordinated timing
3. Tree analysis reveals common ancestry
4. Forensic investigation traces to source
5. Surgical removal of network
```

## Development

### Project Structure

```
arborescent-trust/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Auth, security, deps
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── tasks/        # Celery tasks
│   │   └── main.py       # FastAPI app
│   ├── alembic/          # Database migrations
│   ├── tests/            # Test suite
│   └── docker-compose.yml
├── invite_tree_roadmap.md  # Technical roadmap
└── README.md
```

### Running Tests

```bash
cd backend
pytest
pytest --cov=app tests/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

See [backend/README.md](backend/README.md) for production deployment guide.

**Quick checklist:**

- [ ] Change `JWT_SECRET_KEY` to secure random value
- [ ] Set `DEBUG=False`
- [ ] Use managed PostgreSQL (RDS, Supabase, Render)
- [ ] Use managed Redis (Upstash, Redis Cloud)
- [ ] Configure CORS for your domain
- [ ] Enable HTTPS only
- [ ] Set up monitoring (Sentry, Prometheus)
- [ ] Configure automated backups

## Performance

Optimized for scale:

- **Tree queries**: O(log n) with proper indexing
- **Health calculation**: Batched daily processing
- **Pruning**: Efficient recursive CTEs
- **API response**: <200ms (p95)

Tested with:
- ✅ 10,000+ user trees
- ✅ Deep nesting (20+ levels)
- ✅ Concurrent operations
- ✅ Large batch pruning (1000+ users)

## Security Considerations

### What We Capture
- Email, username (required for accounts)
- Password hash (bcrypt)
- Registration IP, user agent, device fingerprint
- Invite relationships
- All actions in audit log

### What We Don't Capture
- Plain text passwords
- Unnecessary PII
- User activity beyond invite system

### Privacy
- Users can view their own tree
- Audit logs admin-only
- Data export capability
- Soft delete maintains privacy

## Roadmap

### Phase 1: Core System ✅
- [x] Database schema
- [x] Authentication
- [x] Invite system
- [x] Tree operations
- [x] Admin API

### Phase 2: Enhanced Detection 🚧
- [ ] Machine learning for pattern detection
- [ ] Graph analysis algorithms
- [ ] Automated bot detection
- [ ] Risk scoring

### Phase 3: Visualization 📋
- [ ] React admin dashboard
- [ ] D3.js tree visualization
- [ ] Real-time monitoring
- [ ] Analytics dashboard

### Phase 4: Advanced Features 📋
- [ ] Multi-tenant support
- [ ] Webhook notifications
- [ ] API rate limiting
- [ ] Blockchain audit trail (experimental)

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file.

## Support

- **Documentation**: See `/docs` in repo
- **Issues**: Open a GitHub issue
- **Security**: Report security issues privately to security@example.com

## Acknowledgments

Built with inspiration from:
- **Trust & Safety** best practices
- **Graph theory** for network analysis
- **Forensic analysis** methodologies
- **Community management** principles

---

**Built for platforms that care about quality over quantity.**

*Stop playing whack-a-mole with individual bad actors. Remove the entire tree.*
