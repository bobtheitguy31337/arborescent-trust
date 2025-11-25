# Invite Tree System - Technical Roadmap

## Executive Summary

This document outlines the technical foundation for a forensic-first invite system designed to track and prune malicious actor networks. The system uses a tree/graph data structure to maintain invite relationships and provides retroactive audit capabilities for identifying coordinated inauthentic behavior (bots, spam networks, state actors).

**Core Principle**: Build the data infrastructure to detect and surgically remove abuse networks, not to police human behavior.

---

## System Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with recursive CTE support
- **Auth**: JWT-based authentication with refresh tokens
- **Cache**: Redis (for token validation, rate limiting)
- **Task Queue**: Celery + Redis (for async operations like tree health calculations)
- **API Documentation**: Built-in FastAPI OpenAPI/Swagger
- **Admin Dashboard**: React + FastAPI backend endpoints

### Deployment Targets
- Web application
- Mobile applications (iOS/Android via API)

---

## Phase 1: Core Data Models & Database Schema

### 1.1 User Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- User type
    is_core_member BOOLEAN DEFAULT FALSE,
    
    -- Invite capacity
    invite_quota INTEGER DEFAULT 0,
    invites_used INTEGER DEFAULT 0,
    
    -- Tree relationship
    invited_by_user_id UUID REFERENCES users(id),
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, banned, flagged
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    
    -- Forensic data (captured at registration)
    registration_ip INET,
    registration_user_agent TEXT,
    registration_fingerprint VARCHAR(255), -- browser/device fingerprint
    
    -- Soft delete
    deleted_at TIMESTAMP NULL,
    deleted_reason TEXT NULL
);

CREATE INDEX idx_users_invited_by ON users(invited_by_user_id);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;
```

### 1.2 Invite Tokens Table
```sql
CREATE TABLE invite_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(64) UNIQUE NOT NULL, -- cryptographically secure random string
    
    -- Ownership
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    
    -- Usage
    used_by_user_id UUID REFERENCES users(id),
    is_used BOOLEAN DEFAULT FALSE,
    
    -- Expiration
    expires_at TIMESTAMP NOT NULL,
    
    -- Status
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP NULL,
    revoked_by_user_id UUID REFERENCES users(id),
    revoked_reason TEXT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    used_at TIMESTAMP NULL,
    
    -- Metadata (for forensics)
    used_ip INET NULL,
    used_user_agent TEXT NULL
);

CREATE INDEX idx_invite_tokens_token ON invite_tokens(token);
CREATE INDEX idx_invite_tokens_creator ON invite_tokens(created_by_user_id);
CREATE INDEX idx_invite_tokens_used_by ON invite_tokens(used_by_user_id);
CREATE INDEX idx_invite_tokens_expires ON invite_tokens(expires_at);
```

### 1.3 Invite Tree Audit Log (Immutable)
```sql
CREATE TABLE invite_audit_log (
    id BIGSERIAL PRIMARY KEY,
    
    -- Event type
    event_type VARCHAR(50) NOT NULL, -- token_created, token_used, token_expired, token_revoked, user_pruned, quota_adjusted
    
    -- Actors
    actor_user_id UUID REFERENCES users(id), -- who performed the action
    target_user_id UUID REFERENCES users(id), -- who was affected
    invite_token_id UUID REFERENCES invite_tokens(id),
    
    -- Event data (JSONB for flexible forensic data)
    event_data JSONB NOT NULL,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Forensic context
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_audit_event_type ON invite_audit_log(event_type);
CREATE INDEX idx_audit_actor ON invite_audit_log(actor_user_id);
CREATE INDEX idx_audit_target ON invite_audit_log(target_user_id);
CREATE INDEX idx_audit_created ON invite_audit_log(created_at);
CREATE INDEX idx_audit_event_data ON invite_audit_log USING GIN(event_data);
```

### 1.4 User Health Scores (Calculated Periodically)
```sql
CREATE TABLE user_health_scores (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Health metrics
    subtree_size INTEGER DEFAULT 0, -- total descendants
    subtree_active_count INTEGER DEFAULT 0,
    subtree_flagged_count INTEGER DEFAULT 0,
    subtree_banned_count INTEGER DEFAULT 0,
    
    -- Calculated scores (0-100)
    direct_invitee_health DECIMAL(5,2) DEFAULT 100.0,
    subtree_health DECIMAL(5,2) DEFAULT 100.0,
    overall_health DECIMAL(5,2) DEFAULT 100.0,
    
    -- Tree depth
    max_depth_below INTEGER DEFAULT 0,
    
    -- Maturity status
    maturity_level VARCHAR(20) DEFAULT 'branch', -- branch, supporting_trunk, core
    
    -- Timestamps
    calculated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, calculated_at)
);

CREATE INDEX idx_health_user ON user_health_scores(user_id);
CREATE INDEX idx_health_calculated ON user_health_scores(calculated_at);
CREATE INDEX idx_health_overall ON user_health_scores(overall_health);
```

### 1.5 Prune Operations Log
```sql
CREATE TABLE prune_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Target
    root_user_id UUID NOT NULL REFERENCES users(id), -- root of pruned branch
    
    -- Operation details
    affected_user_count INTEGER NOT NULL,
    reason TEXT NOT NULL,
    
    -- Decision maker
    executed_by_user_id UUID REFERENCES users(id), -- admin who executed
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, rolled_back
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    executed_at TIMESTAMP NULL,
    
    -- Affected users snapshot (for potential rollback)
    affected_users JSONB NOT NULL
);

