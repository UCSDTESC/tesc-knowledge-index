from __future__ import annotations

import re

from .database import connect


IMPORTANT_MIME_BONUS = {
    "application/vnd.google-apps.document": 18,
    "application/vnd.google-apps.presentation": 18,
    "application/vnd.google-apps.spreadsheet": 14,
    "application/vnd.google-apps.form": 12,
    "application/pdf": 14,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 12,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": 12,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": 10,
    "text/plain": 8,
    "text/csv": 8,
    "text/html": 4,
}


def query_variants(query: str) -> list[str]:
    q = " ".join(query.strip().split())
    if not q:
        return []

    variants = {q}

    spaced = re.sub(r"([A-Z]{2,})([A-Z][a-z])", r"\1 \2", q)
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", spaced)

    variants.add(spaced)
    variants.add(q.replace("-", " "))
    variants.add(q.replace("_", " "))
    variants.add(q.replace(" ", ""))
    variants.add(q.replace(" ", "-"))
    variants.add(q.lower())
    variants.add(spaced.lower())

    # Useful for SD Hacks / SDHacks style.
    if "hack" in q.lower():
        variants.add("SD Hacks")
        variants.add("SDHacks")
        variants.add("hackathon")

    return sorted(v for v in variants if v)


def _tokens(query: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z0-9]+", query) if len(t) >= 2]


def search_files(query: str, limit: int = 25) -> list[dict]:
    variants = query_variants(query)
    tokens = _tokens(query)

    if not variants:
        return []

    where_parts: list[str] = []
    where_params: list[object] = []

    for variant in variants:
        pattern = f"%{variant}%"
        where_parts.append(
            """
            (
                LOWER(f.name) LIKE LOWER(?)
                OR LOWER(f.mime_type) LIKE LOWER(?)
                OR LOWER(f.owners) LIKE LOWER(?)
                OR LOWER(f.path_hint) LIKE LOWER(?)
                OR LOWER(COALESCE(t.extracted_text, '')) LIKE LOWER(?)
            )
            """
        )
        where_params.extend([pattern, pattern, pattern, pattern, pattern])

    for token in tokens:
        pattern = f"%{token}%"
        where_parts.append(
            """
            (
                LOWER(f.name) LIKE LOWER(?)
                OR LOWER(f.path_hint) LIKE LOWER(?)
                OR LOWER(COALESCE(t.extracted_text, '')) LIKE LOWER(?)
            )
            """
        )
        where_params.extend([pattern, pattern, pattern])

    exact = query.strip()
    contains = f"%{query.strip()}%"

    sql = f"""
    SELECT
        f.id,
        f.name,
        f.mime_type,
        f.web_view_link,
        f.modified_time,
        f.created_time,
        f.owners,
        f.source_accounts,
        f.path_hint,
        COALESCE(t.extraction_status, '') AS extraction_status,
        substr(COALESCE(t.extracted_text, ''), 1, 500) AS text_preview,

        (
            CASE WHEN LOWER(f.name) = LOWER(?) THEN 120 ELSE 0 END
            + CASE WHEN LOWER(f.name) LIKE LOWER(?) THEN 90 ELSE 0 END
            + CASE WHEN LOWER(f.path_hint) LIKE LOWER(?) THEN 45 ELSE 0 END
            + CASE WHEN LOWER(COALESCE(t.extracted_text, '')) LIKE LOWER(?) THEN 35 ELSE 0 END
            + CASE WHEN f.source_accounts LIKE '%,%' THEN 12 ELSE 0 END
            + CASE
                WHEN f.mime_type = 'application/vnd.google-apps.document' THEN 18
                WHEN f.mime_type = 'application/vnd.google-apps.presentation' THEN 18
                WHEN f.mime_type = 'application/vnd.google-apps.spreadsheet' THEN 14
                WHEN f.mime_type = 'application/vnd.google-apps.form' THEN 12
                WHEN f.mime_type = 'application/pdf' THEN 14
                WHEN f.mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' THEN 12
                WHEN f.mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation' THEN 12
                WHEN f.mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' THEN 10
                WHEN f.mime_type = 'text/plain' THEN 8
                WHEN f.mime_type = 'text/csv' THEN 8
                ELSE 0
              END
            + CASE WHEN f.modified_time >= '2023-01-01' THEN 8 ELSE 0 END
            - CASE WHEN LOWER(f.name) LIKE 'copy of %' THEN 12 ELSE 0 END
        ) AS score
    FROM files f
    LEFT JOIN file_text t ON t.file_id = f.id
    WHERE {" OR ".join(where_parts)}
    ORDER BY score DESC, f.modified_time DESC
    LIMIT ?
    """

    params: list[object] = [
        exact,
        contains,
        contains,
        contains,
        *where_params,
        limit,
    ]

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def search_files_by_ids(file_ids: list[str]) -> list[dict]:
    if not file_ids:
        return []

    placeholders = ",".join("?" for _ in file_ids)
    sql = f"""
    SELECT
        f.*,
        COALESCE(t.extraction_status, '') AS extraction_status,
        substr(COALESCE(t.extracted_text, ''), 1, 800) AS text_preview
    FROM files f
    LEFT JOIN file_text t ON t.file_id = f.id
    WHERE f.id IN ({placeholders})
    """

    with connect() as conn:
        rows = conn.execute(sql, file_ids).fetchall()
        return [dict(row) for row in rows]
