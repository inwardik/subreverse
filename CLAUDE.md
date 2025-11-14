# CLAUDE.md - AI Assistant Navigation Guide

## Project Overview

**SubReverse** is a bilingual (English-Russian) subtitle search engine that allows users to discover interesting phrases, idioms, and quotes from movies and TV shows. The application follows **Onion Architecture** (Clean Architecture) principles with clear separation of concerns.

### Quick Facts
- **Backend**: FastAPI with async Python
- **Frontend**: React 18 + Vite (single-file SPA)
- **Databases**: MongoDB (primary storage), Elasticsearch (full-text search)
- **Architecture**: Onion/Layered architecture with dependency inversion
- **Authentication**: JWT-based with energy/leveling system

---

## Directory Structure

```
/home/user/subreverse/
├── backend/src/
│   ├── domain/              # CORE LAYER (no dependencies)
│   │   ├── entities.py      # Business entities (SubtitlePair, User, etc.)
│   │   └── interfaces.py    # Abstract interfaces (repositories, handlers)
│   ├── application/         # USE CASES LAYER
│   │   ├── subtitle_service.py  # Main business logic
│   │   ├── auth_service.py      # Authentication logic
│   │   └── dto.py              # Data Transfer Objects (Pydantic)
│   ├── infrastructure/      # EXTERNAL DEPENDENCIES LAYER
│   │   ├── database/
│   │   │   ├── mongodb.py              # DB connection + User repo
│   │   │   └── subtitle_mongo_repo.py  # Subtitle/Idiom/Quote repos
│   │   ├── elasticsearch_engine.py     # Search engine implementation
│   │   ├── security/
│   │   │   ├── password.py    # SHA256 password hashing
│   │   │   └── jwt_handler.py # Manual JWT implementation
│   │   ├── srt_parser.py      # SRT subtitle parser
│   │   └── config.py          # Application settings
│   └── api/                 # HTTP LAYER (outermost)
│       ├── main.py          # FastAPI app setup
│       ├── subtitle_routes.py   # Subtitle endpoints
│       ├── upload_routes.py     # File upload endpoints
│       ├── auth_routes.py       # Authentication endpoints
│       ├── self_routes.py       # User self-service endpoints
│       └── dependencies.py      # Dependency injection container
├── frontend/src/
│   ├── App.jsx             # Single-file SPA (954 lines)
│   └── main.jsx            # Entry point
├── docker-compose.yml      # Full stack orchestration
└── nginx.conf             # Reverse proxy configuration
```

---

## Architecture Layers (Onion Pattern)

### Layer 1: Domain (Core) - `/backend/src/domain/`

**Purpose**: Pure business logic with zero external dependencies

**Key Files**:
- **`entities.py`**: Core business entities
  - `SubtitlePair` (en, ru, file, time, rating, category, seq_id)
  - `User` (id, username, email, energy, level, xp, role)
  - `Idiom`, `Quote`, `SystemStats`

- **`interfaces.py`**: Abstract interfaces (dependency inversion)
  - `ISubtitlePairRepository`, `ISearchEngine`
  - `IUserRepository`, `IPasswordHandler`, `IJWTHandler`
  - All other layers depend on these interfaces

**When to edit**: Adding new business entities or repository contracts

---

### Layer 2: Application - `/backend/src/application/`

**Purpose**: Orchestrate business logic and use cases

**Key Files**:
- **`subtitle_service.py`** (310 lines): Main business logic
  - `get_random_pair()` - Random pair with 3-attempt fallback strategy
  - `update_pair()` - Rating/category updates with energy consumption
  - `search()` - Elasticsearch integration with MongoDB fallback
  - `get_pair_with_offset()` - Temporal navigation (prev/next subtitles)
  - Energy/XP/leveling system
  - Automatic idiom/quote mirroring

- **`auth_service.py`** (88 lines): Authentication logic
  - `signup()` - User registration with validation
  - `login()` - JWT token generation
  - `get_current_user()` - Token verification

- **`dto.py`**: Pydantic models for API serialization

**When to edit**: Implementing new features or business rules