CREATE INDEX idx_prune_root ON prune_operations(root_user_id);
CREATE INDEX idx_prune_executed_by ON prune_operations(executed_by_user_id);
CREATE INDEX idx_prune_created ON prune_operations(created_at);
```

---

## Phase 2: Core Backend Services (FastAPI)

### 2.1 Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment config
│   ├── database.py             # Database connection
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── invite_token.py
│   │   ├── audit_log.py
│   │   ├── health_score.py
│   │   └── prune_operation.py
│   │
│   ├── schemas/                # Pydantic models for API
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── invite.py
│   │   ├── auth.py
│   │   └── admin.py
│   │
│   ├── api/                    # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py             # Login, register, refresh
│   │   ├── invites.py          # Invite CRUD
│   │   ├── users.py            # User profile, tree view
│   │   └── admin.py            # Admin dashboard endpoints
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── invite_service.py
│   │   ├── tree_service.py     # Graph traversal logic
│   │   ├── health_service.py   # Health score calculation
│   │   └── prune_service.py    # Pruning operations
│   │
│   ├── core/                   # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py         # Password hashing, JWT
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   └── exceptions.py       # Custom exceptions
│   │
│   └── tasks/                  # Celery tasks
│       ├── __init__.py
│       ├── invite_tasks.py     # Token expiration checker
│       └── health_tasks.py     # Periodic health recalculation
│
├── alembic/                    # Database migrations
├── tests/
├── requirements.txt
└── .env
```

### 2.2 Authentication Service

**JWT-based authentication with refresh tokens**

Endpoints:
- `POST /api/auth/register` - Create account with invite token
- `POST /api/auth/login` - Login, return access + refresh tokens
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Invalidate refresh token

**Security Features**:
- Password hashing with bcrypt
- Access tokens (15 min expiry)
- Refresh tokens (7 day expiry, stored in Redis with rotation)
- Rate limiting on auth endpoints
- Capture forensic metadata (IP, user agent, fingerprint)

### 2.3 Invite Service

**Core Functionality**:
- Generate invite tokens (cryptographically secure)
- Validate invite tokens (check expiry, usage, revocation)
- Track token usage
- Auto-expire unused tokens after 24 hours
- Credit back expired invites to creator's quota
- Allow core members to revoke tokens

**Endpoints**:
- `POST /api/invites/create` - Generate new invite token(s)
- `GET /api/invites/my-invites` - List user's created invites
- `POST /api/invites/revoke/{token_id}` - Revoke an invite
- `GET /api/invites/validate/{token}` - Check if token is valid (public)

**Business Rules**:
- Core members: Can generate invites up to their quota
- Regular users: Start with limited quota (3-5), earn more over time
- Tokens expire in 24 hours if unused
- Expired tokens credit back to creator's available quota
- All operations logged to audit log

### 2.4 Tree Service

