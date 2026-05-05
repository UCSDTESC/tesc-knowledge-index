# TESC Knowledge Index

A local-first Python application for indexing, searching, and exporting topic-specific knowledge packets from TESC Google Drive history.

TESC has decades of institutional knowledge spread across Google Drive artifacts: Google Docs, Slides, Sheets, PDFs, Forms, shared folders, shared drives, and files shared directly with individual accounts. This project helps preserve and search that history without reorganizing or moving the original Drive structure.

The goal is simple:

> When someone asks, “What do we have from past SDHacks work?” or “What resources exist for banquet planning?”, TESC should be able to quickly generate a useful resource packet instead of manually searching through years of scattered Drive files.

---

## What This Project Does

`tesc-knowledge-index` indexes Google Drive files accessible to one or more authenticated TESC accounts, stores searchable metadata in a local SQLite database, and generates topic-specific export packets.

Example workflows:

```bash
tesc-drive search "SDHacks"
tesc-drive packet "SDHacks" --out exports/sdhacks
```

A generated packet can include:

- A CSV of relevant files
- A Markdown list of direct Drive links
- File names, types, owners, modification dates, and access source
- A starter summary document for advisor-facing or board-facing review

The app does **not** move, rename, or modify Google Drive files. It only reads metadata and, in future versions, may optionally extract/download content where permissions allow.

---

## Why This Exists

TESC has a large institutional archive, but much of it is difficult to access because resources are spread across:

- Shared Google Drives
- Folders shared directly with officers
- Files owned by past board members
- Old planning documents
- Event-specific decks, forms, budgets, and postmortems
- Multiple TESC accounts and aliases

This project is designed to make that history searchable and useful for future boards, advisors, and event leads.

Instead of manually cleaning the entire Drive, this project creates a searchable index over the existing archive.

---

## Current MVP Features

- Authenticate one or more Google accounts using OAuth
- Crawl accessible Google Drive files
- Support shared-drive-aware indexing
- Store file metadata in SQLite
- Search indexed files by topic or event name
- Generate Markdown/CSV knowledge packets
- Track which account had access to each file
- Preserve original Drive links
- Avoid modifying Drive contents

---

## Planned Features

Future versions may include:

- Google Docs text extraction
- Google Slides text extraction
- Google Sheets CSV/text extraction
- PDF text extraction
- Better ranking by title, folder context, file type, and recency
- Duplicate detection
- Timeline generation by year
- Advisor-ready summary reports
- Semantic search with embeddings
- Streamlit or FastAPI web interface
- Scheduled re-indexing
- Shared “TESC Knowledge Packets” export folder

---

## Recommended Project Structure

```text
tesc-knowledge-index/
  README.md
  pyproject.toml
  .gitignore

  credentials/
    .gitkeep

  tokens/
    .gitkeep

  data/
    .gitkeep

  exports/
    .gitkeep

  src/
    tesc_knowledge_index/
      __init__.py
      cli.py
      auth.py
      drive_client.py
      crawler.py
      database.py
      search.py
      packet.py

  tests/
    test_search.py
    test_ranking.py
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/tesc-knowledge-index.git
cd tesc-knowledge-index
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -e .
```

---

## Google Drive API Setup

This project uses the Google Drive API with OAuth desktop authentication.

### 1. Create a Google Cloud project

Go to the Google Cloud Console and create a project, for example:

```text
TESC Knowledge Index
```

### 2. Enable the Google Drive API

In the Google Cloud project, enable:

```text
Google Drive API
```

### 3. Create OAuth credentials

Create OAuth client credentials with:

```text
Application type: Desktop app
```

Download the credentials JSON file and save it as:

```text
credentials/client_secret.json
```

Do **not** commit this file to GitHub.

---

## Authentication

Authenticate each Google account that has useful TESC Drive access.

Example:

```bash
tesc-drive auth add --account rohan
tesc-drive auth add --account contact
```

OAuth tokens are saved locally in:

```text
tokens/
```

Do **not** commit token files to GitHub.

---

## Usage

### Initialize the local database

```bash
tesc-drive init
```

### Index one account

For a small test crawl:

```bash
tesc-drive index --account rohan --max-pages 2
```

For a full crawl:

```bash
tesc-drive index --account rohan
```

Index another account:

```bash
tesc-drive index --account contact
```

The app merges duplicate files by Google Drive file ID and records which account had access.

---

## Searching

Search for a topic, event, process, or organization:

```bash
tesc-drive search "SDHacks"
tesc-drive search "E-Week"
tesc-drive search "banquet"
tesc-drive search "sponsorship"
tesc-drive search "DECaF"
```

Search results include:

- File name
- MIME type
- Last modified time
- Source account
- Drive link

---

## Generating a Knowledge Packet

Create a packet for a topic:

```bash
tesc-drive packet "SDHacks" --out exports/sdhacks
```

Example output:

```text
exports/sdhacks/
  README.md
  files.csv
  links.md
  summary_stub.md
```

### Packet Contents

`README.md`

A short overview of the generated packet.

`files.csv`

A spreadsheet-friendly list of relevant files.

`links.md`

A Markdown document with clickable Drive links.

`summary_stub.md`

A starting point for a human-reviewed summary.

---

## Example Use Case

If an advisor asks:

> What resources does TESC have from past SDHacks involvement?

Run:

```bash
tesc-drive index --account rohan
tesc-drive index --account contact
tesc-drive packet "SDHacks" --out exports/sdhacks
```

Then review:

```text
exports/sdhacks/links.md
exports/sdhacks/files.csv
exports/sdhacks/summary_stub.md
```