---

### Layer 3: Infrastructure - `/backend/src/infrastructure/`

**Purpose**: Implement domain interfaces using external systems

**Key Files**:
- **`database/subtitle_mongo_repo.py`** (400+ lines):
  - `MongoDBSubtitlePairRepository` - seq_id-based random selection
  - `MongoDBIdiomRepository`, `MongoDBQuoteRepository`
  - `MongoDBStatsRepository`

- **`database/mongodb.py`** (160 lines):
  - `MongoDBConnection` - Async connection manager
  - `MongoDBUserRepository` - User CRUD with atomic energy updates

- **`elasticsearch_engine.py`** (215 lines):
  - NGram analyzer for exact substring matching
  - Standard analyzer for fuzzy word matching
  - Bulk indexing with batching

- **`security/password.py`**: SHA256 + salt hashing
- **`security/jwt_handler.py`**: Manual HS256 JWT (no external library)
- **`srt_parser.py`** (91 lines): Parse SRT subtitle files

**When to edit**: Changing database queries, search algorithms, or adding new data sources

---

### Layer 4: API - `/backend/src/api/`

**Purpose**: HTTP endpoints and dependency injection

**Key Files**:
- **`main.py`**: FastAPI app setup, CORS, static file serving
- **`subtitle_routes.py`** (165 lines): Main API endpoints
  - `GET /api/get_random` - Random pair
  - `GET /api/search/{id}/` - Get by ID with offset (temporal navigation)
  - `PATCH /api/search/{id}/` - Update pair (requires auth + energy)
  - `GET /api/search?q={query}` - Text search
  - `GET /api/idioms`, `GET /api/quotes` - Collections
  - `POST /api/index_elastic_search` - Reindex all

- **`upload_routes.py`** (190 lines): File management
  - `POST /api/upload_zip` - Upload ZIP with _en.srt/_ru.srt pairs
  - `POST /api/import_ndjson`, `POST /api/export` - Bulk data

- **`auth_routes.py`** (35 lines): Authentication
  - `POST /auth/signup`, `POST /auth/login`

- **`dependencies.py`** (90 lines): Dependency injection container
  - Global connection management
  - Repository/service factories
  - `get_current_user` middleware

**When to edit**: Adding new endpoints or modifying API contracts

---

## Frontend Architecture - `/frontend/src/App.jsx`

**Single-file SPA** (954 lines) with hash-based routing

**Components**:
1. **`AuthWidget`** - Login/signup forms, user profile with energy/XP bars
2. **`Card`** - Subtitle pair display with temporal navigation (←/→), rating controls, category toggles
3. **`HomePage`** - Search interface with tabs (Search/Idioms/Quotes/Leaderboard)
4. **`IdiomsView`** - Idiom list display
5. **`AdminPage`** - File upload, duplicate removal, indexing, export
6. **`ContentPage`** - File listing

**Key Features**:
- Hash-based routing: `#/`, `#/search`, `#/idioms`, `#/admin`
- Global auth state with custom `auth-changed` events
- LocalStorage-based JWT storage
- Real-time energy updates

**When to edit**: Adding new UI features or pages

---

## Key Systems & Features

### Energy System
- Users start with 10 energy, recharges at midnight UTC
- Each action (rating/category change) costs 1 energy
- Max energy increases by 5 per level

### Leveling System
- Level N requires N * 10 XP to level up
- Each action grants 1 XP
- Level up resets XP to 0

### Temporal Navigation
- Arrows (←/→) load previous/next subtitle from same file
- Fast path: Use seq_id for O(1) lookup
- Slow path: Fetch all from file, sort by time

### Search Features
- Standard search: Word-based matching (operator: "and")
- Quoted search: Exact phrase matching using ngram analyzer
- Rating-based boosting (factor: 0.2)
- Fallback to MongoDB regex if Elasticsearch unavailable

### Random Selection Strategy
1. Try seq_id approach (5 attempts) - O(1) lookup
2. Fallback to skip random offset (3 attempts)
3. Final fallback to MongoDB `$sample` aggregation

---

## Common Tasks