**Graph Traversal Operations**:
- Get user's ancestors (path to root)
- Get user's descendants (entire subtree)
- Calculate subtree depth
- Count active/flagged/banned users in subtree
- Find "trunk" ancestors (users who've matured to supporting trunks)

**Key Queries**:
```sql
-- Get all descendants (recursive CTE)
WITH RECURSIVE subtree AS (
    SELECT id, invited_by_user_id, 0 as depth
    FROM users
    WHERE id = $root_user_id
    
    UNION ALL
    
    SELECT u.id, u.invited_by_user_id, st.depth + 1
    FROM users u
    INNER JOIN subtree st ON u.invited_by_user_id = st.id
    WHERE u.deleted_at IS NULL
)
SELECT * FROM subtree;

-- Get ancestors (path to root)
WITH RECURSIVE ancestors AS (
    SELECT id, invited_by_user_id, 0 as depth
    FROM users
    WHERE id = $user_id
    
    UNION ALL
    
    SELECT u.id, u.invited_by_user_id, a.depth + 1
    FROM users u
    INNER JOIN ancestors a ON a.invited_by_user_id = u.id
)
SELECT * FROM ancestors;
```

**Endpoints**:
- `GET /api/users/{user_id}/tree` - Get subtree visualization data
- `GET /api/users/{user_id}/ancestors` - Get path to root
- `GET /api/users/{user_id}/descendants` - Get all descendants with health data

### 2.5 Health Score Service

**Calculation Logic**:

Health score is calculated based on:
- Direct invitees' status (50% weight)
- Second-level descendants (30% weight)
- Third-level+ descendants (20% weight)

Formula:
```python
def calculate_health_score(user_id: UUID) -> float:
    # Get subtree statistics
    stats = get_subtree_stats(user_id)
    
    # Weight by depth
    direct_health = (stats.direct_active / stats.direct_total) * 100 if stats.direct_total > 0 else 100
    level2_health = (stats.level2_active / stats.level2_total) * 100 if stats.level2_total > 0 else 100
    level3_health = (stats.level3_active / stats.level3_total) * 100 if stats.level3_total > 0 else 100
    
    # Penalties for flagged/banned
    penalty = (stats.flagged_count * 10) + (stats.banned_count * 25)
    
    overall = (direct_health * 0.5) + (level2_health * 0.3) + (level3_health * 0.2) - penalty
    
    return max(0, min(100, overall))
```

**Maturity Level Determination**:
```python
def determine_maturity(user: User, health_score: float) -> str:
    if user.is_core_member:
        return "core"
    
    account_age_days = (now() - user.created_at).days
    subtree_depth = get_max_subtree_depth(user.id)
    subtree_size = get_subtree_size(user.id)
    
    # Supporting trunk criteria
    if (account_age_days >= 90 and 
        health_score >= 75 and 
        subtree_depth >= 3 and 
        subtree_size >= 10):
        return "supporting_trunk"
    
    return "branch"
```

**Background Task** (Celery):
- Run health calculation daily for all users
- Store results in `user_health_scores` table
- Trigger alerts for users dropping below thresholds

### 2.6 Prune Service

**Pruning Operations**:

When a branch is identified for pruning:
1. Create `prune_operation` record (pending status)
2. Recursively mark all descendants as `deleted_at = NOW()`
3. Log each affected user to `affected_users` JSONB
4. Update prune operation status to `completed`
5. Audit log all operations

**Soft Delete Implementation**:
```python
async def prune_branch(root_user_id: UUID, reason: str, executed_by: UUID):
    # Get all descendants
    descendants = await get_all_descendants(root_user_id)
    
    # Create prune operation record
    prune_op = PruneOperation(
        root_user_id=root_user_id,
        affected_user_count=len(descendants),
        reason=reason,
        executed_by_user_id=executed_by,
        affected_users=[{
            "id": str(u.id),
            "username": u.username,
            "created_at": u.created_at.isoformat()
        } for u in descendants]
    )
    await db.save(prune_op)
    
    # Soft delete all users
    for user in descendants:
        user.deleted_at = datetime.utcnow()
        user.deleted_reason = f"Pruned: {reason}"
        user.status = "banned"
        await db.save(user)
        
        # Audit log
        await log_audit_event(
            event_type="user_pruned",
            actor_user_id=executed_by,
            target_user_id=user.id,
            event_data={
                "prune_operation_id": str(prune_op.id),
                "reason": reason
            }
        )
    
    prune_op.status = "completed"
    prune_op.executed_at = datetime.utcnow()
    await db.save(prune_op)
```

**Endpoints**:
- `POST /api/admin/prune` - Execute prune operation
- `GET /api/admin/prune-history` - List past prune operations
- `GET /api/admin/prune/{operation_id}` - Get details of specific prune

---

## Phase 3: Admin Dashboard

### 3.1 Dashboard Features

**Overview Page**:
- Total users (active, flagged, banned)
- Invite token statistics
- Recent prune operations
- Health score distribution chart

**Tree Visualization**:
- Interactive D3.js tree/graph visualization
- Color-coded nodes by health score
- Click to drill into subtrees
- Search for specific users

**User Investigation**:
- Search users by username, email
- View full invite ancestry (path to root)
- View full subtree with health scores
- Timeline of user activity
- Audit log for specific user

**Flagging & Review**:
- Queue of users flagged by automated detection
- Ability to investigate, approve, or prune
- Bulk operations for efficiency

**Prune Operations**:
- Initiate prune with reason
- Preview affected users before execution
- History of past prunes
- Rollback capability (if needed)

### 3.2 Admin Endpoints

```python
# Admin-only routes (require admin role check)
GET  /api/admin/stats                    # Dashboard overview stats
GET  /api/admin/users                    # Paginated user list with filters
GET  /api/admin/users/{id}/full-tree     # Complete tree data for user
POST /api/admin/users/{id}/flag          # Manually flag a user
POST /api/admin/users/{id}/unflag        # Remove flag
GET  /api/admin/audit-log                # Searchable audit log
GET  /api/admin/health-scores            # Users sorted by health score
POST /api/admin/prune                    # Execute prune operation
GET  /api/admin/prune-history            # Past prune operations
```

### 3.3 Admin Role System

Simple role-based access:
```python
# Add to users table
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';
-- Roles: user, admin, superadmin

# Dependency for admin-only routes
async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

---

## Phase 4: Background Tasks & Automation

### 4.1 Celery Tasks

**Invite Token Expiration** (runs every hour):
```python
@celery.task
def expire_unused_tokens():
    # Find tokens expired but not marked used
    expired = InviteToken.query.filter(
        InviteToken.expires_at < datetime.utcnow(),
        InviteToken.is_used == False,
        InviteToken.is_revoked == False
    ).all()
    
    for token in expired:
        # Mark as revoked
        token.is_revoked = True
        token.revoked_reason = "Auto-expired"
        
        # Credit back to creator
        creator = token.created_by_user
        creator.invites_used -= 1
        
        # Audit log
        log_audit_event(
            event_type="token_expired",
            actor_user_id=None,
            target_user_id=creator.id,
            invite_token_id=token.id,
            event_data={"token": token.token}
        )
        
        db.commit()
```

**Health Score Calculation** (runs daily):
```python
@celery.task
def calculate_all_health_scores():
    users = User.query.filter(User.deleted_at.is_(None)).all()
    
    for user in users:
        health_score = calculate_health_score(user.id)
        maturity = determine_maturity(user, health_score)
        
        HealthScore.create(
            user_id=user.id,
            overall_health=health_score,
            maturity_level=maturity,
            calculated_at=datetime.utcnow()
        )
        
        # Check for threshold alerts
        if health_score < 50:
            # Trigger alert/notification
            flag_user_for_review(user.id, "Low health score")
```

**Invite Quota Growth** (runs daily):
```python
@celery.task
def adjust_invite_quotas():
    """Grant additional invite capacity to healthy, mature users"""
    
    users = get_users_eligible_for_quota_increase()
    
    for user in users:
        additional_invites = calculate_quota_increase(user)
        
        if additional_invites > 0:
            user.invite_quota += additional_invites
            
            log_audit_event(
                event_type="quota_adjusted",
                actor_user_id=None,
                target_user_id=user.id,
                event_data={
                    "old_quota": user.invite_quota - additional_invites,
                    "new_quota": user.invite_quota,
                    "reason": "Earned through healthy subtree growth"
                }
            )
```

---

## Phase 5: API Design & Documentation

### 5.1 Core API Endpoints

**Authentication**:
```
POST   /api/auth/register          # Register with invite token
POST   /api/auth/login             # Login, get JWT tokens
POST   /api/auth/refresh           # Refresh access token
POST   /api/auth/logout            # Invalidate refresh token
GET    /api/auth/me                # Get current user info
```

**Invites**:
```
POST   /api/invites/create         # Generate invite token(s)
GET    /api/invites/my-invites     # List user's created invites
POST   /api/invites/revoke/{id}    # Revoke invite token
GET    /api/invites/validate/{token} # Validate token (public)
```

**Users**:
```
GET    /api/users/me               # Current user profile
GET    /api/users/{id}             # Public user profile
GET    /api/users/{id}/tree        # User's subtree data
GET    /api/users/{id}/ancestors   # Path to root
```

**Admin** (protected):
```
GET    /api/admin/stats            # Dashboard stats
GET    /api/admin/users            # All users (paginated, filtered)
GET    /api/admin/users/{id}/full-tree # Complete tree for user
POST   /api/admin/users/{id}/flag  # Flag user for review
GET    /api/admin/audit-log        # Audit log viewer
POST   /api/admin/prune            # Execute prune operation
GET    /api/admin/prune-history    # Past prunes
```

### 5.2 Response Formats

**Standard Success Response**:
```json
{
    "success": true,
    "data": { ... },
    "message": "Operation successful"
}
```

**Standard Error Response**:
```json
{
    "success": false,
    "error": {
        "code": "INVALID_TOKEN",
        "message": "Invite token is expired or invalid",
        "details": { ... }
    }
}
```

### 5.3 Rate Limiting

Implement rate limiting on sensitive endpoints:
- Auth endpoints: 5 requests/minute per IP
- Invite creation: 10 requests/hour per user
- Admin operations: 100 requests/hour per admin

Use Redis for rate limit storage.

---

## Phase 6: Security & Privacy Considerations

### 6.1 Security Measures

**Authentication Security**:
- Bcrypt password hashing (cost factor 12)
- JWT with short expiry (15 min access, 7 day refresh)
- Refresh token rotation
- IP-based anomaly detection on login
- Rate limiting on auth endpoints

**Invite Token Security**:
- Cryptographically secure random tokens (64 chars)
- Single-use only
- Time-limited (24h expiry)
- Revocation capability

**Database Security**:
- Prepared statements (SQLAlchemy ORM handles this)
- Role-based database access
- Encrypted connections (TLS)
- Regular backups

**API Security**:
- HTTPS only
- CORS properly configured
- Input validation (Pydantic)
- Rate limiting
- Admin endpoints require elevated privileges

### 6.2 Privacy Considerations

**Data Minimization**:
- Only collect forensic metadata necessary for abuse detection
- Don't store unnecessary PII

**User Rights**:
- Allow users to view their own invite tree
- Allow users to export their data
- Handle account deletion (soft delete maintains tree integrity)

**Audit Log Access**:
- Audit logs only accessible to admins
- Consider anonymizing IP addresses after certain time period

---

## Phase 7: Testing Strategy

### 7.1 Unit Tests
- Test each service in isolation
- Mock database calls
- Test edge cases (expired tokens, invalid users, etc.)

### 7.2 Integration Tests
- Test API endpoints end-to-end
- Test database transactions
- Test auth flow
- Test invite flow (create → use → expire)

### 7.3 Graph/Tree Tests
- Test recursive queries with deep trees
- Test pruning operations
- Test health score calculations
- Performance test with large subtrees (10k+ users)

### 7.4 Load Testing
- Simulate hundreds of thousands of users
- Test concurrent invite token creation/usage
- Test health score calculation performance
- Identify bottlenecks in graph traversal

---

## Phase 8: Deployment & DevOps

### 8.1 Infrastructure

**Production Environment**:
- FastAPI app (Gunicorn + Uvicorn workers)
- PostgreSQL 15+ (with regular backups)
- Redis (for caching + task queue)
- Celery workers (for background tasks)
- Nginx (reverse proxy, SSL termination)

**Recommended Hosting**:
- Render, Railway, or AWS ECS for app
- Managed PostgreSQL (RDS, Supabase, or Render)
- Managed Redis (Upstash, Redis Cloud)

### 8.2 Database Migrations

Use Alembic for schema migrations:
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### 8.3 Environment Configuration

```bash
# .env file
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0
JWT_SECRET_KEY=<secure-random-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=https://yourapp.com,https://mobile.yourapp.com
```

### 8.4 Monitoring & Logging

**Application Monitoring**:
- Sentry for error tracking
- Prometheus + Grafana for metrics
- Custom metrics: invite usage, health score distribution, prune operations

**Database Monitoring**:
- Query performance monitoring
- Connection pool metrics
- Slow query log analysis

**Audit Log Retention**:
- Store forever (they're append-only, shouldn't grow too large)
- Consider archiving to cold storage after 1 year

---

## Phase 9: Future Enhancements

### 9.1 Advanced Detection

**Machine Learning Models**:
- Train models on pruned branch characteristics
- Predict likelihood of coordinated behavior
- Automate flagging (with human review)

**Graph Analysis**:
- Community detection algorithms
- Identify tightly-coupled clusters
- Anomaly detection in growth patterns

### 9.2 Blockchain Integration (Fun Experiment)

Store immutable audit trail on blockchain:
- Use Ethereum/Polygon for invite tree events
- Each prune operation gets a transaction hash
- Provides tamper-proof forensic trail
- Note: This is expensive and slow, use sparingly

**Implementation**:
```python
# Store critical events on-chain
async def log_to_blockchain(event: AuditEvent):
    tx_hash = await web3.eth.send_transaction({
        'to': CONTRACT_ADDRESS,
        'data': encode_event(event)
    })
    
    # Store tx_hash in audit log for reference
    event.blockchain_tx_hash = tx_hash
```

### 9.3 User-Facing Features

**Invite Reputation Dashboard**:
- Show users their own health score
- Show their subtree growth
- Gamify healthy inviting

**Invite Request System**:
- Allow users to request invites from existing members
- Vouching system

**Transparency Reports**:
- Public stats on prune operations (anonymized)
- Build trust by showing you're actively fighting abuse

---

## Implementation Timeline

### Week 1-2: Foundation
- Set up FastAPI project structure
- Database schema + migrations
- User model + auth service
- JWT implementation

### Week 3-4: Invite System
- Invite token generation/validation
- Token expiration logic
- Audit logging
- Basic API endpoints

### Week 5-6: Tree Operations
- Recursive tree queries
- Health score calculation
- Maturity level logic
- Tree service API

### Week 7-8: Admin Dashboard
- Admin API endpoints
- React dashboard scaffolding
- Tree visualization (D3.js)
- User search + investigation tools

### Week 9-10: Background Tasks
- Celery setup
- Token expiration task
- Health score calculation task
- Quota adjustment task

### Week 11-12: Polish & Deploy
- Testing (unit + integration)
- Documentation
- Performance optimization
- Production deployment

---

## Key Success Metrics

**Technical Metrics**:
- API response time < 200ms (p95)
- Tree query performance < 500ms for 10k node subtrees
- Zero data loss in audit logs
- 99.9% uptime

**Business Metrics**:
- Time to detect bot networks (should decrease over time)
- False positive rate in pruning (should be < 1%)
- User retention in healthy branches (> 80%)
- Core member invite quality (track by subtree health)

---

## Critical Considerations

1. **Soft Delete is Essential**: Never hard delete users or you break tree integrity
2. **Audit Everything**: When in doubt, log it. Future forensics will thank you.
3. **Performance at Scale**: Test recursive queries with large datasets early
4. **Admin Tools First**: You need good visibility before you can make good decisions
5. **Conservative Pruning**: Better to under-prune than over-prune initially
6. **Clear Escalation**: Define thresholds for auto-flag → manual review → prune

---

## Final Notes

This system is designed to be **forensics-first**: you're building the infrastructure to retroactively identify and surgically remove malicious networks. The beauty of the invite tree is that it gives you the data structure to trace problems back to their source, even if you don't know what you're looking for yet.

The key is to:
- **Capture everything** (forensic data, relationships, timestamps)
- **Store immutably** (audit logs are append-only)
- **Query efficiently** (optimize those recursive CTEs)
- **Act surgically** (prune with precision, not broad strokes)

Start simple, let patterns emerge from the data, then build detection tools based on what you actually find in the wild.

---

## Appendix A: Example API Flows

### A.1 User Registration Flow

```
1. User visits registration page
2. Frontend: GET /api/invites/validate/{token}
   Response: {
     "valid": true,
     "created_by": "alice",
     "expires_at": "2025-11-25T12:00:00Z"
   }

3. User fills registration form
4. Frontend: POST /api/auth/register
   Request: {
     "email": "bob@example.com",
     "username": "bob",
     "password": "securepassword",
     "invite_token": "abc123...",
     "fingerprint": "device_fingerprint_hash"
   }
   Response: {
     "success": true,
     "data": {
       "user_id": "uuid",
       "access_token": "jwt...",
       "refresh_token": "jwt..."
     }
   }

5. Backend:
   - Validates invite token
   - Hashes password
   - Creates user with invited_by_user_id set
   - Marks token as used
   - Logs to audit_log
   - Returns JWT tokens
```

### A.2 Invite Creation Flow

```
1. User (alice) wants to invite friends
2. Frontend: GET /api/users/me
   Response: {
     "invite_quota": 10,
     "invites_used": 5,
     "invites_available": 5
   }

3. Frontend: POST /api/invites/create
   Request: {
     "count": 3,
     "note": "For my college friends"
   }
   Response: {
     "success": true,
     "data": {
       "tokens": [
         {
           "id": "uuid1",
           "token": "abc123def456...",
           "expires_at": "2025-11-25T12:00:00Z",
           "invite_url": "https://app.com/invite/abc123..."
         },
         // ... 2 more
       ]
     }
   }

4. Backend:
   - Checks user has available quota
   - Generates 3 cryptographically secure tokens
   - Sets expiry to now + 24 hours
   - Increments user.invites_used by 3
   - Logs to audit_log
   - Returns tokens
```

### A.3 Admin Prune Flow

```
1. Admin investigates suspicious user "bot_user_123"
2. Frontend: GET /api/admin/users/bot_user_123/full-tree
   Response: {
     "user": { ... },
     "descendants": [
       {"id": "uuid1", "username": "bot1", "status": "flagged", ...},
       {"id": "uuid2", "username": "bot2", "status": "flagged", ...},
       // ... 50 more
     ],
     "health_score": 12.5,
     "maturity_level": "branch"
   }

3. Admin decides to prune
4. Frontend: POST /api/admin/prune
   Request: {
     "root_user_id": "bot_user_123",
     "reason": "Coordinated bot network - identical post patterns",
     "dry_run": false
   }
   Response: {
     "success": true,
     "data": {
       "operation_id": "prune_uuid",
       "affected_count": 52,
       "status": "completed"
     }
   }

5. Backend:
   - Recursively finds all descendants (52 users)
   - Creates prune_operation record
   - Soft deletes all users (sets deleted_at, status=banned)
   - Logs each deletion to audit_log
   - Marks prune_operation as completed
   - Returns result
```

### A.4 Health Score Calculation (Background Task)

```
Daily Celery Task:

1. Fetch all active users
2. For each user:
   a. Get direct invitees
   b. Get level-2 descendants
   c. Get level-3+ descendants
   
   d. Calculate:
      - direct_active_pct = active_count / total_count
      - level2_active_pct = ...
      - level3_active_pct = ...
      
   e. Apply weights:
      score = (direct * 0.5) + (level2 * 0.3) + (level3 * 0.2)
      
   f. Apply penalties:
      penalty = (flagged * 10) + (banned * 25)
      final_score = max(0, score - penalty)
      
   g. Determine maturity level:
      if account_age >= 90d AND score >= 75 AND depth >= 3:
          maturity = "supporting_trunk"
      else:
          maturity = "branch"
   
   h. Store in user_health_scores table
   
   i. If score < 50:
      - Flag user for admin review
      - Send notification
```

---

## Appendix B: Database Query Examples

### B.1 Get Entire Subtree with Depth

```sql
WITH RECURSIVE subtree AS (
    -- Base case: start with the root user
    SELECT 
        id,
        username,
        email,
        status,
        invited_by_user_id,
        created_at,
        0 as depth,
        ARRAY[id] as path
    FROM users
    WHERE id = :root_user_id
      AND deleted_at IS NULL
    
    UNION ALL
    
    -- Recursive case: get children
    SELECT 
        u.id,
        u.username,
        u.email,
        u.status,
        u.invited_by_user_id,
        u.created_at,
        st.depth + 1,
        st.path || u.id
    FROM users u
    INNER JOIN subtree st ON u.invited_by_user_id = st.id
    WHERE u.deleted_at IS NULL
)
SELECT * FROM subtree
ORDER BY depth, created_at;
```

### B.2 Get Path to Root (Ancestors)

```sql
WITH RECURSIVE ancestors AS (
    -- Base case: start with the user
    SELECT 
        id,
        username,
        invited_by_user_id,
        0 as hops_to_root
    FROM users
    WHERE id = :user_id
    
    UNION ALL
    
    -- Recursive case: climb up
    SELECT 
        u.id,
        u.username,
        u.invited_by_user_id,
        a.hops_to_root + 1
    FROM users u
    INNER JOIN ancestors a ON a.invited_by_user_id = u.id
)
SELECT * FROM ancestors
ORDER BY hops_to_root DESC;
```

### B.3 Find Users with Low Health Scores

```sql
SELECT 
    u.id,
    u.username,
    u.email,
    u.created_at,
    hs.overall_health,
    hs.subtree_size,
    hs.subtree_flagged_count,
    hs.subtree_banned_count
FROM users u
INNER JOIN user_health_scores hs ON u.id = hs.user_id
WHERE hs.calculated_at = (
    SELECT MAX(calculated_at) 
    FROM user_health_scores 
    WHERE user_id = u.id
)
AND hs.overall_health < 50
AND u.deleted_at IS NULL
ORDER BY hs.overall_health ASC
LIMIT 100;
```

### B.4 Audit Log Query: Track Token Usage

```sql
SELECT 
    al.created_at,
    al.event_type,
    u_actor.username as actor,
    u_target.username as target,
    it.token,
    al.event_data,
    al.ip_address
FROM invite_audit_log al
LEFT JOIN users u_actor ON al.actor_user_id = u_actor.id
LEFT JOIN users u_target ON al.target_user_id = u_target.id
LEFT JOIN invite_tokens it ON al.invite_token_id = it.id
WHERE al.event_type IN ('token_created', 'token_used', 'token_expired', 'token_revoked')
ORDER BY al.created_at DESC
LIMIT 100;
```

### B.5 Find Suspicious Clusters

```sql
-- Find groups of users created around the same time from same IP
SELECT 
    registration_ip,
    DATE_TRUNC('hour', created_at) as creation_hour,
    COUNT(*) as user_count,
    ARRAY_AGG(username) as usernames
FROM users
WHERE created_at > NOW() - INTERVAL '7 days'
  AND deleted_at IS NULL
GROUP BY registration_ip, DATE_TRUNC('hour', created_at)
HAVING COUNT(*) > 10  -- More than 10 accounts from same IP in same hour
ORDER BY user_count DESC;
```

---

## Appendix C: FastAPI Code Examples

### C.1 Authentication Dependency

```python
# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.security import verify_token
from app.models.user import User
from app.database import get_db

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
) -> User:
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

