# TESC Knowledge Index

A local-first Python CLI for indexing, searching, enriching, and exporting topic-specific knowledge packets from TESC Google Drive history.

TESC has decades of institutional knowledge spread across Google Drive artifacts: Google Docs, Slides, Sheets, PDFs, Forms, shared folders, shared drives, old officer-owned files, and files shared directly with individual accounts. This project helps preserve and search that history **without reorganizing, moving, renaming, or modifying the original Drive structure**.

The goal is simple:

> When someone asks, “What do we have from past SD Hacks work?” or “What resources exist for banquet planning?”, TESC should be able to quickly generate a useful resource packet instead of manually searching through years of scattered Drive files.

---

## What This Project Does

`tesc-knowledge-index` indexes Google Drive files accessible to one or more authenticated TESC accounts, stores searchable metadata and extracted text in a local SQLite database, and generates topic-specific exports.

Example workflows:

```bash
tesc-drive search "SD Hacks"
tesc-drive drive-search "SD Hacks" --account contact --links --limit 75
tesc-drive extract --account contact --query "SD Hacks" --limit 50
tesc-drive report "SD Hacks" --out exports/sd_hacks_report.md
tesc-drive packet "SD Hacks" --out exports/sd_hacks_packet
```

A generated packet can include:

- An advisor-ready Markdown summary
- A CSV of relevant files
- A Markdown list of direct Drive links
- File names, types, owners, modification dates, and source accounts
- Text-extraction status
- A timeline-style view of relevant resources
- Suggested manual review order

The app does **not** move, rename, or modify Google Drive files. It reads metadata, optionally exports/downloads readable content where permissions allow, and stores a local index.

---

## Why This Exists

TESC has a large institutional archive, but much of it is difficult to access because resources are spread across:

- Shared Google Drives
- Folders shared directly with officers
- Files owned by past board members
- Old planning documents
- Event-specific decks, forms, budgets, invoices, and postmortems
- Multiple TESC accounts and aliases

This project is designed to make that history searchable and useful for future boards, advisors, and event leads.

Instead of manually cleaning the entire Drive, this project creates a searchable index over the existing archive.

---

## Current Features

- Authenticate one or more Google accounts using OAuth
- Crawl accessible Google Drive files
- Support shared-drive-aware indexing
- Store file metadata in SQLite
- Track which account had access to each file
- Merge duplicate files by Google Drive file ID
- Search local indexed files by topic/event/process
- Run live Google Drive `name`/`fullText` search
- Save live Drive search results back into the local index
- Extract text from supported file types
- Rebuild the local SQLite FTS search index after schema changes
- Rank results using title, path, extracted text, file type, account overlap, recency, and copy penalties
- Generate Markdown/CSV knowledge packets
- Generate advisor-ready Markdown reports
- Preserve original Drive links
- Avoid modifying Drive contents

---

## Supported File Types

The indexer stores metadata for all visible files, but text extraction is intentionally limited to useful/readable formats.

Currently supported for text extraction:

- Google Docs
- Google Slides
- Google Sheets
- PDFs
- DOCX
- XLSX
- TXT
- CSV

Skipped or metadata-only by default:

- Google Forms
- Folders
- Images
- Videos
- ZIP files
- Photoshop/HEIF/SVG and other asset formats
- HTML files by default, because old Drive HTML exports can be huge/noisy

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
      extractors.py
      report.py
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

If you are installing dependencies manually during development:

```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
pip install typer rich pydantic python-dotenv pypdf pandas python-docx openpyxl
pip install -e .
```

---

## `pyproject.toml`

Example dependency section:

```toml
[project]
name = "tesc-knowledge-index"
version = "0.1.0"
description = "Index, search, enrich, and export topic-specific knowledge packets from TESC Google Drive history."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "google-api-python-client>=2.0.0",
    "google-auth>=2.0.0",
    "google-auth-oauthlib>=1.0.0",
    "google-auth-httplib2>=0.2.0",
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "pypdf>=4.0.0",
    "pandas>=2.0.0",
    "python-docx>=1.1.0",
    "openpyxl>=3.1.0",
]

[project.scripts]
tesc-drive = "tesc_knowledge_index.cli:app"

[tool.setuptools.packages.find]
where = ["src"]
```

