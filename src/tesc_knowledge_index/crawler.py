from __future__ import annotations

from rich.console import Console

from .database import upsert_file
from .drive_client import build_drive_service


console = Console()


FIELDS = (
    "nextPageToken, files("
    "id, name, mimeType, webViewLink, createdTime, modifiedTime, "
    "owners(displayName,emailAddress), parents, driveId, capabilities/canDownload"
    ")"
)


def _escape_drive_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def crawl_account(account: str, max_pages: int | None = None) -> int:
    service = build_drive_service(account)

    page_token = None
    count = 0
    page_count = 0

    while True:
        page_count += 1

        result = (
            service.files()
            .list(
                q="trashed = false",
                spaces="drive",
                fields=FIELDS,
                pageToken=page_token,
                pageSize=500,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute(num_retries=5)
        )

        files = result.get("files", [])

        for file in files:
            upsert_file(file, account)
            count += 1

        console.print(
            f"[green]Indexed page {page_count} for {account}: {len(files)} files[/green]"
        )

        page_token = result.get("nextPageToken")

        if not page_token:
            break

        if max_pages is not None and page_count >= max_pages:
            break

    return count


def drive_search_account(account: str, query: str, limit: int = 25) -> list[dict]:
    service = build_drive_service(account)

    safe = _escape_drive_query_value(query)
    q = f"trashed = false and (name contains '{safe}' or fullText contains '{safe}')"

    result = (
        service.files()
        .list(
            q=q,
            spaces="drive",
            fields=FIELDS,
            pageSize=limit,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute(num_retries=5)
    )

    return result.get("files", [])