### C.2 Invite Creation Endpoint

```python
# app/api/invites.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.invite import InviteCreateRequest, InviteCreateResponse
from app.services.invite_service import InviteService
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/invites", tags=["invites"])

@router.post("/create", response_model=InviteCreateResponse)
async def create_invites(
    request: InviteCreateRequest,
    current_user: User = Depends(get_current_user),
    invite_service: InviteService = Depends()
):
    """
    Generate new invite tokens for the current user.
    
    - Checks available quota
    - Generates cryptographically secure tokens
    - Sets 24-hour expiration
    - Logs to audit trail
    """
    
    # Check if user has enough quota
    available = current_user.invite_quota - current_user.invites_used
    if available < request.count:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient invite quota. Available: {available}, Requested: {request.count}"
        )
    
    # Generate tokens
    tokens = await invite_service.create_tokens(
        user_id=current_user.id,
        count=request.count,
        note=request.note
    )
    
    return InviteCreateResponse(tokens=tokens)
```

### C.3 User Registration Endpoint

```python
# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.auth import RegisterRequest, AuthResponse
from app.services.auth_service import AuthService
from app.services.invite_service import InviteService

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    http_request: Request,
    auth_service: AuthService = Depends(),
    invite_service: InviteService = Depends()
):
    """
    Register a new user with an invite token.
    
    - Validates invite token
    - Creates user account
    - Establishes invite relationship
    - Returns JWT tokens
    """
    
    # Validate invite token
    token = await invite_service.validate_token(request.invite_token)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired invite token")
    
    # Capture forensic data
    client_ip = http_request.client.host
    user_agent = http_request.headers.get("user-agent")
    
    # Create user
    user = await auth_service.register_user(
        email=request.email,
        username=request.username,
        password=request.password,
        invited_by_token=token,
        registration_ip=client_ip,
        registration_user_agent=user_agent,
        registration_fingerprint=request.fingerprint
    )
    
    # Generate tokens
    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)
    
    return AuthResponse(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token
    )
```