---

## Google Drive API Setup

This project uses the Google Drive API with OAuth desktop authentication.

### 1. Create a Google Cloud project

Create a Google Cloud project, for example:

```text
TESC Knowledge Index
```

### 2. Enable Google Drive API

In the project, enable:

```text
Google Drive API
```

### 3. Create OAuth credentials

Create OAuth client credentials with:

```text
Application type: Desktop app
Name: TESC Knowledge Index Desktop Client
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

## First-Time Setup Workflow

Run:

```bash
tesc-drive doctor
tesc-drive init
tesc-drive auth add --account rohan
tesc-drive auth add --account contact
```

Then test indexing:

```bash
tesc-drive index --account rohan --max-pages 2
tesc-drive index --account contact --max-pages 2
tesc-drive stats
```

If that works, run full indexing:

```bash
tesc-drive index --account rohan
tesc-drive index --account contact
tesc-drive stats
```

---

## Core Commands

### Check project health

```bash
tesc-drive doctor
```

Checks for:

- `credentials/client_secret.json`
- `tokens/`
- `data/`
- `exports/`
- SQLite database

### Initialize or migrate local database

```bash
tesc-drive init
```

This creates required tables and ensures the FTS search table has the expected schema.

### Rebuild the local search index

```bash
tesc-drive rebuild-fts
```

Use this after changing search schema, adding text extraction, or fixing FTS-related issues.

This rebuilds only the derived FTS table. It does **not** delete indexed files.

### Show database stats

```bash
tesc-drive stats
```

Shows:

- Total unique files indexed
- Number of files with extraction records
- Number of files with successful text extraction
- Files by source account
- Top MIME types

---

## Indexing Google Drive

Index one account:

```bash
tesc-drive index --account rohan
```

Index another account:

```bash
tesc-drive index --account contact
```

Test with fewer pages:

```bash
tesc-drive index --account contact --max-pages 2
```

The app merges duplicate files by Google Drive file ID and records which account had access.

---

## Local Search

Search local metadata and extracted text:

```bash
tesc-drive search "SD Hacks"
tesc-drive search "SDHacks"
tesc-drive search "sponsorship"
tesc-drive search "banquet"
tesc-drive search "Decaf"
```

Show full copy-pasteable links:

```bash
tesc-drive search "SD Hacks" --links --limit 25
```

Show extracted text previews:

```bash
tesc-drive search "SD Hacks sponsorship" --links --preview --limit 25
```

Search results include:

- Score
- File name
- MIME type
- Modified time
- Source account(s)
- Text extraction status
- Drive link

---

## Live Google Drive Search

Local search only knows what is already indexed and extracted. Live Drive search asks Google Drive directly using `name` and `fullText`.

```bash
tesc-drive drive-search "SD Hacks" --account rohan --links --limit 75
tesc-drive drive-search "SD Hacks" --account contact --links --limit 75
```

Important behavior:

> Live Drive search results are saved back into the local database.

This means live search acts as a discovery/enrichment tool. After running live Drive search, local search and packets become stronger.

Recommended pattern:

```bash
tesc-drive drive-search "SD Hacks" --account rohan --links --limit 75
tesc-drive drive-search "SD Hacks" --account contact --links --limit 75
tesc-drive search "SD Hacks" --limit 75
```

---

## Text Extraction

Extract text for top local search results for a topic:

```bash
tesc-drive extract --account contact --query "SD Hacks" --limit 50
```

This is the recommended extraction workflow.

Avoid running global extraction unless you intentionally want to process arbitrary pending files:

```bash
tesc-drive extract --account contact --limit 100
```

If no `--query` is provided, the CLI warns you that it will extract arbitrary pending files from the whole database.

### Why topic-scoped extraction matters

This command:

```bash
tesc-drive extract --account contact --query "SD Hacks" --limit 50
```

means:

> Extract text from the top 50 local results related to SD Hacks.

This command:

```bash
tesc-drive extract --account contact --limit 50
```

means:

> Extract the next 50 pending extractable files in the whole database.

Topic-scoped extraction is safer, faster, and more relevant.

---

## Ranking

Local search uses a weighted score based on:

- Exact title match
- Partial title match
- Folder/path match
- Extracted text match
- Important file type bonus
- Account overlap bonus
- Recency bonus
- Copy/duplicate penalty

Important file types receive a boost:

- Google Docs
- Google Slides
- Google Sheets
- Google Forms
- PDFs
- DOCX/PPTX/XLSX
- TXT/CSV

This helps files like:

```text
SD Hacks Master Document
SD Hacks Operations
SD Hacks Event Planning Guide
Sponsorship Timeline - SD Hacks 2019
SD Hacks 23 Day-of Logistics Company Packet
```

rank above weaker or less relevant mentions.

---

## Exporting Links

Print simple copy-pasteable links:

```bash
tesc-drive links "SD Hacks" --limit 25
```

Export links to Markdown:

```bash
tesc-drive export-links "SD Hacks" --out exports/sd_hacks_links.md --limit 75
```

The Markdown export includes:

- File name
- Score
- Link
- Type
- Modified time
- Source account(s)
- Owners
- Text extraction status

---

## Advisor-Ready Reports

Generate an advisor-ready Markdown report:

```bash
tesc-drive report "SD Hacks" --out exports/sd_hacks_report.md --limit 75
```

The report includes:

- Executive summary
- What TESC appears to have done
- Most relevant resources
- Resource categories
- Timeline by modified year
- Recommended manual review order
- Notes and limitations

The report is meant to be a strong starting point, not a final official historical statement. Review top files manually before sending it to advisors, university staff, sponsors, or external partners.

---

## Knowledge Packets

Create a full packet for a topic:

```bash
tesc-drive packet "SD Hacks" --out exports/sd_hacks_packet --limit 75
```

Example output:

```text
exports/sd_hacks_packet/
  README.md
  files.csv
  links.md
  summary.md