### Adding a New API Endpoint
1. Define request/response DTOs in `application/dto.py`
2. Implement business logic in appropriate service (`application/subtitle_service.py`)
3. Add route handler in `api/subtitle_routes.py` (or new routes file)
4. Register router in `api/main.py` if creating new routes file

### Adding a New Repository Method
1. Add method signature to interface in `domain/interfaces.py`
2. Implement in `infrastructure/database/subtitle_mongo_repo.py`
3. Use in service layer (`application/subtitle_service.py`)

### Adding a New Frontend Feature
1. Add component function to `frontend/src/App.jsx`
2. Add route handler in `Router` component
3. Add navigation link in `HomePage` or navbar

### Modifying Search Behavior
1. Update Elasticsearch query in `infrastructure/elasticsearch_engine.py`
2. Test with `GET /api/search?q=test` endpoint

### Adding Database Indexes
1. Update `MongoDBConnection.create_indexes()` in `infrastructure/database/mongodb.py`
2. Indexes are created on startup

---

## Important Implementation Details

### Authentication Flow
1. User signs up → password hashed with salt → stored in MongoDB
2. User logs in → password verified → JWT generated (7-day expiry)
3. Protected endpoints → JWT decoded → user loaded from DB
4. Frontend stores JWT in localStorage → sends in `Authorization: Bearer <token>`

### Data Flow Example (Update Rating)
```
Frontend Card component
    ↓ PATCH /api/search/{id}/?delta=1
API Layer (subtitle_routes.py)
    ↓ get_current_user dependency
    ↓ get_subtitle_service dependency
Application Layer (subtitle_service.py)
    ↓ Check energy > 0
    ↓ user_repo.update_energy(-1)
    ↓ pair_repo.update_rating(delta)
    ↓ Handle XP gain + level up
Infrastructure Layer (subtitle_mongo_repo.py)
    ↓ MongoDB atomic update
Domain Layer (entities.py)
    ↓ Return SubtitlePair entity
Application Layer
    ↓ Convert to SubtitlePairResponseDTO
API Layer
    ↓ Return JSON
Frontend
    ↓ Update UI + refresh user energy
```

### Duplicate Removal Algorithm
- Groups by `(en, ru)` pair
- Uses MongoDB aggregation with `$group` and `$first`
- Keeps one document per unique pair, deletes rest

### Elasticsearch NGram Configuration
- Edge ngram filter: 3-20 characters
- Enables substring matching for quoted queries
- Example: `"the cat"` matches exact phrase anywhere in text

---

## Configuration

### Environment Variables (`.env.example`)
```bash
DATABASE_TYPE=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=subtitles
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=pairs
JWT_SECRET=change_me_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_SECONDS=604800  # 7 days
```

### Docker Services (docker-compose.yml)
- **mongo**: Port 27017
- **elasticsearch**: Port 9200 (security disabled for dev)
- **backend**: Port 8000
- **frontend**: Port 5173 (Vite dev server)
- **nginx**: Ports 80/443 (HTTPS configured)

---

## Testing & Development

### Running Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Frontend
```bash
cd frontend
npm install
npm run dev
```

### Running Full Stack
```bash
docker-compose up
```

### Reindexing Elasticsearch
```bash
POST /api/index_elastic_search
# or
curl -X POST http://localhost:8000/api/index_elastic_search
```

---

## Database Schema

### `subtitle_pairs` Collection
```json
{
  "_id": ObjectId("..."),
  "en": "Hello, world!",
  "ru": "Привет, мир!",
  "file_en": "movie_en.srt",
  "file_ru": "movie_ru.srt",
  "time_en": "00:01:23,456 --> 00:01:26,789",
  "time_ru": "00:01:23,500 --> 00:01:26,800",
  "rating": 5,
  "category": "idiom",  // or "quote", "wrong", null
  "seq_id": 12345
}
```

### `users` Collection
```json
{
  "_id": "uuid-string",
  "username": "john_doe",
  "email": "john@example.com",
  "password_hash": "sha256-hash",
  "salt": "random-hex-string",
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "energy": 10,
  "max_energy": 10,
  "level": 1,
  "xp": 5,
  "role": "user",
  "last_recharge": ISODate("2024-01-01T00:00:00Z")
}
```