### C.4 Tree Query Endpoint

```python
# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserTreeResponse
from app.services.tree_service import TreeService
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/{user_id}/tree", response_model=UserTreeResponse)
async def get_user_tree(
    user_id: str,
    current_user: User = Depends(get_current_user),
    tree_service: TreeService = Depends()
):
    """
    Get the invite tree for a user (their descendants).
    
    - Returns subtree structure
    - Includes health scores
    - Paginated for large trees
    """
    
    # Privacy check: users can only view their own tree (unless admin)
    if str(current_user.id) != user_id and current_user.role not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Can only view your own tree")
    
    # Get tree data
    tree_data = await tree_service.get_subtree(
        root_user_id=user_id,
        max_depth=5,  # Limit depth for performance
        include_health=True
    )
    
    return UserTreeResponse(
        root_user_id=user_id,
        tree=tree_data
    )
```

### C.5 Prune Operation Endpoint

```python
# app/api/admin.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.admin import PruneRequest, PruneResponse
from app.services.prune_service import PruneService
from app.core.dependencies import require_admin
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/prune", response_model=PruneResponse)
async def prune_branch(
    request: PruneRequest,
    current_admin: User = Depends(require_admin),
    prune_service: PruneService = Depends()
):
    """
    Prune a branch (soft delete all descendants).
    
    - Requires admin role
    - Supports dry-run mode
    - Creates immutable audit trail
    """
    
    # Get preview of affected users
    affected_users = await prune_service.get_affected_users(request.root_user_id)
    
    if request.dry_run:
        return PruneResponse(
            dry_run=True,
            affected_count=len(affected_users),
            affected_users=affected_users
        )
    
    # Execute prune
    operation = await prune_service.execute_prune(
        root_user_id=request.root_user_id,
        reason=request.reason,
        executed_by=current_admin.id
    )
    
    return PruneResponse(
        dry_run=False,
        operation_id=operation.id,
        affected_count=operation.affected_user_count,
        status=operation.status
    )
```

