# SubReverse 🎬

**Discover and learn language through movie and TV show subtitles**

SubReverse is a bilingual (English-Russian) subtitle search engine that helps language learners discover interesting phrases, idioms, and quotes from authentic media content. Search through thousands of subtitle pairs, save your favorites, and track your learning progress with an engaging leveling system.

## ✨ Features

### 🔍 Powerful Search
- **Full-text search** with Elasticsearch-powered fuzzy matching
- **Exact phrase search** using quotes (e.g., `"break a leg"`)
- **Random exploration** to discover new content
- **Temporal navigation** to browse previous/next subtitles from the same scene

### 📚 Learning Tools
- **Idiom collection** - Save interesting idioms with context
- **Quote collection** - Bookmark memorable quotes
- **Rating system** - Upvote/downvote pairs to improve search results
- **Category tagging** - Mark pairs as idioms, quotes, or incorrect translations

### 🎮 Gamification
- **Energy system** - Earn energy to interact with content (recharges daily)
- **Experience points (XP)** - Gain XP from every action
- **Leveling system** - Level up to increase your max energy
- **User profiles** - Track your progress and contributions

### 📂 Content Management
- **ZIP upload** - Import subtitle pairs from ZIP files (format: `*_en.srt`, `*_ru.srt`)
- **NDJSON import/export** - Bulk data operations
- **Duplicate removal** - Automatic cleanup of redundant pairs
- **Statistics tracking** - Monitor total pairs, files, and collections

## 🏗️ Architecture

SubReverse is built with modern technologies and clean architecture principles:

- **Backend**: FastAPI (Python) with Onion/Clean Architecture
- **Frontend**: React 18 + Vite SPA
- **Database**: MongoDB for data storage
- **Search Engine**: Elasticsearch for full-text search
- **Deployment**: Docker Compose with Nginx reverse proxy

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/subreverse.git
   cd subreverse
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set your JWT_SECRET and other configurations
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: https://localhost (or http://localhost:80)
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### First Steps

1. **Create an account** - Click the user icon and sign up
2. **Import subtitles** - Go to Admin page and upload ZIP files with subtitle pairs
3. **Index search** - Click "Index Elasticsearch" to enable full-text search
4. **Start exploring** - Search for phrases or get random pairs!

## 📖 Usage

### Searching

**Standard search** (word-based):
```
hello world
```
Finds pairs containing both "hello" and "world" (in any order)

**Exact phrase search** (with quotes):
```
"hello world"
```
Finds pairs containing the exact phrase "hello world"

### Interacting with Pairs

Each subtitle pair shows:
- **English and Russian text**
- **Source file and timestamp**
- **Rating** (upvote ↑ / downvote ↓)
- **Category tags** (idiom / quote / wrong translation)
- **Navigation arrows** (← →) to browse adjacent subtitles

**Note**: Each action (rating, tagging) costs 1 energy point. Energy recharges to maximum at midnight UTC.

### Building Collections

- Click **"idiom"** to add interesting idioms to your collection
- Click **"quote"** to save memorable quotes
- View your collections in the Idioms and Quotes tabs

### Admin Features

Access the Admin page to:
- Upload subtitle files (ZIP format)
- Import/export data (NDJSON format)
- Remove duplicate pairs
- Reindex Elasticsearch
- View statistics

## 📁 Subtitle File Format

SubReverse expects subtitle pairs in SRT format:

```
movie_name_en.srt  (English subtitles)
movie_name_ru.srt  (Russian subtitles)
```

### ZIP Upload Format

Create a ZIP file containing matching pairs:
```
archive.zip
├── movie1_en.srt
├── movie1_ru.srt
├── movie2_en.srt
└── movie2_ru.srt
```

The system automatically matches files by name (excluding `_en`/`_ru` suffix).

### SRT File Example

```srt
1
00:00:10,500 --> 00:00:13,000
Hello, world!

2
00:00:15,000 --> 00:00:18,000
How are you?
```

## 🔧 Development

### Running Locally (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Dependencies:**
- MongoDB running on `localhost:27017`
- Elasticsearch running on `localhost:9200`

### Project Structure

```
subreverse/
├── backend/              # FastAPI application
│   ├── src/
│   │   ├── domain/      # Business entities and interfaces
│   │   ├── application/ # Business logic and services
│   │   ├── infrastructure/ # Database, search, security
│   │   └── api/         # HTTP endpoints
│   └── requirements.txt
├── frontend/            # React SPA
│   ├── src/
│   │   └── App.jsx     # Main application
│   └── package.json
├── docker-compose.yml   # Service orchestration
└── nginx.conf          # Reverse proxy configuration
```