This provides a structured starting point instead of a raw Google Drive search dump.

---

## Privacy and Security

This project is designed to be public on GitHub, but the data it indexes may be private.

Never commit:

- OAuth tokens
- Google API client secret files
- Downloaded TESC files
- Exported packets containing private links or content
- Local SQLite databases
- `.env` files
- Cached Drive content

The included `.gitignore` should exclude these files, but contributors should still be careful before committing.

Recommended `.gitignore` entries:

```gitignore
.venv/
__pycache__/
*.pyc

.env

credentials/*.json
tokens/*.json

data/
exports/
cache/

*.sqlite
*.db

.DS_Store
Thumbs.db
```

To keep empty folders in Git, use `.gitkeep` files:

```text
credentials/.gitkeep
tokens/.gitkeep
data/.gitkeep
exports/.gitkeep
```

---

## Design Philosophy

### Index first, reorganize later

The app does not try to clean or move TESC Drive files. Historical Drive structures can be messy for good reasons: ownership, sharing, permissions, and context. Indexing is safer than reorganizing.

### Preserve original links

The app keeps the original Google Drive links so files remain connected to their actual source of truth.

### Local-first

The first version uses SQLite and local exports. This keeps the system simple, transparent, and easy to transfer to future officers.

### Human-reviewed summaries

The app helps gather and organize resources, but final summaries should be reviewed by a human before being sent to advisors, university staff, sponsors, or external partners.

---

## Technical Overview

The MVP pipeline is:

```text
Google Drive OAuth
        ↓
Drive API file crawl
        ↓
SQLite metadata index
        ↓
SQLite FTS search
        ↓
Topic packet export
```

The app currently focuses on file metadata and Drive links. Future versions can add full text extraction and semantic search.

---

## Database

The app uses SQLite.

Main table:

```sql
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mime_type TEXT,
    web_view_link TEXT,
    created_time TEXT,
    modified_time TEXT,
    owners TEXT,
    parents TEXT,
    drive_id TEXT,
    source_accounts TEXT,
    path_hint TEXT,
    can_download INTEGER,
    indexed_at TEXT
);
```

Search table:

```sql
CREATE VIRTUAL TABLE files_fts
USING fts5(
    id UNINDEXED,
    name,
    mime_type,
    owners,
    path_hint,
    content='',
    tokenize='porter'
);
```

---

## Development Commands

Install in editable mode:

```bash
pip install -e .
```

Run a test crawl:

```bash
tesc-drive index --account rohan --max-pages 1
```

Run a search:

```bash
tesc-drive search "SDHacks"
```

Generate a packet:

```bash
tesc-drive packet "SDHacks" --out exports/sdhacks
```

---

## Troubleshooting

### `tesc-drive` command not found

Make sure your virtual environment is activated and the project is installed:

```bash
pip install -e .
```

### Missing `credentials/client_secret.json`

Download OAuth desktop credentials from Google Cloud Console and save the file as:

```text
credentials/client_secret.json
```

### Search returns no results

Try:

```bash
tesc-drive index --account rohan --max-pages 2
tesc-drive search "sponsor"
```

If results still do not appear, confirm that the authenticated account can access the files in Google Drive.

### Shared Drive files are missing

Make sure the crawler uses shared-drive-aware options:

```python
supportsAllDrives=True
includeItemsFromAllDrives=True
```

### Accidentally committed private files

Immediately remove them from Git history and rotate/revoke affected credentials or OAuth tokens.

---

## Roadmap

### Milestone 1: Metadata Indexer

- [x] OAuth authentication
- [x] Drive metadata crawl
- [x] SQLite database
- [x] Basic FTS search
- [x] Packet export

### Milestone 2: Text Extraction

- [ ] Export Google Docs to text
- [ ] Export Google Slides to text or PDF
- [ ] Export Google Sheets to CSV
- [ ] Parse PDFs with `pypdf`
- [ ] Store extracted text in SQLite

### Milestone 3: Better Search and Ranking

- [ ] Title exact-match boost
- [ ] Folder/path boost
- [ ] File type boost
- [ ] Recency boost
- [ ] Duplicate grouping
- [ ] Account overlap boost

### Milestone 4: Reports

- [ ] Advisor-ready Markdown reports
- [ ] Year-by-year timelines
- [ ] Top files by category
- [ ] Missing/permission-blocked file notes
- [ ] Suggested next steps for human review

### Milestone 5: Web Interface

- [ ] Streamlit prototype
- [ ] Search page
- [ ] Packet generation page
- [ ] File preview metadata
- [ ] Export controls

### Milestone 6: Semantic Search

- [ ] Embedding-based search
- [ ] Local vector database
- [ ] Hybrid keyword + semantic ranking
- [ ] Question-answering over selected packets

---

## Suggested Queries for TESC

Examples of useful search topics:

```text
SDHacks
E-Week
DECaF
banquet
sponsorship
sponsor packet
budget
GBM
retreat
ESC Night
project teams
transition docs
constitution
funding
marketing
outreach
alumni
volunteer form
```

---

## Contributor Notes

When contributing:

1. Do not commit private TESC data.
2. Do not commit OAuth credentials or tokens.
3. Keep the CLI usable before adding a web app.
4. Prefer small, reviewable features.
5. Keep generated packets out of Git.
6. Document any new command in this README.

---

## License

Choose a license before making the repository broadly public. For an internal student-organization tool, MIT is usually simple and permissive.

Suggested:

```text
MIT License
```

---

## Project Status

Early MVP. The first goal is to reliably index and search Google Drive metadata from multiple TESC accounts, then generate useful topic packets for historical events and processes.