---

## Appendix D: Pydantic Schemas

### D.1 Auth Schemas

```python
# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    invite_token: str
    fingerprint: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str
```

### D.2 Invite Schemas

```python
# app/schemas/invite.py
from pydantic import BaseModel, Field
from datetime import datetime

class InviteCreateRequest(BaseModel):
    count: int = Field(..., ge=1, le=10)
    note: str | None = None

class InviteToken(BaseModel):
    id: str
    token: str
    expires_at: datetime
    invite_url: str

class InviteCreateResponse(BaseModel):
    tokens: list[InviteToken]

class InviteValidateResponse(BaseModel):
    valid: bool
    created_by: str | None = None
    expires_at: datetime | None = None
    reason: str | None = None  # If invalid, why?
```

### D.3 User Tree Schemas

```python
# app/schemas/user.py
from pydantic import BaseModel
from datetime import datetime

class TreeNode(BaseModel):
    id: str
    username: str
    status: str
    created_at: datetime
    depth: int
    health_score: float | None = None
    children: list['TreeNode'] = []

class UserTreeResponse(BaseModel):
    root_user_id: str
    tree: TreeNode
    total_descendants: int

# Enable forward reference
TreeNode.model_rebuild()
```

### D.4 Admin Schemas

```python
# app/schemas/admin.py
from pydantic import BaseModel

class PruneRequest(BaseModel):
    root_user_id: str
    reason: str
    dry_run: bool = False

class PruneResponse(BaseModel):
    dry_run: bool
    operation_id: str | None = None
    affected_count: int
    affected_users: list[dict] | None = None
    status: str | None = None

class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    flagged_users: int
    banned_users: int
    total_invites_issued: int
    avg_health_score: float
```

