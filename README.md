# IMDB Content System

A REST API for ingesting and querying IMDB movie data from CSV files, backed by MongoDB.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| **Flask** | Web framework |
| **PyMongo** | MongoDB driver |
| **python-dotenv** | Load environment variables from `.env` |
| **Flasgger** | Swagger UI for API documentation |

---

## Project Structure

```
imdb-content-system/
│
├── config/
│   ├── __init__.py               # Exports AppConfig and DBConfig
│   ├── app_config.py             # Loads env vars — MONGO_URI, DB_NAME, BATCH_SIZE, DEBUG
│   ├── db_config.py              # Creates MongoClient, sets up collection indexes
│   └── logger_config.py         # Configures application-wide logging
│
├── container/
│   ├── infroContainer.py         # Connects to MongoDB, exposes db (Database object)
│   ├── RepositoryContainer.py    # Creates all repository instances, injects db
│   └── serviceContainer.py      # Creates all service instances, injects repositories
│
├── apis/
│   ├── controllers/
│   │   ├── upload_controller.py  # Parses and validates upload request, calls upload_service
│   │   └── movie_controller.py   # Parses and validates query params, calls movie_service
│   └── routes/
│       ├── __init__.py           # register_blueprints() — registers all blueprints on the app
│       ├── upload_routes.py      # Blueprint for POST /api/upload/, Swagger docs
│       └── movie_routes.py       # Blueprint for GET /api/movies/, Swagger docs
│
├── services/
│   ├── upload_service.py         # Reads CSV, parses rows, batches and upserts into MongoDB
│   └── movie_service.py          # Filters, paginates, and returns movies from MongoDB
│
├── repository/
│   ├── upload_repository.py      # Executes bulk_write upsert operations on movies collection
│   └── movie_repository.py       # Executes find and count_documents on movies collection
│
├── app.py                        # Entry point — creates Flask app, registers blueprints
├── .env                          # Local environment variables (never commit this)
├── requirements.txt              # Python dependencies
└── README.md
```

---

## Architecture — Dependency Injection & Container Pattern

The project follows a strict layered architecture. Each layer only talks to the layer directly below it. No layer creates its own dependencies — everything is injected.

```
infraContainer.py       →   creates db (MongoDB Database object)
        ↓
RepositoryContainer.py  →   creates upload_repo, movie_repo   (inject db)
        ↓
serviceContainer.py     →   creates upload_service, movie_service   (inject repos)
        ↓
controllers/            →   import services from serviceContainer, parse requests
        ↓
routes/                 →   import controllers, define blueprints and Swagger docs
        ↓
app.py                  →   calls register_blueprints(app)
```

### Why this pattern?

- **Testability** — every class accepts its dependencies via constructor, so you can inject mocks in tests without touching the implementation
- **Single responsibility** — container files are the only place that knows how to wire things together; the rest of the code doesn't care where its dependencies come from
- **Swappability** — replacing MongoDB with another database only requires updating the repository layer and `RepositoryContainer.py`, nothing else changes

---

## Setup & Installation

### 1. Install MongoDB (Mac via Homebrew)

```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

### 2. Clone and create virtual environment

```bash
cd imdb-content-system
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
MONGO_URI=mongodb://localhost:27017
DB_NAME=imdb
BATCH_SIZE=1000
DEBUG=true
```

### 5. Run the server

```bash
python app.py
```

Server starts at `http://localhost:5000`.
Swagger UI available at `http://localhost:5000/apidocs`.

---

## Environment Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `MONGO_URI` | string | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | string | `imdb` | Name of the MongoDB database to use |
| `BATCH_SIZE` | int | `1000` | Number of rows processed per bulk write during CSV upload |
| `DEBUG` | bool | `false` | Enables Flask debug mode and verbose logging |

---

## API Reference

### POST `/api/upload/`

Upload a CSV file to import movies into MongoDB.

**Request**

- Content-Type: `multipart/form-data`
- Field: `file` — a `.csv` file

**Query Parameters**

| Param | Type | Required | Default | Description |
|---|---|---|---|---|
| `mode` | string | No | `upsert` | Upload strategy — `upsert` or `insert` (see below) |

**Upload Modes**

| Mode | When to use | How it works | Speed |
|---|---|---|---|
| `upsert` (default) | Data already exists and you want to add new rows or update existing ones | Matches each row on `(original_title, release_date)`. Updates the document if it exists, inserts if it doesn't. | Slower — each row requires a read + write against the unique index |
| `insert` | First load, or adding only new records without touching existing ones | Bulk inserts rows directly. Rows that already exist (duplicate key on `original_title + release_date`) are silently skipped. No read-before-write. | Fast — recommended for large files (1 GB+) |