### `idioms` Collection
```json
{
  "_id": ObjectId("..."),
  "en": "Break a leg!",
  "ru": "Ни пуха, ни пера!",
  "pair_seq_id": 12345,
  "rating": 8,
  "filename": "movie_en.srt",
  "time": "00:01:23,456 --> 00:01:26,789",
  "owner_username": "john_doe"
}
```

### `quotes` Collection
Same schema as `idioms`

### `system_stats` Collection
```json
{
  "_id": ObjectId("..."),
  "total_pairs": 10000,
  "total_idioms": 150,
  "total_quotes": 80,
  "files": ["movie1_en.srt", "movie2_en.srt", ...]
}
```

---

## API Endpoints Quick Reference

### Public Endpoints
- `GET /health` - Health check
- `GET /api/get_random` - Random subtitle pair
- `GET /api/search?q={query}` - Search pairs
- `GET /api/search/{id}/?offset_en={n}&offset_ru={m}` - Get by ID with temporal offset
- `GET /api/stats` - System statistics
- `GET /api/idioms?limit=50` - Recent idioms
- `GET /api/quotes?limit=50` - Recent quotes

### Authenticated Endpoints
- `PATCH /api/search/{id}/?delta={n}&category={cat}` - Update pair (costs 1 energy)
- `GET /auth/me` - Current user info
- `GET /self` - User info with energy recharge

### Admin Endpoints
- `POST /api/upload_zip` - Upload subtitle ZIP
- `POST /api/import_ndjson` - Import data
- `POST /api/export` - Export all data as NDJSON
- `POST /api/clear` - Remove duplicates
- `POST /api/delete_all` - Delete all pairs
- `POST /api/index_elastic_search` - Reindex Elasticsearch
- `POST /api/stats` - Compute statistics

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - Login (returns JWT)

---

## Troubleshooting

### Elasticsearch Not Working
- Check if ES is running: `curl http://localhost:9200`
- System falls back to MongoDB regex search if ES unavailable
- Reindex: `POST /api/index_elastic_search`

### Energy Not Recharging
- Energy recharges at midnight UTC
- Check `user.last_recharge` field
- Call `GET /self` endpoint to trigger recharge check

### Random Pairs Repeating
- System tries seq_id approach first (fast but may repeat)
- Falls back to MongoDB `$sample` for true randomness
- Ensure seq_id index exists for best performance

### Temporal Navigation Not Working
- Requires matching `file_en` values
- Works best with seq_id field populated
- Falls back to time-based sorting (slower)

---

## Future Improvements (TODOs)

Based on codebase analysis:
- [ ] Add comprehensive test suite
- [ ] Implement leaderboard functionality
- [ ] Complete quotes page UI
- [ ] Add structured logging (replace print statements)
- [ ] Add health check for database connections
- [ ] PostgreSQL support (code exists but untested)
- [ ] Request-level rate limiting (currently only energy-based)
- [ ] Admin user management UI
- [ ] Batch operations for better performance
- [ ] Search query suggestions/autocomplete

---

## Quick Reference for AI Assistants

**When asked to add a feature**:
1. Identify which layer(s) need changes (Domain → Application → Infrastructure → API)
2. Start from inner layers and work outward
3. Update interfaces before implementations
4. Add DTOs for new data structures
5. Update frontend last

**When debugging**:
1. Check logs in terminal (uvicorn output)
2. Verify MongoDB queries in mongo shell
3. Test Elasticsearch queries: `GET http://localhost:9200/pairs/_search`
4. Check frontend console for errors
5. Verify JWT token in browser DevTools → Application → LocalStorage

**Code style**:
- Use async/await consistently
- Type hints for all functions
- Pydantic models for validation
- Dependency injection via FastAPI dependencies
- Error handling with try/except in services

---

This document should help you navigate and modify the SubReverse codebase effectively. Refer to specific files mentioned for implementation details.