---

## Appendix E: Environment Setup

### E.1 requirements.txt

```txt
# FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Task Queue
celery==5.3.4
redis==5.0.1

# Utilities
pydantic[email]==2.5.0
pydantic-settings==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Monitoring (optional)
sentry-sdk==1.38.0
```

### E.2 .env.example

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/invite_tree_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Admin
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=changeme

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# App
APP_NAME=InviteTreeAPI
APP_VERSION=1.0.0
DEBUG=True

# Sentry (optional)
SENTRY_DSN=
```

### E.3 Docker Compose (Development)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: invitetree
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: invite_tree_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    env_file:
      - .env

  celery:
    build: .
    command: celery -A app.tasks worker --loglevel=info
    volumes:
      - ./backend:/app
    depends_on:
      - redis
      - postgres
    env_file:
      - .env

  celery-beat:
    build: .
    command: celery -A app.tasks beat --loglevel=info
    volumes:
      - ./backend:/app
    depends_on:
      - redis
      - postgres
    env_file:
      - .env

volumes:
  postgres_data:
```

---

## Appendix F: Performance Optimization Tips

### F.1 Database Indexing

Critical indexes for performance:
```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_invited_by ON users(invited_by_user_id);

-- Tree traversal (most important!)
CREATE INDEX idx_users_parent_status ON users(invited_by_user_id, status) WHERE deleted_at IS NULL;

-- Token lookups
CREATE INDEX idx_tokens_token ON invite_tokens(token) WHERE is_used = FALSE;

-- Audit log queries
CREATE INDEX idx_audit_created ON invite_audit_log(created_at DESC);
CREATE INDEX idx_audit_user_events ON invite_audit_log(target_user_id, event_type);
```