**Which mode should I use?**

- **First time loading data** → use `insert`. Fastest path, no upsert overhead.
- **Adding new movies only** → use `insert`. Existing records are skipped automatically via the unique index.
- **Updating existing records or correcting data** → use `upsert`. It overwrites existing documents with the latest values from the CSV.
- **CSV contains duplicate `(original_title, release_date)` rows** → use `upsert`. Duplicates within the file are handled gracefully; `insert` mode will skip the second occurrence of any duplicate.

**CSV Expected Columns**

```
budget, homepage, original_language, original_title, overview,
release_date, revenue, runtime, status, title, vote_average,
vote_count, production_company_id, genre_id, languages
```

**Response 200**

```json
{
  "message": "Upload complete",
  "result": {
    "inserted": 4803,
    "skipped": 0,
    "total_rows": 4803,
    "updated": 0
  }
}
```

**Response 400**

```json
{ "error": "No file provided" }
{ "error": "Empty filename" }
{ "error": "Only CSV files are allowed" }
{ "error": "Invalid mode. Allowed: upsert, insert" }
```

---

### GET `/api/movies/`

Fetch a paginated, filtered, and sorted list of movies.

**Query Parameters**

| Param | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | int | No | `1` | Page number |
| `page_size` | int | No | `20` | Results per page (max 100) |
| `year` | int | No | — | Filter by release year |
| `language` | string | No | — | Filter by original language code (e.g. `en`) |
| `sort_by` | string | No | `release_date` | Sort field — `release_date` or `vote_average` |
| `order` | string | No | `desc` | Sort direction — `asc` or `desc` |

**Response 200**

```json
{
  "data": [
    {
      "original_title": "Toy Story",
      "title": "Toy Story",
      "original_language": "en",
      "languages": "['English']",
      "overview": "Led by Woody...",
      "homepage": "http://toystory.disney.com/toy-story",
      "release_date": "1995-10-30",
      "release_year": 1995,
      "revenue": 373554033,
      "runtime": 81,
      "status": "Released",
      "vote_average": 7.7,
      "vote_count": 5415,
      "genre_ids": [16],
      "production_company_ids": [3]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_records": 4803,
    "total_pages": 241,
    "has_next": true,
    "has_prev": false
  }
}
```

**Response 400**

```json
{ "error": "Invalid sort_by value. Allowed: release_date, vote_average" }
```

---

## Database Design Decisions

### Primary Key — Compound Unique Index on `(original_title, release_date)`

MongoDB auto-generates an `_id` for each document, but the natural identity of a movie in this dataset is its title and release date together. A unique compound index on `(original_title, release_date)` enforces deduplication at the database level and serves as the match key for upserts.

### Two Upload Strategies — `insert` vs `upsert`

The API supports two modes controlled by the `?mode=` query parameter.

**`insert` mode** — bulk inserts every row using `InsertOne` with `ordered=False`. Rows that already exist (duplicate `(original_title, release_date)`) are silently skipped by the unique index — no document is dropped or overwritten. This is the fastest path because MongoDB never has to read an existing document before writing. Recommended for the first load or when adding only new records to a large collection.

**`upsert` mode** — matches each row on `(original_title, release_date)` using `UpdateOne` with `upsert=True` and `$set`. If a document with that key already exists it is overwritten; otherwise a new document is inserted. This is the right choice when you want to add new movies or correct existing records without affecting the rest of the collection. The trade-off is speed — every write requires a read against the unique index, and this cost compounds as the collection grows.

### Primary Key — Compound Unique Index on `(original_title, release_date)`

MongoDB auto-generates an `_id` for each document, but the natural identity of a movie in this dataset is its title and release date together. A unique compound index on `(original_title, release_date)` enforces deduplication at the database level and serves as the match key for upserts. In `insert` mode the index is recreated before data is loaded, so any duplicate rows within the CSV itself will be rejected.

### Indexes

| Index | Type | Reason |
|---|---|---|
| `(original_title, release_date)` | Unique compound | Deduplication and upsert match key |
| `release_year` | Single field | Filter by year |
| `original_language` | Single field | Filter by language |
| `vote_average` | Single field | Sort by rating |
| `release_date` | Single field | Sort by date (default sort) |
| `(original_language, release_year)` | Compound | Combined filter — language + year together |