```

### Packet Contents

`README.md`

Overview of the generated packet and recommended next step.

`files.csv`

Spreadsheet-friendly list of relevant files.

`links.md`

Markdown document with clickable Drive links and metadata.

`summary.md`

Advisor-ready summary generated from the top local search results.

---

## Recommended Topic Workflow

For one topic:

```bash
tesc-drive drive-search "SD Hacks" --account rohan --links --limit 75
tesc-drive drive-search "SD Hacks" --account contact --links --limit 75

tesc-drive extract --account contact --query "SD Hacks" --limit 50

tesc-drive search "SD Hacks" --limit 75 --links --preview
tesc-drive report "SD Hacks" --out exports/sd_hacks_report.md --limit 75
tesc-drive packet "SD Hacks" --out exports/sd_hacks_packet --limit 75
```

---

## PowerShell Helper Script

Create `search-topic.ps1`:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$Topic,

    [int]$Limit = 75,

    [int]$ExtractLimit = 50
)

$safeName = $Topic.ToLower().Replace(" ", "_").Replace("/", "_").Replace("\", "_")

Write-Host ""
Write-Host "=== Local search before live enrichment: $Topic ==="
tesc-drive search "$Topic" --limit $Limit

Write-Host ""
Write-Host "=== Live Drive search via rohan: $Topic ==="
tesc-drive drive-search "$Topic" --account rohan --links --limit $Limit

Write-Host ""
Write-Host "=== Live Drive search via contact: $Topic ==="
tesc-drive drive-search "$Topic" --account contact --links --limit $Limit

Write-Host ""
Write-Host "=== Extracting text for topic files via contact ==="
tesc-drive extract --account contact --query "$Topic" --limit $ExtractLimit

Write-Host ""
Write-Host "=== Local search after live enrichment + extraction: $Topic ==="
tesc-drive search "$Topic" --limit $Limit

Write-Host ""
Write-Host "=== Exporting links ==="
tesc-drive export-links "$Topic" --out "exports/${safeName}_links.md" --limit $Limit

Write-Host ""
Write-Host "=== Creating advisor report ==="
tesc-drive report "$Topic" --out "exports/${safeName}_report.md" --limit $Limit

Write-Host ""
Write-Host "=== Creating packet ==="
tesc-drive packet "$Topic" --out "exports/${safeName}_packet" --limit $Limit
```