### F.2 Query Optimization

For deep trees, consider materialized path or closure table:

**Materialized Path** (store ancestor IDs as array):
```sql
ALTER TABLE users ADD COLUMN ancestor_path UUID[];

-- Update path on insert
CREATE OR REPLACE FUNCTION update_ancestor_path()
RETURNS TRIGGER AS $
BEGIN
    IF NEW.invited_by_user_id IS NULL THEN
        NEW.ancestor_path = ARRAY[NEW.id];
    ELSE
        SELECT ancestor_path || NEW.id INTO NEW.ancestor_path
        FROM users
        WHERE id = NEW.invited_by_user_id;
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER set_ancestor_path
BEFORE INSERT ON users
FOR EACH ROW EXECUTE FUNCTION update_ancestor_path();

-- Now queries are fast
SELECT * FROM users WHERE NEW.id = ANY(ancestor_path);  -- All descendants
SELECT * FROM users WHERE id = ANY(:user_ancestor_path);  -- All ancestors
```

### F.3 Caching Strategy

Use Redis for:
- User session data (JWT blacklist)
- Rate limiting counters
- Frequently accessed health scores
- Tree structure cache (invalidate on changes)

```python
# Example: Cache health scores
import redis
import json

async def get_health_score(user_id: str) -> float:
    cache_key = f"health:{user_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Calculate from DB
    score = calculate_health_score(user_id)
    
    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, json.dumps(score))
    
    return score
```

### F.4 Pagination for Large Results

```python
# Always paginate admin queries
@router.get("/admin/users")
async def list_users(
    page: int = 1,
    page_size: int = 50,
    status: str | None = None
):
    offset = (page - 1) * page_size
    
    query = db.query(User)
    if status:
        query = query.filter(User.status == status)
    
    total = query.count()
    users = query.offset(offset).limit(page_size).all()
    
    return {
        "data": users,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size
        }
    }
```

---

## Final Checklist

Before deploying to production:

**Security**:
- [ ] Change all default passwords/secrets
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Review database permissions
- [ ] Enable SQL query logging (temporarily) to catch N+1 queries

**Performance**:
- [ ] All critical indexes created
- [ ] Tested recursive queries with 10k+ node trees
- [ ] Load testing completed
- [ ] Redis caching configured
- [ ] Connection pooling tuned

**Monitoring**:
- [ ] Error tracking (Sentry) configured
- [ ] Application metrics (Prometheus) set up
- [ ] Database slow query log enabled
- [ ] Audit log rotation policy defined

**Data Integrity**:
- [ ] Database backups automated
- [ ] Soft delete working correctly
- [ ] Audit logs immutable
- [ ] No way to orphan users (foreign key constraints)

**Documentation**:
- [ ] API documentation (Swagger) accessible
- [ ] Admin playbook for common operations
- [ ] Runbook for incident response
- [ ] Architecture diagram created

---

This roadmap gives you everything needed to build a production-ready invite tree system from the ground up. Start with Phase 1-2 (data models + core API), validate with real usage, then expand to admin tools and automation.

The system is designed to scale, providing you with the forensic infrastructure to retroactively hunt down malicious networks whenever you discover them - even months after they've infiltrated.