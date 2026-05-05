from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path("data/index.sqlite")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def connect_raw() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS files (
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

            CREATE TABLE IF NOT EXISTS file_text (
                file_id TEXT PRIMARY KEY,
                extracted_text TEXT,
                extraction_status TEXT,
                extracted_at TEXT,
                extractor TEXT,
                error_message TEXT,
                FOREIGN KEY(file_id) REFERENCES files(id)
            );
            """
        )

    ensure_fts_schema()


def ensure_fts_schema() -> None:
    """
    SQLite FTS virtual tables do not support normal ALTER TABLE migrations
    reliably for our use case. If the existing files_fts table has the old
    schema, drop and recreate only the FTS table. This does not delete the
    real indexed file metadata in files or extracted text in file_text.
    """
    with connect() as conn:
        row = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'files_fts'
            """
        ).fetchone()

        if row is None:
            create_fts_table(conn)
            rebuild_all_fts(conn)
            return

        columns = conn.execute("PRAGMA table_info(files_fts)").fetchall()
        column_names = {col["name"] for col in columns}

        expected = {
            "id",
            "name",
            "mime_type",
            "owners",
            "path_hint",
            "extracted_text",
        }

        if not expected.issubset(column_names):
            drop_fts_table(conn)
            create_fts_table(conn)
            rebuild_all_fts(conn)


def drop_fts_table(conn: sqlite3.Connection) -> None:
    """
    Drop FTS table and its shadow tables safely.
    """
    conn.executescript(
        """
        DROP TABLE IF EXISTS files_fts;
        DROP TABLE IF EXISTS files_fts_data;
        DROP TABLE IF EXISTS files_fts_idx;
        DROP TABLE IF EXISTS files_fts_content;
        DROP TABLE IF EXISTS files_fts_docsize;
        DROP TABLE IF EXISTS files_fts_config;
        """
    )


def create_fts_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS files_fts
        USING fts5(
            id UNINDEXED,
            name,
            mime_type,
            owners,
            path_hint,
            extracted_text,
            tokenize='porter'
        )
        """
    )


def rebuild_all_fts(conn: sqlite3.Connection | None = None) -> int:
    should_close = False

    if conn is None:
        conn = connect()
        should_close = True

    try:
        conn.execute("DELETE FROM files_fts")

        rows = conn.execute(
            """
            SELECT
                f.id,
                f.name,
                f.mime_type,
                f.owners,
                f.path_hint,
                COALESCE(t.extracted_text, '') AS extracted_text
            FROM files f
            LEFT JOIN file_text t ON t.file_id = f.id
            """
        ).fetchall()

        for row in rows:
            conn.execute(
                """
                INSERT INTO files_fts (
                    id, name, mime_type, owners, path_hint, extracted_text
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["name"] or "",
                    row["mime_type"] or "",
                    row["owners"] or "",
                    row["path_hint"] or "",
                    row["extracted_text"] or "",
                ),
            )

        return len(rows)
    finally:
        if should_close:
            conn.commit()
            conn.close()


def upsert_file(file: dict[str, Any], account_label: str) -> None:
    owners = ", ".join(
        owner.get("emailAddress", owner.get("displayName", ""))
        for owner in file.get("owners", [])
    )

    parents = ", ".join(file.get("parents", []) or [])

    can_download = int(file.get("capabilities", {}).get("canDownload", False))

    with connect() as conn:
        existing = conn.execute(
            "SELECT source_accounts FROM files WHERE id = ?",
            (file["id"],),
        ).fetchone()

        if existing and existing["source_accounts"]:
            accounts = set(
                a.strip() for a in existing["source_accounts"].split(",") if a.strip()
            )
            accounts.add(account_label)
            source_accounts = ",".join(sorted(accounts))
        else:
            source_accounts = account_label

        conn.execute(
            """
            INSERT INTO files (
                id, name, mime_type, web_view_link, created_time,
                modified_time, owners, parents, drive_id, source_accounts,
                path_hint, can_download, indexed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                mime_type=excluded.mime_type,
                web_view_link=excluded.web_view_link,
                created_time=excluded.created_time,
                modified_time=excluded.modified_time,
                owners=excluded.owners,
                parents=excluded.parents,
                drive_id=excluded.drive_id,
                source_accounts=excluded.source_accounts,
                path_hint=excluded.path_hint,
                can_download=excluded.can_download,
                indexed_at=datetime('now')
            """,
            (
                file["id"],
                file.get("name", ""),
                file.get("mimeType", ""),
                file.get("webViewLink", ""),
                file.get("createdTime", ""),
                file.get("modifiedTime", ""),
                owners,
                parents,
                file.get("driveId", ""),
                source_accounts,
                parents,
                can_download,
            ),
        )

        rebuild_fts_for_file(conn, file["id"])


def upsert_file_text(
    file_id: str,
    extracted_text: str,
    extraction_status: str,
    extractor: str,
    error_message: str = "",
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO file_text (
                file_id, extracted_text, extraction_status,
                extracted_at, extractor, error_message
            )
            VALUES (?, ?, ?, datetime('now'), ?, ?)
            ON CONFLICT(file_id) DO UPDATE SET
                extracted_text=excluded.extracted_text,
                extraction_status=excluded.extraction_status,
                extracted_at=datetime('now'),
                extractor=excluded.extractor,
                error_message=excluded.error_message
            """,
            (
                file_id,
                extracted_text or "",
                extraction_status,
                extractor,
                error_message or "",
            ),
        )
        rebuild_fts_for_file(conn, file_id)


def rebuild_fts_for_file(conn: sqlite3.Connection, file_id: str) -> None:
    row = conn.execute(
        """
        SELECT
            f.id,
            f.name,
            f.mime_type,
            f.owners,
            f.path_hint,
            COALESCE(t.extracted_text, '') AS extracted_text
        FROM files f
        LEFT JOIN file_text t ON t.file_id = f.id
        WHERE f.id = ?
        """,
        (file_id,),
    ).fetchone()

    if row is None:
        return

    conn.execute("DELETE FROM files_fts WHERE id = ?", (file_id,))
    conn.execute(
        """
        INSERT INTO files_fts (
            id, name, mime_type, owners, path_hint, extracted_text
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            row["id"],
            row["name"] or "",
            row["mime_type"] or "",
            row["owners"] or "",
            row["path_hint"] or "",
            row["extracted_text"] or "",
        ),
    )


def get_file(file_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM files WHERE id = ?",
            (file_id,),
        ).fetchone()
        return dict(row) if row else None


def list_extractable_files(
    limit: int = 100, force: bool = False
) -> list[dict[str, Any]]:
    extractable_mimes = [
        "application/vnd.google-apps.document",
        "application/vnd.google-apps.presentation",
        "application/vnd.google-apps.spreadsheet",
        "application/pdf",
        "text/plain",
        "text/csv",
        "text/html",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]

    placeholders = ",".join("?" for _ in extractable_mimes)

    if force:
        sql = f"""
        SELECT f.*
        FROM files f
        WHERE f.mime_type IN ({placeholders})
        ORDER BY f.modified_time DESC
        LIMIT ?
        """
        params: list[Any] = [*extractable_mimes, limit]
    else:
        sql = f"""
        SELECT f.*
        FROM files f
        LEFT JOIN file_text t ON t.file_id = f.id
        WHERE f.mime_type IN ({placeholders})
          AND t.file_id IS NULL
        ORDER BY f.modified_time DESC
        LIMIT ?
        """
        params = [*extractable_mimes, limit]

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