Usage:

```powershell
.\search-topic.ps1 "SD Hacks" -Limit 75 -ExtractLimit 50
.\search-topic.ps1 "Decaf" -Limit 75 -ExtractLimit 50
.\search-topic.ps1 "sponsorship" -Limit 100 -ExtractLimit 50
```

---

## Example Use Case

If an advisor asks:

> What resources does TESC have from past SD Hacks involvement?

Run:

```bash
tesc-drive drive-search "SD Hacks" --account rohan --links --limit 75
tesc-drive drive-search "SD Hacks" --account contact --links --limit 75
tesc-drive extract --account contact --query "SD Hacks" --limit 50
tesc-drive packet "SD Hacks" --out exports/sd_hacks_packet --limit 75
```

Then review:

```text
exports/sd_hacks_packet/summary.md
exports/sd_hacks_packet/links.md
exports/sd_hacks_packet/files.csv
```

This provides a structured starting point instead of a raw Google Drive search dump.

---

## Suggested Queries for TESC

Examples of useful search topics:

```text
SD Hacks
SDHacks
hackathon
E Week
E-Week
DECaF
Decaf
banquet
sponsorship
sponsor packet
budget
GBM
General Body Meeting
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
judging
applications
operations
day-of logistics
```

Search broad first, then narrow:

```bash
tesc-drive search "hackathon"
tesc-drive search "SD Hacks sponsorship"
tesc-drive search "SD Hacks budget"
tesc-drive search "SD Hacks logistics"
tesc-drive search "SD Hacks judging"
```

---

## Privacy and Security

This project can be public on GitHub, but the data it indexes may be private.

Never commit:

- OAuth tokens
- Google API client secret files
- Downloaded TESC files
- Exported packets containing private links or content
- Local SQLite databases
- `.env` files
- Cached Drive content

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

Before pushing to GitHub, run:

```bash
git status
```

Make sure no private data, tokens, credentials, database files, or exports are staged.

---

## Design Philosophy

### Index first, reorganize later

The app does not try to clean or move TESC Drive files. Historical Drive structures can be messy for good reasons: ownership, sharing, permissions, and context. Indexing is safer than reorganizing.

### Preserve original links

The app keeps the original Google Drive links so files remain connected to their actual source of truth.

### Local-first

The first version uses SQLite and local exports. This keeps the system simple, transparent, and easy to transfer to future officers.

### Live search strengthens local search

Google Drive live search can discover files through `fullText` even when local extraction has not happened yet. The app saves live results back into SQLite so future local searches and packets improve.

### Human-reviewed summaries

The app helps gather and organize resources, but final summaries should be reviewed by a human before being sent to advisors, university staff, sponsors, or external partners.

---

## Technical Overview

The pipeline is:

```text
Google Drive OAuth
        ↓
Drive API file crawl
        ↓
SQLite metadata index
        ↓
Live Drive search enrichment
        ↓
Topic-scoped text extraction
        ↓
SQLite FTS search
        ↓
Ranking
        ↓
Advisor report / knowledge packet export
```

---

## Database

The app uses SQLite.

Main metadata table:

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

Extracted text table:

```sql
CREATE TABLE file_text (
    file_id TEXT PRIMARY KEY,
    extracted_text TEXT,
    extraction_status TEXT,
    extracted_at TEXT,
    extractor TEXT,
    error_message TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id)
);
```

FTS search table:

```sql
CREATE VIRTUAL TABLE files_fts
USING fts5(
    id UNINDEXED,
    name,
    mime_type,
    owners,
    path_hint,
    extracted_text,
    tokenize='porter'
);
```

If FTS schema changes, run:

```bash
tesc-drive rebuild-fts
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

### Search returns no results, but Drive search finds files

Run live Drive search to enrich the local database:

```bash
tesc-drive drive-search "SD Hacks" --account contact --links --limit 75
tesc-drive search "SD Hacks" --limit 75
```

### `files_fts has no column named extracted_text`

Your SQLite database has the old FTS schema. Run:

```bash
tesc-drive init
tesc-drive rebuild-fts
```

Do not delete `data/index.sqlite` unless you intentionally want to recrawl everything.

### Extraction appears stuck

Use topic-scoped extraction and a small limit first:

```bash
tesc-drive extract --account contact --query "SD Hacks" --limit 10
```

Then increase:

```bash
tesc-drive extract --account contact --query "SD Hacks" --limit 50
```

### Shared Drive files are missing

Confirm the crawler uses shared-drive-aware options:

```python
supportsAllDrives=True
includeItemsFromAllDrives=True
```

### Accidentally committed private files

Immediately remove them from Git history and rotate/revoke affected credentials or OAuth tokens.

---

## Development Commands

Install in editable mode:

```bash
pip install -e .
```

Run a small crawl:

```bash
tesc-drive index --account rohan --max-pages 1
```

Rebuild local search index:

```bash
tesc-drive rebuild-fts
```

Run a search:

```bash
tesc-drive search "SD Hacks"
```

Run live Drive search:

```bash
tesc-drive drive-search "SD Hacks" --account contact --links --limit 75
```

Extract topic text:

```bash
tesc-drive extract --account contact --query "SD Hacks" --limit 25
```

Generate report:

```bash
tesc-drive report "SD Hacks" --out exports/sd_hacks_report.md
```

Generate packet:

```bash
tesc-drive packet "SD Hacks" --out exports/sd_hacks_packet
```

---

## Roadmap

### Milestone 1: Metadata Indexer

- [x] OAuth authentication
- [x] Drive metadata crawl
- [x] Shared-drive-aware indexing
- [x] SQLite database
- [x] Account-source tracking
- [x] Packet export

### Milestone 2: Search and Ranking

- [x] Local search
- [x] Live Google Drive search
- [x] Live search enrichment into local DB
- [x] Title exact-match boost
- [x] Path/folder boost
- [x] Extracted-text boost
- [x] File type boost
- [x] Account overlap boost
- [x] Recency boost
- [x] Copy penalty
- [ ] Better duplicate grouping
- [ ] Folder path reconstruction beyond parent IDs

### Milestone 3: Text Extraction

- [x] Export Google Docs to text
- [x] Export Google Slides to text
- [x] Export Google Sheets to XLSX/text
- [x] Parse PDFs with `pypdf`
- [x] Parse DOCX
- [x] Parse XLSX
- [x] Store extracted text in SQLite
- [x] Topic-scoped extraction
- [ ] OCR for important images/scans
- [ ] Better handling for very large PDFs/spreadsheets

### Milestone 4: Reports

- [x] Advisor-ready Markdown reports
- [x] Resource categories
- [x] Year-by-year modified timeline
- [x] Recommended manual review order
- [x] Notes and limitations
- [ ] Better natural-language summaries using reviewed top files
- [ ] Missing/permission-blocked file notes
- [ ] People/contact extraction

### Milestone 5: Web Interface

- [ ] Streamlit prototype
- [ ] Search page
- [ ] Packet generation page
- [ ] File preview metadata
- [ ] Export controls
- [ ] Simple advisor-facing read-only view

### Milestone 6: Semantic Search

- [ ] Embedding-based search
- [ ] Local vector database
- [ ] Hybrid keyword + semantic ranking
- [ ] Question-answering over selected packets

---

## Contributor Notes

When contributing:

1. Do not commit private TESC data.
2. Do not commit OAuth credentials or tokens.
3. Keep the CLI usable before adding a web app.
4. Prefer small, reviewable features.
5. Keep generated packets out of Git.
6. Document any new command in this README.
7. Treat advisor-ready reports as draft summaries requiring human review.

---

## License

Choose a license before making the repository broadly public. For an internal student-organization tool, MIT is usually simple and permissive.

Suggested:

```text
MIT License
```

---

## Project Status

Working local-first CLI.

The app can authenticate multiple TESC accounts, index Drive metadata, run live Drive searches, enrich the local database, extract text for topic-specific files, rank results, and generate advisor-ready Markdown reports and knowledge packets.

The next major improvements are duplicate grouping, better folder-path reconstruction, OCR for scanned/image-heavy files, and a lightweight web interface.