## 🎯 API Endpoints

### Public Endpoints

- `GET /api/get_random` - Get a random subtitle pair
- `GET /api/search?q={query}` - Search for pairs
- `GET /api/search/{id}/` - Get specific pair with offset navigation
- `GET /api/idioms` - Get recent idioms
- `GET /api/quotes` - Get recent quotes
- `GET /api/stats` - Get system statistics

### Authenticated Endpoints

- `PATCH /api/search/{id}/` - Update pair rating/category (costs 1 energy)
- `GET /auth/me` - Get current user info
- `GET /self` - Get user info with energy recharge

### Admin Endpoints

- `POST /api/upload_zip` - Upload subtitle ZIP
- `POST /api/import_ndjson` - Import data
- `POST /api/export` - Export all data
- `POST /api/index_elastic_search` - Reindex search engine
- `POST /api/clear` - Remove duplicates
- `POST /api/delete_all` - Delete all pairs

### Authentication

- `POST /auth/signup` - Create new account
- `POST /auth/login` - Login and receive JWT token

Full API documentation available at: http://localhost:8000/docs (Swagger UI)

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_TYPE=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=subtitles

# Search Engine
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=pairs

# Authentication
JWT_SECRET=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_SECONDS=604800  # 7 days
```

### Docker Compose Services

- **mongo**: MongoDB 4.4.18 on port 27017
- **elasticsearch**: Elasticsearch 8.14.3 on port 9200
- **backend**: FastAPI on port 8000
- **frontend**: Vite dev server on port 5173
- **nginx**: Reverse proxy on ports 80/443

## 🎮 Game Mechanics

### Energy System

- **Starting energy**: 10 points
- **Energy cost**: 1 point per action (rating, tagging)
- **Recharge**: Full recharge at midnight UTC
- **Max energy**: Increases by 5 per level

### Leveling System

- **Starting level**: 1
- **XP per action**: 1 point
- **Level up requirement**: Level N requires N × 10 XP
- **Benefits**: Higher max energy, sense of progression

### User Roles

- **user**: Standard user with energy limitations
- **admin**: Full access to admin endpoints (future feature)

## 🔐 Security

- **Password hashing**: SHA256 with random salt
- **Authentication**: JWT tokens with HS256 signing
- **Token expiry**: 7 days (configurable)
- **CORS**: Configured for development (adjust for production)

**⚠️ Important for Production**:
- Change `JWT_SECRET` to a strong random value
- Enable Elasticsearch security
- Configure CORS to allow only your domain
- Use HTTPS (nginx.conf includes SSL configuration)
- Set strong MongoDB credentials

## 🐛 Troubleshooting

### Elasticsearch not working
**Problem**: Search returns no results

**Solution**:
1. Check if Elasticsearch is running: `curl http://localhost:9200`
2. Reindex data: `POST /api/index_elastic_search`
3. The system falls back to MongoDB regex search if ES is unavailable

### Energy not recharging
**Problem**: Energy stays at 0

**Solution**:
- Energy recharges at midnight UTC
- Trigger recharge manually by calling `GET /self` endpoint
- Check server time is correct

### Cannot upload ZIP files
**Problem**: ZIP upload fails

**Solution**:
- Ensure ZIP contains matching pairs: `name_en.srt` + `name_ru.srt`
- Check file encoding is UTF-8
- Verify SRT format is correct (use VLC to test subtitles)

### Random pairs repeating
**Problem**: Same pairs appear frequently

**Solution**:
- This is expected with small datasets
- Import more subtitle files for better variety
- The system uses weighted random selection

## 📊 Statistics

View system statistics at `GET /api/stats`:
- Total subtitle pairs
- Total idioms saved
- Total quotes saved
- List of imported files

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Add more language pairs (French-English, Spanish-English, etc.)
- [ ] Implement leaderboard functionality
- [ ] Add export to Anki flashcards
- [ ] Improve search relevance algorithm
- [ ] Add spaced repetition system
- [ ] Mobile app (React Native)
- [ ] User profiles and social features
- [ ] Advanced filters (by rating, category, source file)

## 📝 License

This project is open source. Please check the LICENSE file for details.

## 🙏 Acknowledgments

- Subtitle content belongs to respective copyright holders
- Built with FastAPI, React, MongoDB, and Elasticsearch
- Inspired by language learning through authentic media

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation in `/backend/README.md`
- Review API docs at `/docs` endpoint

---

**Happy learning! 🎓**

*SubReverse - Because the best way to learn a language is through the stories you love.*
